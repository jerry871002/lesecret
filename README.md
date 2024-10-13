# Le Secret

This is a TUI re-implementation of my freshman year project [The Secret](https://github.com/jerry871002/OOP-Final-Project) (it was 2018 by the way...🫣), an image steganography tool to hide secrets in plain sight.

Use it to secretly encode and decode messages within image files and share the images on popular messaging apps!

## Installation

```
pip install lesecret
```

## Get Started

Start the TUI-based application with the following command:

```
lesecret
```

There are two modes for *Le Secret*: encode and decode.

In encode mode, you need to provide an image along with the message you would like to encode and a passkey.
*Le Secret* will produce a new image with the name `<original-name>-<random-hex-digits>.png` in the same directory.

In decode mode, you need to provide an image and a passkey.
The decoded message will be shown only if the image contains an encoded message and the correct passkey is provided.

So far I have tested sending the image over Line, Telegram (send as a file), and Messenger.
The encoded message preserves in all three applications.
However, if you download the image on your iPhone (I don't have an Android phone sorry) then resend the image, the encoded message won't preserve. I suppose it's because the file format changes while downloading the image.
