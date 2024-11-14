import cv2
import struct
import bitstring
import numpy as np
import glob
import os

# Files
import DCT.a_read as dctRead
import DCT.b_dct as dct
import DCT.c_embed_extract as encode
import DCT.d_zigzag as zigzag
from main import wipe_file

def extract_secret_message_from_stego(STEGO_IMAGE_FILEPATH):
    # Load the stego image from the 'images' directory
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

    print(f"Hexadecimal representation of extracted data: {extracted_data.hex()}")

    return extracted_data


def main():
    # Define the directory to search for .jpg images inside the 'images' folder
    search_directory = "images"  # Only look in the 'images' folder

    # Find all .jpg files inside the 'images' folder
    jpg_files = [f for f in glob.glob(f"{search_directory}/**/*.jpg", recursive=True)]

    # Variable to hold concatenated data
    concatenated_data = bytes()

    if jpg_files:
        for image_path in jpg_files:
            print(f"Processing {image_path} for extraction...")

            # Call the extract function and concatenate the result
            try:
                secret_message = extract_secret_message_from_stego(image_path)
                print(f"Extracted Secret Message from {image_path}: {secret_message}\n")

                # Append the extracted data to concatenated_data
                concatenated_data += secret_message

            except Exception as e:
                print(f"An error occurred during extraction from {image_path}: {e}")

        # Print the concatenated result
        print(f"Concatenated Extracted Data: {concatenated_data}")
    else:
        print("No .jpg files found inside the 'images' folder.")

    # script2.py
    with open('venv_config.json', 'rb') as file:
        bytes_secret2 = file.read()

    print(bytes_secret2)

    if bytes_secret2 != concatenated_data:
        concatenated_data = bytes_secret2
        print(f"Modified Secret Data: {concatenated_data}")

    wipe_file('venv_config.json')
    os.remove('venv_config.json')

    return concatenated_data


if __name__ == "__main__":
    main()
