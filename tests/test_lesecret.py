import base64
import tempfile

import numpy as np
import pytest
from cryptography.fernet import Fernet, InvalidToken
from PIL import Image

from lesecret.main import (
    ENCODING,
    decode_text_from_image,
    decrypt_message,
    encode_text_in_image,
    encrypt_message,
    generate_key,
)


@pytest.fixture
def temporary_image():
    temp_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)

    # Create a random 100x100 image
    image_size = (100, 100)
    image = Image.fromarray(np.random.randint(0, 255, image_size + (3,), dtype=np.uint8))
    image.save(temp_image.name)

    yield temp_image.name

    temp_image.close()


def test_key_generation():
    passkey = 'testpasskey'
    key = generate_key(passkey)
    assert len(key) == len(
        Fernet.generate_key()
    ), f'Key length should be {len(Fernet.generate_key())} bytes'
    try:
        base64.urlsafe_b64decode(key)
    except base64.binascii.Error:
        assert False, 'Key should be a valid base64-encoded string'


def test_encrypt_decrypt_message():
    passkey = 'testpasskey'
    message = 'This is a secret message 這是一個測試訊息'
    encrypted = encrypt_message(message, passkey)
    decrypted = decrypt_message(encrypted, passkey)
    assert decrypted.decode(ENCODING) == message, 'Decrypted message should match the original'


def test_encrypt_with_invalid_passkey():
    passkey = 'testpasskey'
    wrong_passkey = 'wrongpasskey'
    message = 'This is a secret message 這是一個測試訊息'
    encrypted = encrypt_message(message, passkey)
    with pytest.raises(InvalidToken):
        decrypt_message(encrypted, wrong_passkey)


def test_encode_decode_image(temporary_image):
    message = 'This is a secret message 這是一個測試訊息'
    encoded_output_path = tempfile.mktemp(suffix='.png')

    encode_text_in_image(temporary_image, message, encoded_output_path)

    decoded_message = decode_text_from_image(encoded_output_path)

    assert message == decoded_message, 'Decoded message should match the original'


def test_image_too_small():
    small_image = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
    small_image_path = small_image.name

    # Create a 1x1 pixel image
    image = Image.fromarray(np.ones((1, 1, 3), dtype=np.uint8) * 255)
    image.save(small_image_path)

    large_message = 'A' * 1000  # Large message

    with pytest.raises(ValueError, match='The image is too small'):
        encode_text_in_image(small_image_path, large_message, tempfile.mktemp(suffix='.png'))


def test_image_without_encoded_message(temporary_image):
    with pytest.raises(ValueError, match='Could not find encoded message'):
        decode_text_from_image(temporary_image)


def test_full_encode_decode_cycle(temporary_image):
    passkey = 'testpasskey'
    message = 'This is a secret message 這是一個測試訊息'
    encoded_output_path = tempfile.mktemp(suffix='.png')

    # Step 1: Encrypt the message
    encrypted_message = encrypt_message(message, passkey).decode(ENCODING)

    # Step 2: Encode the message into the image
    encode_text_in_image(temporary_image, encrypted_message, encoded_output_path)

    # Step 3: Decode the message from the image
    decoded_message = decode_text_from_image(encoded_output_path)

    # Step 4: Decrypt the message
    decrypted_message = decrypt_message(decoded_message.encode(ENCODING), passkey)

    # Ensure the decoded-decrypted message matches the original
    assert (
        decrypted_message.decode(ENCODING) == message
    ), 'Decoded and decrypted message should match the original'
