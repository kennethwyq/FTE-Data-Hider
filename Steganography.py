from PIL import Image

# Helper Functions
def int_to_bin(value):
    """Convert an integer to an 8-bit binary string."""
    return format(value, '08b')

def bin_to_int(binary_value):
    """Convert an 8-bit binary string to an integer."""
    return int(binary_value, 2)

# LSB encoding for PNG with proper RGBA handling
def hide_data_in_png(image_path, secret_data):
    """Hide data in PNG image using LSB encoding."""
    img = Image.open(image_path)
    pixels = list(img.getdata())

    # Check if image is RGBA or RGB
    is_rgba = len(pixels[0]) == 4

    binary_secret_data = ''.join([int_to_bin(byte) for byte in secret_data])
    total_bits = len(binary_secret_data)

    if total_bits > len(pixels):
        raise ValueError(f"Not enough space in image to hide {total_bits} bits of data.")

    pixel_index = 0
    print(f"Total bits to hide: {total_bits}")
    for bit in binary_secret_data:
        r, g, b, *a = pixels[pixel_index] if is_rgba else (*pixels[pixel_index],)  # Handle RGBA and RGB

        # Modify the LSB of the red channel to hide the bit
        r = (r & ~1) | int(bit)

        pixels[pixel_index] = (r, g, b, *a) if is_rgba else (r, g, b)

        print(f"Embedding bit {bit} at pixel {pixel_index}, red channel before: {r & ~1}, after: {r}")
        pixel_index += 1

    # Save the modified image
    img.putdata(pixels)
    modified_image_path = "images/image_with_hidden_data2.png"
    img.save(modified_image_path)
    print(f"Modified image saved as: {modified_image_path}")

    return True


def extract_data_from_png(image_path, data_length):
    """Extract hidden data from PNG image."""
    img = Image.open(image_path)
    pixels = list(img.getdata())

    # Check if image is RGBA or RGB
    is_rgba = len(pixels[0]) == 4

    binary_data = []
    pixel_index = 0
    print(f"Extracting {data_length * 8} bits of data.")

    for _ in range(data_length * 8):
        r, g, b, *a = pixels[pixel_index] if is_rgba else (*pixels[pixel_index],)

        # Extract the LSB of the red channel
        extracted_bit = str(r & 1)
        binary_data.append(extracted_bit)

        print(f"Extracted bit {extracted_bit} from pixel {pixel_index}, red channel: {r}")
        pixel_index += 1

    # Convert the binary data back into bytes
    binary_string = ''.join(binary_data)
    extracted_data = bytes([bin_to_int(binary_string[i:i + 8]) for i in range(0, len(binary_string), 8)])

    print(f"Extracted Binary Data (as bits): {binary_string}")
    print(f"Extracted Data (Hex): {extracted_data.hex()}")

    return extracted_data
