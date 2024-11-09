from PIL import Image
import os

# Define the secret data to hide
secret_data = b'p..?\xa8\x8f\xf3M\x0e3\x18\xb8;Ml\xef\x10\x160h\xd4\xfb\x1aO\x96\xa0VO^\xb0^\xe8\x8a\xc2\xca\x9b\xe8\xba\xbc\x17?P\xea\xed\x0eK:\xa1\x8a\xc7\x01\xc9\xd9F\x16\xef}\xf1\xc9)\xfc\xfd\xc5d\x97<\tA\xe7I\xe6\xf4\x97\x8b\x95\x9f\x8c\\`d\xe0NC\x0b\xe9\xc6}\xf8\xf8\xd3}\xf1Y\xb2\x14\xc4{G9\xb6\xa0x|\x92\x0f\xb3\xfb\xa4\xc3\x11\x94\xcb_\xbdSP\xd8tF\xae\xf3i6h\x02\x0f\xa4\xce\xd2\xda\x8d\x0c!b:\x8eQ\xd7+L\xee\xfd\xb6=X\xb8w\xb2Z\x03n\xab3%\xa4\x8c\x03%e\xc3\xb7XRo)\x9d\xb9\xf4\xfdx\xd2\x90N<x\xbc\xcaMh[\xf4\x8b\xbc{G\x14\x83\xe81\x8a0\\\\\x9d\x97V\xfcI\xe1\x82\xf7\xf3\xdcc\x9a\x88\x8b\xe6L\x1d\xbf\xd6w\x0c~<k\x0c\xe9\xbe\xfcb{$\x87\xbfo\x86n\xd4\xbbY\x8c\xaa\xc4|Gh\xe96/\xe3k\xab\xd77w\xc6o\xa5\xc5^\x1cL\xb0\xfe\xf5\xa7Sg\'E\xb3\x87C3\xdf\xfe\xf2X.\x1f\xe5i\xbc\x94\xb0\x82\x99\xef\xc7\xb3\xf07\xef\xe4R\x10\xed\xda }E\xb4*|\xd5\xc0\xeb)\xc2\xd3\xcf;\x8e\xf1\x96,\x04Y\x14\xa49L\xb2J\x1f\x1e34\xfb\xff\xe8\xfd\xd3{\x94}+13\\\xc1\x07Nb\x13n\x7f\xab\x04\x7f\x00\xbe\x94F\xa3\x11\xb3\xe1r\x10\x1f\x89\xd9\xf5:\x96\xba\xe4\xd7\n=\xf8`\xc5\x8b\xf4jei\xc8\x04N\x13\xd3\x19\x7f\x01\x9f\x98\x12`9\xe5\x18b\x0e\xb6et)\xbd\x1fjG\x00\x8c\x06K\xae\xf1\xc0\xc5\x9157\xb9\x95e\xa8y\xf4r\xfb\xab\x9d\xc1V\xafG\xbd2C\xfe\xcaQ\x10\'?\xbaA\x08\x86\x80\xdb6\xbc\x05\x02\xb9\xe9]q\x17o\x9c\xccP\xc7\x89\xac\xfdy\x04&5\xa5\x8f\x08\x11_\xae\xd6\x7fQ\xf9\xae\xaf\xfa^\xc3<\xce\xbc$\xd9\xa9D\xfa\x16\x91q\x19\xf2\xb3=\x88`\x1d\xcen\xb1|"|o\xe5O\xd4\xad\x02\xa7\xf6\t\xd0#+\x1f>n'

# Set up a sample PNG file path (ensure the image exists at this path or create one if needed)
image_path = "test_image.png"

# Check if the image file exists, otherwise create a simple RGB image to test
if not os.path.exists(image_path):
    # Create a blank RGB image for testing
    img = Image.new('RGB', (200, 200), color=(255, 255, 255))
    img.save(image_path)

# Helper Functions
def int_to_bin(value):
    """Convert an integer to an 8-bit binary string."""
    return format(value, '08b')

def bin_to_int(binary_value):
    """Convert an 8-bit binary string to an integer."""
    return int(binary_value, 2)

# LSB encoding for PNG with RGB channel support
def hide_data_in_png(image_path, secret_data):
    """Hide data in all RGB channels of PNG image using LSB encoding and save it back to the original image."""
    img = Image.open(image_path)
    pixels = list(img.getdata())

    binary_secret_data = ''.join([int_to_bin(byte) for byte in secret_data])
    total_bits = len(binary_secret_data)

    if total_bits > len(pixels) * 3:
        raise ValueError(f"Not enough space in image to hide {total_bits} bits of data.")

    pixel_index = 0
    color_index = 0
    print(f"Total bits to hide: {total_bits}")

    for bit in binary_secret_data:
        r, g, b = pixels[pixel_index]

        # Change the respective color channel based on color_index (cycle through R, G, B)
        if color_index == 0:  # Red channel
            r = (r & ~1) | int(bit)
        elif color_index == 1:  # Green channel
            g = (g & ~1) | int(bit)
        elif color_index == 2:  # Blue channel
            b = (b & ~1) | int(bit)

        # Set the new pixel and update indices
        pixels[pixel_index] = (r, g, b)
        color_index = (color_index + 1) % 3
        if color_index == 0:
            pixel_index += 1

    # Save the modified image back to the original file
    img.putdata(pixels)
    img.save(image_path)
    print("Data length (in bytes):", len(secret_data))
    print(f"Data hidden successfully in the original image: {image_path}")
    return True

def extract_data_from_png(image_path, data_length):
    """Extract hidden data from PNG image across RGB channels."""
    img = Image.open(image_path)
    pixels = list(img.getdata())

    binary_data = []
    pixel_index = 0
    color_index = 0
    print(f"Extracting {data_length * 8} bits of data.")

    for _ in range(data_length * 8):
        r, g, b = pixels[pixel_index]

        # Extract the LSB of the respective channel based on color_index
        if color_index == 0:  # Red channel
            binary_data.append(str(r & 1))
        elif color_index == 1:  # Green channel
            binary_data.append(str(g & 1))
        elif color_index == 2:  # Blue channel
            binary_data.append(str(b & 1))

        color_index = (color_index + 1) % 3
        if color_index == 0:
            pixel_index += 1

    binary_string = ''.join(binary_data)
    extracted_data = bytes([bin_to_int(binary_string[i:i + 8]) for i in range(0, len(binary_string), 8)])
    print(f"Extracted Binary Data (as bits): {binary_string[:64]}...")  # Show only the first 64 bits for brevity
    print(f"Extracted Data (Hex): {extracted_data.hex()}")
    return extracted_data

# Test the hiding and extraction functions
try:
    print("\n--- Hiding Data ---")
    hide_data_in_png(image_path, secret_data)
    
    print("\n--- Extracting Data ---")
    extracted_data = extract_data_from_png(image_path, len(secret_data))
    
    # Check if the extracted data matches the original secret data
    if extracted_data == secret_data:
        print("\nSuccess: Extracted data matches the original secret data!")
    else:
        print("\nFailure: Extracted data does not match the original secret data.")
except Exception as e:
    print("An error occurred:", e)
