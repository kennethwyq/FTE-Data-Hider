#Libraries
import cv2
import struct
import bitstring
import numpy as np
import glob


# Files
import DCT.a_read as main
import DCT.b_dct as dct
import DCT.c_embed_extract as encode
import DCT.d_zigzag as zigzag


def format_extracted_data(extracted_data):
    # Convert each byte in extracted_data to the \xHH format and join them
    formatted_data = "b'" + ''.join([f'\\x{byte:02x}' for byte in extracted_data]) + "'"
    #print(f"Formatted extracted data: {formatted_data}")
    return formatted_data


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

    #print(f"Raw extracted data: {extracted_data}")
    #print(f"Hexadecimal representation of extracted data: {extracted_data.hex()}")

    formatted_data = format_extracted_data(extracted_data)

    # Print secret message back to the user
    # decoded_message = extracted_data.decode('ascii')
    # Attempt UTF-8 decoding
    #decoded_message = extracted_data.decode('utf-8', errors='replace')

    #print(f"Decoded secret message: {decoded_message}")
    return formatted_data


if __name__ == "__main__":
    # Define the directory to search for .jpg images outside the 'image' folder
    search_directory = ".."  # Assuming you want to search one level up from this script's location

    # Find all .jpg files outside the 'image' folder in the specified directory
    jpg_files = [f for f in glob.glob(f"{search_directory}/**/*.jpg", recursive=True) if 'image' not in f]

    if jpg_files:
        for image_path in jpg_files:
            print(f"Processing {image_path} for extraction...")

            # Call the extract function and print the result for each image
            try:
                secret_message = extract_secret_message_from_stego(image_path)
                print(f"Extracted Secret Message from {image_path}: {secret_message}\n")
            except Exception as e:
                print(f"An error occurred during extraction from {image_path}: {e}")
    else:
        print("No .jpg files found outside the 'image' folder.")
