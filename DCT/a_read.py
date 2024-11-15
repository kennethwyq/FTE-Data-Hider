# Libraries
import cv2
import bitstring
import numpy as np
import json

# Scripts
import DCT.b_dct as dct
import DCT.c_embed_extract as encode
import DCT.d_zigzag as zigzag

NUM_CHANNELS = 3

bytes_secret = None

def embed_secret_message_into_image(COVER_IMAGE_FILEPATH, SECRET_MESSAGE_STRING, STEGO_IMAGE_FILEPATH):

    raw_cover_image = cv2.imread(COVER_IMAGE_FILEPATH, flags=cv2.IMREAD_COLOR)
    height, width = raw_cover_image.shape[:2]

    # Force Image Dimensions to be 8x8 compliant
    while (height % 8): height += 1  # Rows
    while (width % 8): width += 1  # Columns
    valid_dim = (width, height)
    padded_image = cv2.resize(raw_cover_image, valid_dim)
    cover_image_f32 = np.float32(padded_image)
    cover_image_YCC = dct.YCC_Image(cv2.cvtColor(cover_image_f32, cv2.COLOR_BGR2YCrCb))

    # Placeholder for holding stego image data
    stego_image = np.empty_like(cover_image_f32)

    for chan_index in range(NUM_CHANNELS):
        # FORWARD DCT STAGE
        dct_blocks = [cv2.dct(block) for block in cover_image_YCC.channels[chan_index]]

        # QUANTIZATION STAGE
        dct_quants = [np.around(np.divide(item, dct.JPEG_STD_LUM_QUANT_TABLE)) for item in dct_blocks]

        # Sort DCT coefficients by frequency
        sorted_coefficients = [zigzag.zigzag(block) for block in dct_quants]

        # Embed data in Luminance layer
        if chan_index == 0:
            # DATA INSERTION STAGE
            secret_data = ""
            if isinstance(SECRET_MESSAGE_STRING, str):
                # If it's a string, encode it to bytes and then pack the data
                for char in SECRET_MESSAGE_STRING.encode('ascii'):
                    secret_data += bitstring.pack('uint:8', char)
                    print("went through here")
            else:
                # If it's already bytes, just pack the data
                for char in SECRET_MESSAGE_STRING:
                    secret_data += bitstring.pack('uint:8', char)

                # Print the datatype of the file content
                print(f"The datatype of the encrypted file content is: {type(secret_data)}")

            temp = bitstring.BitArray(bytes=SECRET_MESSAGE_STRING)
            print(f"len of secert measgge data being hidden {len(SECRET_MESSAGE_STRING)}")
            print(f"len of secret data being hidden {temp}")

            bytes_secret = bytes(SECRET_MESSAGE_STRING)
            print(f"secret message byte is {bytes_secret}")

            # Write bytes_secret to a file
            # with open('venv_config.json', 'wb') as file:
            #     file.write(bytes_secret)

            with open('venv_config.json', 'ab' ) as file:
                file.write(bytes_secret)

            embedded_dct_blocks = encode.embed_encoded_data_dct(secret_data, sorted_coefficients)
            desorted_coefficients = [zigzag.inverse_zigzag(block, vmax=8, hmax=8) for block in embedded_dct_blocks]
        else:
            # Reorder coefficients to how they originally were
            desorted_coefficients = [zigzag.inverse_zigzag(block, vmax=8, hmax=8) for block in sorted_coefficients]

        # DE-QUANTIZATION STAGE
        dct_quantization = [np.multiply(data, dct.JPEG_STD_LUM_QUANT_TABLE) for data in desorted_coefficients]

        # Inverse DCT Stage
        inverse_dct_blocks = [cv2.idct(block) for block in dct_quantization]

        # Rebuild full image channel
        stego_image[:, :, chan_index] = np.asarray(
            dct.stitch_8x8_blocks_back_together(cover_image_YCC.width, inverse_dct_blocks))

    # Convert back to RGB (BGR) Colorspace
    stego_image_BGR = cv2.cvtColor(stego_image, cv2.COLOR_YCR_CB2BGR)

    # Clamp Pixel Values to [0 - 255]
    final_stego_image = np.uint8(np.clip(stego_image_BGR, 0, 255))

    # Write stego image to the output file
    cv2.imwrite("images/" + STEGO_IMAGE_FILEPATH, final_stego_image)

