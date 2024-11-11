from PIL import Image
import os
from binascii import hexlify

# Define the secret data to hide
#secret_data = b'p..?\xa8\x8f\xf3M\x0e3\x18\xb8;Ml\xef\x10\x160h\xd4\xfb\x1aO\x96\xa0VO^\xb0^\xe8\x8a\xc2\xca\x9b\xe8\xba\xbc\x17?P\xea\xed\x0eK:\xa1\x8a\xc7\x01\xc9\xd9F\x16\xef}\xf1\xc9)\xfc\xfd\xc5d\x97<\tA\xe7I\xe6\xf4\x97\x8b\x95\x9f\x8c\\`d\xe0NC\x0b\xe9\xc6}\xf8\xf8\xd3}\xf1Y\xb2\x14\xc4{G9\xb6\xa0x|\x92\x0f\xb3\xfb\xa4\xc3\x11\x94\xcb_\xbdSP\xd8tF\xae\xf3i6h\x02\x0f\xa4\xce\xd2\xda\x8d\x0c!b:\x8eQ\xd7+L\xee\xfd\xb6=X\xb8w\xb2Z\x03n\xab3%\xa4\x8c\x03%e\xc3\xb7XRo)\x9d\xb9\xf4\xfdx\xd2\x90N<x\xbc\xcaMh[\xf4\x8b\xbc{G\x14\x83\xe81\x8a0\\\\\x9d\x97V\xfcI\xe1\x82\xf7\xf3\xdcc\x9a\x88\x8b\xe6L\x1d\xbf\xd6w\x0c~<k\x0c\xe9\xbe\xfcb{$\x87\xbfo\x86n\xd4\xbbY\x8c\xaa\xc4|Gh\xe96/\xe3k\xab\xd77w\xc6o\xa5\xc5^\x1cL\xb0\xfe\xf5\xa7Sg\'E\xb3\x87C3\xdf\xfe\xf2X.\x1f\xe5i\xbc\x94\xb0\x82\x99\xef\xc7\xb3\xf07\xef\xe4R\x10\xed\xda }E\xb4*|\xd5\xc0\xeb)\xc2\xd3\xcf;\x8e\xf1\x96,\x04Y\x14\xa49L\xb2J\x1f\x1e34\xfb\xff\xe8\xfd\xd3{\x94}+13\\\xc1\x07Nb\x13n\x7f\xab\x04\x7f\x00\xbe\x94F\xa3\x11\xb3\xe1r\x10\x1f\x89\xd9\xf5:\x96\xba\xe4\xd7\n=\xf8`\xc5\x8b\xf4jei\xc8\x04N\x13\xd3\x19\x7f\x01\x9f\x98\x12`9\xe5\x18b\x0e\xb6et)\xbd\x1fjG\x00\x8c\x06K\xae\xf1\xc0\xc5\x9157\xb9\x95e\xa8y\xf4r\xfb\xab\x9d\xc1V\xafG\xbd2C\xfe\xcaQ\x10\'?\xbaA\x08\x86\x80\xdb6\xbc\x05\x02\xb9\xe9]q\x17o\x9c\xccP\xc7\x89\xac\xfdy\x04&5\xa5\x8f\x08\x11_\xae\xd6\x7fQ\xf9\xae\xaf\xfa^\xc3<\xce\xbc$\xd9\xa9D\xfa\x16\x91q\x19\xf2\xb3=\x88`\x1d\xcen\xb1|"|o\xe5O\xd4\xad\x02\xa7\xf6\t\xd0#+\x1f>n'
#secret_data =b'123'
# Set up a sample PNG file path (ensure the image exists at this path or create one if needed)
#image_path = "test_image.png"
length_file = "lsb_data_length.txt"  


# Check if the image file exists, otherwise create a simple RGB image to test
#if not os.path.exists(image_path):
#    # Create a blank RGB image for testing
#    img = Image.new('RGB', (200, 200), color=(255, 255, 255))
#    img.save(image_path)

# Helper Functions
def int_to_bin(value):
    """Convert an integer to an 8-bit binary string."""
    return format(value, '08b')

def bin_to_int(binary_value):
    """Convert an 8-bit binary string to an integer."""
    return int(binary_value, 2)

# LSB encoding for PNG with RGB channel support
# Hiding data using LSB
# LSB encoding for PNG with RGB and RGBA channel support
def hide_data_in_png(image_path, secret_data):
    print(f"Saving data to image path: {image_path}")
    img = Image.open(image_path)
    
    # Ensure image mode is RGB; if RGBA, convert to RGB
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    pixels = list(img.getdata())

    binary_secret_data = ''.join([int_to_bin(byte) for byte in secret_data])
    total_bits = len(binary_secret_data)
    
    if total_bits > len(pixels) * 3:
        raise ValueError("Not enough space in the image.")

    # Embed data using LSB technique
    pixel_index, color_index = 0, 0
    for bit in binary_secret_data:
        r, g, b = pixels[pixel_index]
        
        # Alter the pixel color values based on the bit
        if color_index == 0:
            r = (r & ~1) | int(bit)
        elif color_index == 1:
            g = (g & ~1) | int(bit)
        elif color_index == 2:
            b = (b & ~1) | int(bit)
        
        # Save the modified pixel back
        pixels[pixel_index] = (r, g, b)
        
        # Move to the next color channel or pixel
        color_index = (color_index + 1) % 3
        if color_index == 0:
            pixel_index += 1

    # Save modified pixels to image and save the modified image
    img.putdata(pixels)
    img.save(image_path)
    print(f"Data successfully saved to {image_path}")

# Extracting data from LSB
# Function to extract data from a single or multiple PNGs using LSB
def extract_data_from_png(image_paths):
    """Extract hidden data from one or multiple PNG images using LSB and display in hex."""
    # Retrieve the total data length from lsb_data_length.txt
    with open(length_file, "r") as file:
        total_data_length = int(file.read().strip())
        print(f"Total data length retrieved: {total_data_length} bytes")

    extracted_data = b""
    remaining_data_length = total_data_length

    # Iterate over each image, extracting the relevant portion of data
    for image_path in image_paths:
        # Calculate the chunk length for this image
        chunk_length = min(256, remaining_data_length)  # Assuming max 256 bytes per chunk
        print(f"Extracting {chunk_length} bytes from {image_path}")

        img = Image.open(image_path)
        pixels = list(img.getdata())
        binary_data = []
        pixel_index, color_index = 0, 0

        # Extract binary data for the specified chunk length
        for _ in range(chunk_length * 8):  # Each byte has 8 bits
            r, g, b = pixels[pixel_index]
            if color_index == 0:
                binary_data.append(str(r & 1))
            elif color_index == 1:
                binary_data.append(str(g & 1))
            elif color_index == 2:
                binary_data.append(str(b & 1))
            color_index = (color_index + 1) % 3
            if color_index == 0:
                pixel_index += 1

        # Convert binary data to bytes
        binary_string = ''.join(binary_data)
        chunk_data = bytes([bin_to_int(binary_string[i:i + 8]) for i in range(0, len(binary_string), 8)])
        extracted_data += chunk_data
        remaining_data_length -= chunk_length

        # Stop if all data has been extracted
        if remaining_data_length <= 0:
            break

    # Print the extracted data in hexadecimal format for verification
    print("Extracted Data (Hex):")
    print(extracted_data.hex())
    return extracted_data


# Run the extraction script directly for unhiding more, 
# but remember to copy and paste the images folder files from main \FTE-Data-Hider\images
if __name__ == "__main__":
    image_paths = ["sample.png", "sample2.png"]  # Specify your image paths here
    extract_data_from_png(image_paths)


# Test extracting data
#if __name__ == "__main__":
#    image_path = "sample.png"  # Example path; change as needed
#    extract_data_from_png(image_path)

# Test hiding and extracting data
#if __name__ == "__main__":
#    try:
#        print("\n--- Hiding Data ---")
#        data_length = hide_data_in_png(image_path, secret_data)
#        
#        print("\n--- Extracting Data ---")
#        extracted_data = extract_data_from_png(image_path, data_length)
#        
        # Check if the extracted data matches the original secret data
#        if extracted_data == secret_data:
#            print("\nSuccess: Extracted data matches the original secret data!")
#        else:
#            print("\nFailure: Extracted data does not match the original secret data.")
#    
#    except Exception as e:
#        print("An error occurred:", e)


#if __name__ == "__main__":
    # Test the hiding and extraction functions
#    try:
#        print("\n--- Hiding Data ---")
#       hide_data_in_png(image_path, secret_data)
        
#        print("\n--- Extracting Data ---")
#        extracted_data = extract_data_from_png(image_path, len(secret_data))
        
        # Check if the extracted data matches the original secret data
#        if extracted_data == secret_data:
#            print("\nSuccess: Extracted data matches the original secret data!")
#        else:
#            print("\nFailure: Extracted data does not match the original secret data.")
#    except Exception as e:
#        print("An error occurred:", e)
