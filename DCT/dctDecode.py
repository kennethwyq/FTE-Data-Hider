# import cv2
# import struct
# import bitstring
# import numpy as np
#
# # Files
# import dctZigZag as zigzag
# import dctEmbed_Extract as encode
# import dctMain as main
# import dct as dct
#
# stego_image = cv2.imread(main.STEGO_IMAGE_FILEPATH, flags=cv2.IMREAD_COLOR)
# stego_image_f32 = np.float32(stego_image)
# stego_image_YCC = dct.YCC_Image(cv2.cvtColor(stego_image_f32, cv2.COLOR_BGR2YCrCb))
#
# # FORWARD DCT STAGE
# dct_blocks = [cv2.dct(block) for block in stego_image_YCC.channels[0]]  # Only care about Luminance layer
#
# # QUANTIZATION STAGE
# dct_quants = [np.around(np.divide(item, dct.JPEG_STD_LUM_QUANT_TABLE)) for item in dct_blocks]
#
# # Sort DCT coefficients by frequency
# sorted_coefficients = [zigzag.zigzag(block) for block in dct_quants]
#
# # DATA EXTRACTION STAGE
# recovered_data = encode.extract_encoded_data_dct(sorted_coefficients)
# recovered_data_stream = bitstring.BitStream(recovered_data)  # Convert to BitStream
# recovered_data_stream.bitpos = 0  # Use bitpos instead of pos
#
# # Determine length of secret message
# data_len = int(recovered_data_stream.read('uint:32'))  # Read the length in bits
# data_len_bytes = data_len // 8  # Convert length to bytes
#
# # Debugging prints
# print(f"Recovered data length in bits: {data_len}")
# print(f"Recovered data length in bytes: {data_len_bytes}")
# print(f"Recovered data bits: {recovered_data_stream.bin}")
#
# # Extract secret message from DCT coefficients
# extracted_data = bytes()
# for _ in range(data_len_bytes):
#     extracted_data += struct.pack('>B', recovered_data_stream.read('uint:8'))
#
# # Print secret message back to the user
# print(extracted_data.decode('ascii'))


import cv2
import struct
import bitstring
import numpy as np

# Files
import DCT.dctZigZag as zigzag
import DCT.dctEmbed_Extract as encode
import DCT.dctMain as main
import DCT.dct as dct

def extract_secret_message_from_stego(STEGO_IMAGE_FILEPATH):
    # Load the stego image
    stego_image = cv2.imread(STEGO_IMAGE_FILEPATH, flags=cv2.IMREAD_COLOR)
    stego_image_f32 = np.float32(stego_image)
    stego_image_YCC = dct.YCC_Image(cv2.cvtColor(stego_image_f32, cv2.COLOR_BGR2YCrCb))

    # FORWARD DCT STAGE
    dct_blocks = [cv2.dct(block) for block in stego_image_YCC.channels[0]]  # Only care about Luminance layer

    # QUANTIZATION STAGE
    dct_quants = [np.around(np.divide(item, dct.JPEG_STD_LUM_QUANT_TABLE)) for item in dct_blocks]

    # Sort DCT coefficients by frequency
    sorted_coefficients = [zigzag.zigzag(block) for block in dct_quants]

    # DATA EXTRACTION STAGE
    recovered_data = encode.extract_encoded_data_dct(sorted_coefficients)
    recovered_data_stream = bitstring.BitStream(recovered_data)  # Convert to BitStream
    recovered_data_stream.bitpos = 0  # Use bitpos instead of pos

    # Determine length of secret message
    data_len = int(recovered_data_stream.read('uint:32'))  # Read the length in bits
    data_len_bytes = data_len // 8  # Convert length to bytes

    # Debugging prints
    print(f"Recovered data length in bits: {data_len}")
    print(f"Recovered data length in bytes: {data_len_bytes}")
    print(f"Recovered data bits: {recovered_data_stream.bin}")

    # Extract secret message from DCT coefficients
    extracted_data = bytes()
    for _ in range(data_len_bytes):
        extracted_data += struct.pack('>B', recovered_data_stream.read('uint:8'))

    # Print secret message back to the user
    decoded_message = extracted_data.decode('ascii')
    print(f"Decoded secret message: {decoded_message}")
    return decoded_message

# # Example usage:
# STOGO_IMAGE_PATH = "../images/stego_gnar.jpg"
# secret_message = extract_secret_message_from_stego(STOGO_IMAGE_PATH)
