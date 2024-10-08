import base64
import logging
import os
import random
import traceback
from pathlib import Path

import numpy as np
from cryptography.fernet import Fernet, InvalidToken
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

logging_level = logging.DEBUG if os.getenv('DEBUG') else logging.INFO
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging_level)

# Arbitrary 4-byte-long bit sequence to mark the end of the encoded message
# The probability of having this bit sequence in a non-encoded image is
# 1 - ((1 - 1/2^N) ^ (W * H * 3 - N + 1))
# For a 1000x1000 image, the probability is around 0.07%
END_OF_TEXT = '11111111111111101111111111111110'
ENCODING = 'utf-8'


def generate_key(passkey: str) -> bytes:
    return base64.urlsafe_b64encode(passkey.ljust(32)[:32].encode())


def encrypt_message(message: str, passkey: str) -> bytes:
    key = generate_key(passkey)
    fernet = Fernet(key)
    return fernet.encrypt(message.encode(ENCODING))


def decrypt_message(encrypted_message: bytes, passkey: str) -> bytes:
    key = generate_key(passkey)
    fernet = Fernet(key)
    return fernet.decrypt(encrypted_message)


def generate_output_path(input_path: str) -> str:
    path = Path(input_path)
    return str(path.with_name(f'{path.stem}-{random.randint(4096, 65535):04x}.png'))


def encode_text_in_image(image_path: str, text: str, output_path: str) -> None:
    image = Image.open(image_path)
    image_data = np.array(image)
    image_capacity = image_data.size

    binary_message = ''.join(format(byte, '08b') for byte in text.encode(ENCODING))
    binary_message += END_OF_TEXT

    if len(binary_message) > image_capacity:
        raise ValueError(
            'The image is too small to hold the encoded text. Please use a larger image.'
        )

    data_flat = image_data.flatten()

    for i, bit in enumerate(binary_message):
        data_flat[i] = np.uint8((data_flat[i] & 0b11111110) | int(bit))

    image_data = data_flat.reshape(image_data.shape)
    encoded_image = Image.fromarray(image_data)
    encoded_image.save(output_path)


def decode_text_from_image(image_path: str) -> str:
    image = Image.open(image_path)
    image_data = np.array(image)

    data_flat = image_data.flatten()

    # Extract all LSBs in one go using numpy's bitwise operations
    lsb_array = data_flat & 1

    binary_message = ''.join(lsb_array.astype(str))
    end_marker = binary_message.find(END_OF_TEXT)
    if end_marker != -1:
        logging.debug(f'{end_marker=}')
        binary_message = binary_message[:end_marker]
    else:
        raise ValueError('Could not find encoded message')

    # Convert binary string into a list of bytes
    byte_chunks = [binary_message[i : i + 8] for i in range(0, len(binary_message), 8)]

    # Convert bytes back into a byte array
    byte_array = bytearray(int(byte, 2) for byte in byte_chunks)

    return byte_array.decode(ENCODING)


def encode_mode(console: Console) -> None:
    image_path = Prompt.ask('[green]Enter the path to the image to encode the text in[/green]')
    text_to_encode = Prompt.ask('[green]Enter the text you want to encode[/green]')
    passkey = Prompt.ask('[green]Enter the passkey to encrypt the text[/green]', password=True)

    encrypted_text = encrypt_message(text_to_encode, passkey)

    output_path = generate_output_path(image_path)
    try:
        encode_text_in_image(image_path, encrypted_text.decode(ENCODING), output_path)
    except Exception as e:
        logging.debug(traceback.format_exc())
        console.print(f'❌ [bold red]Error: {e}[/bold red]')

    console.print(
        f'✅ [bold green]Text successfully encoded into the image and saved at {output_path}[/bold green]'
    )


def decode_mode(console: Console) -> None:
    image_path = Prompt.ask('[cyan]Enter the path to the image with hidden text[/cyan]')
    passkey = Prompt.ask('[cyan]Enter the passkey to decrypt the text[/cyan]', password=True)

    with console.status("[bold green]Working on it..."):
        try:
            encrypted_message = decode_text_from_image(image_path)
        except Exception as e:
            logging.debug(traceback.format_exc())
            console.print(f'❌ [bold red]Error: No encoded message in the image[/bold red]')
            return

        try:
            decrypted_message = decrypt_message(encrypted_message.encode(ENCODING), passkey)
        except InvalidToken:
            console.print(f'❌ [bold red]Error: Wrong passkey[/bold red]')
            return
        except Exception as e:
            logging.debug(traceback.format_exc())
            console.print(f'❌ [bold red]Error: {e.__class__.__name__}[/bold red]')
            if str(e):
                console.print(f'❌ [bold red]Error detail: {e}[/bold red]')
            return

        console.print(
            Panel(decrypted_message.decode(ENCODING), title='Decoded Message', style='bold green')
        )


def main() -> None:
    console = Console()
    console.clear()
    console.print(
        Panel(
            Text('Hide in Plain Sight', justify='center'), title='The Secret', style='bold magenta'
        )
    )
    mode = Prompt.ask('[cyan]Choose Mode[/cyan] (encode/decode)', choices=['encode', 'decode'])

    if mode == 'encode':
        encode_mode(console)
    elif mode == 'decode':
        decode_mode(console)


if __name__ == '__main__':
    main()
