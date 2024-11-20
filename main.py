#Libraries
import sys
import winreg
import random
from pathlib import Path
from binascii import hexlify, unhexlify
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.SecretSharing import Shamir
import shutil

#Scripts
import LSB.LSB as lsb
import ADS.ads as ads
import EOI.jpegeol as eol
import DCT.a_read as dctRead
import DCT.b_dct as dct
import DCT.c_embed_extract as dctEmbed_Extract
import DCT.d_zigzag as dctZigzag
import DCT.e_decode as dctDecode


REG_PATH = r"SOFTWARE\f3832454-4e14-a1b9-0f614e507aa5"
AES_KEY_SIZE = 32  # 256 bits for AES-256
IV_SIZE = 16
THRESHOLD = 3  # Minimum number of shares required to recover the key
TOTAL_SHARES = 5  # Total number of shares


# Function to create fake software registry keys
def create_fake_registry_key():
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)

    # Define fake values for the key (anti-forensics layer)
    winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Fake Software")
    winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
    winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Fake Publisher Inc.")
    winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, "20240925")
    winreg.SetValueEx(
        key, "InstallLocation", 0, winreg.REG_SZ, r"C:\Program Files\Fake Software"
    )
    winreg.CloseKey(key)


def clean_up_registry():
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_PATH)


def check_registry_for_key():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ)
        return True
    except FileNotFoundError:
        return False


# Function to generate a new AES key and split it into parts using SSS
def generate_secret_key():
    key = get_random_bytes(AES_KEY_SIZE)
    print(f"Generated AES Key: {key.hex()}")
    iv = get_random_bytes(IV_SIZE)
    return key, iv


def split_and_store_key(key, iv):
    key_parts_1 = Shamir.split(THRESHOLD, TOTAL_SHARES, key[:16])
    key_parts_2 = Shamir.split(THRESHOLD, TOTAL_SHARES, key[16:])
    iv_parts = Shamir.split(THRESHOLD, TOTAL_SHARES, iv)

    # Create fake registry key (anti-forensics)
    create_fake_registry_key()

    # Store real encryption-related values in the registry
    for idx, part in key_parts_1:
        reg_name = f"Cache{idx}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as reg_key:
            winreg.SetValueEx(
                reg_key, reg_name, 0, winreg.REG_SZ, hexlify(part).decode()
            )
    for idx, part in key_parts_2:
        reg_name = f"Config{idx}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as reg_key:
            winreg.SetValueEx(
                reg_key, reg_name, 0, winreg.REG_SZ, hexlify(part).decode()
            )
    for idx, part in iv_parts:
        reg_name = f"Temp{idx}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as reg_key:
            winreg.SetValueEx(
                reg_key, reg_name, 0, winreg.REG_SZ, hexlify(part).decode()
            )


def retrieve_key_from_registry():
    key_parts_1 = []
    key_parts_2 = []
    iv_parts = []
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ
    ) as reg_key:
        for idx in range(1, TOTAL_SHARES + 1):
            try:
                reg_name = f"Cache{idx}"
                part, _ = winreg.QueryValueEx(reg_key, reg_name)
                key_parts_1.append((idx, unhexlify(part)))
            except FileNotFoundError:
                pass
            try:
                reg_name = f"Config{idx}"
                part, _ = winreg.QueryValueEx(reg_key, reg_name)
                key_parts_2.append((idx, unhexlify(part)))
            except FileNotFoundError:
                pass
            try:
                reg_name = f"Temp{idx}"
                part, _ = winreg.QueryValueEx(reg_key, reg_name)
                iv_parts.append((idx, unhexlify(part)))
            except FileNotFoundError:
                pass
    return key_parts_1, key_parts_2, iv_parts


def reconstruct_key():
    key_parts_1, key_parts_2, iv_parts = retrieve_key_from_registry()
    if (
        len(key_parts_1) >= THRESHOLD
        and len(key_parts_2) >= THRESHOLD
        and len(iv_parts) >= THRESHOLD
    ):
        key_part_1 = Shamir.combine(key_parts_1)
        key_part_2 = Shamir.combine(key_parts_2)
        iv_parts = Shamir.combine(iv_parts)
        return key_part_1 + key_part_2, iv_parts
    else:
        print("Number of shares is less than the required threshold.")
        sys.exit(1)


def split_byte_data(data, num_parts):
    part_size = len(data) // num_parts
    remainder = len(data) % num_parts 

    parts = []
    start = 0
    
    for i in range(num_parts):
        end = start + part_size + (1 if i < remainder else 0)
        parts.append(data[start:end]) 
        start = end
    
    return parts


# Encrypt and hide data in PNG & JPG
def hide_mode(steg_technique, path_of_data, number_of_files):
    if not check_registry_for_key():
        key, iv = generate_secret_key()
        split_and_store_key(key, iv)
    key, iv = reconstruct_key()

    number_of_files = int(number_of_files)
    with open(path_of_data, 'rb') as file:
        file_data = file.read()

    path = Path("images") #TODO: let user choose which folder of files to use as hiding medium or default
    cipher = AES.new(key, AES.MODE_EAX, iv)

    ciphertext = cipher.encrypt(file_data)  # Continue using the same cipher instance
    print("\nOriginal Data (Hex):")
    print(hexlify(ciphertext))  # Print original data in hexadecimal
    splitted_data = split_byte_data(ciphertext, number_of_files)
    # Ensure `list_of_used_files` is limited to the number of data chunks
    list_of_used_files = []
    
    if steg_technique.lower() == "lsb":
        length_file = "LSB/lsb_data_length.txt"
        # Calculate the total byte length of all chunks
        total_data_length = sum(len(chunk) for chunk in splitted_data)

        # Save the total length to `lsb_data_length.txt`
        with open(length_file, 'w') as length_file_obj:
            length_file_obj.write(str(total_data_length))
        print(f"Total data length saved: {total_data_length} bytes")

        # Retrieve available files from the "images" directory
        # Choose the image to hide data in (for simplicity, we're using the first PNG file)
        path = Path("images")
        png_files = [file for file in path.iterdir() if file.suffix.lower() == '.png']
    
        if len(png_files) < len(splitted_data):
            print(f"Not enough PNG images to hide data. Required: {len(splitted_data)}, available: {len(png_files)}.")
            sys.exit(1)
    
            # Loop through each chunk and each file, hiding the data
        for i, data_chunk in enumerate(splitted_data):
            file_path = str(png_files[i])
            list_of_used_files.append(file_path)  
            # Hide the chunk in the current PNG file
            print(f"Hiding data chunk in {file_path}")
            lsb.hide_data_in_png(file_path, data_chunk)

        print("All data chunks have been hidden successfully.")

        
    elif steg_technique.lower() == "dct":
        # List comprehension to retrieve file names
        list_of_used_files = [file.name for file in path.iterdir() if file.is_file() and file.suffix in ['.jpg']]
        list_of_used_files = list_of_used_files[:len(splitted_data)]

        if len(list_of_used_files) != len(splitted_data):
            print(f"Not enough images to be used. Number of images needed is {len(splitted_data)}.")
            sys.exit(1)

        for i in range(len(splitted_data)):
            data = splitted_data[i]
            file_path = str(path.absolute()) + '\\' + list_of_used_files[i]
            dctRead.embed_secret_message_into_image(file_path, data, list_of_used_files[i])

        print("All data chunks have been hidden successfully.")

    elif steg_technique.lower() == "ads":
        # List comprehension to retrieve file names
        list_of_used_files = [file.name for file in path.iterdir() if file.is_file()]
        list_of_used_files = list_of_used_files[:len(splitted_data)]

        if len(list_of_used_files) != len(splitted_data):
            print(f"Not enough images to be used. Number of images needed is {len(splitted_data)}.")
            sys.exit(1)

        for i in range(len(splitted_data)):
            data = splitted_data[i]
            file_path = str(path.absolute())+'\\'+ list_of_used_files[i]
            stream_name = '1'
            # Hide the encrypted data in the image
            ads.write_ads(data, file_path, stream_name)


    elif steg_technique.lower() == "eol":
        # List comprehension to retrieve file names
        list_of_used_files = [file.name for file in path.iterdir() if file.is_file() and file.suffix == '.jpeg']
        list_of_used_files = list_of_used_files[:len(splitted_data)]
        print(len(list_of_used_files))
        print(len(splitted_data))

        if len(list_of_used_files) != len(splitted_data):
            print(f"Not enough images to be used. Number of images needed is {len(splitted_data)}.")
            sys.exit(1)

        for i in range(len(splitted_data)):
            data = splitted_data[i]
            file_path = str(path.absolute()) + '\\' + list_of_used_files[i]
            # Hide the encrypted data in the image
            jpeg_bytes = eol.read_jpeg(file_path)
            eol_position = eol.eol_jpeg(jpeg_bytes)
            new_jpeg_bytes = eol.insert(jpeg_bytes, eol_position, data)
            eol.overwrite(new_jpeg_bytes, file_path)


    elif steg_technique.lower() =="default":
        split_point = (number_of_files + 1) // 2 
        chunks_DCT = splitted_data[:split_point]
        chunks_ADS = splitted_data[split_point:]
        list_of_used_files_DCT = [file.name for file in path.iterdir() if file.is_file() and file.suffix in ['.jpg']]
        list_of_used_files_ADS = [file.name for file in path.iterdir() if file.is_file() and file.suffix.lower() != '.jpg']
        list_of_used_files_DCT = list_of_used_files_DCT[:split_point]
        list_of_used_files_ADS = list_of_used_files_ADS[:(number_of_files-split_point)]

        if len(list_of_used_files_DCT) != len(chunks_DCT):
            print(f"Not enough images to be used. Number of images for DCT needed is {len(chunks_DCT)}.")
            sys.exit(1)

        for i in range(len(chunks_DCT)):
            data = chunks_DCT[i]
            file_path = str(path.absolute()) + '\\' + list_of_used_files_DCT[i]
            # Hide the encrypted data in the image
            # hide_data_in_png(file, )
            dctRead.embed_secret_message_into_image(file_path, data, list_of_used_files_DCT[i])

        if len(list_of_used_files_ADS) != len(chunks_ADS):
            print(f"Not enough images to be used. Number of images for ADS needed is {len(chunks_ADS)}.")
            sys.exit(1)

        for i in range(len(chunks_ADS)):
            data = chunks_ADS[i]
            file_path = str(path.absolute())+'\\'+ list_of_used_files_ADS[i]
            stream_name = '1'
            # Hide the encrypted data in the image
            ads.write_ads(data, file_path, stream_name)
        list_of_used_files = list_of_used_files_DCT + list_of_used_files_ADS
        pass

    cipher = AES.new(key, AES.MODE_EAX, iv)
    order = ','.join([str(file_path) for file_path in list_of_used_files])
    order = order.encode()
    encrypted_order = cipher.encrypt(order)
    with open('order.txt', 'wb') as order_file:
        order_file.write(encrypted_order)
    print("Encrypted order saved to order.txt")
    wipe_file(path_of_data)
    print(f"Data from {file_path} has been hidden and the original file securely wiped.")


def unhide_mode(technique):
    key, iv = reconstruct_key()
    cipher = AES.new(key, AES.MODE_EAX, iv)
    path = Path("images") #TODO: let user choose which folder of files to use as hiding medium or default

    try:
        with open('order.txt', 'rb') as order_file:
            encrypted_order = order_file.read()
            decrypted_order = cipher.decrypt(encrypted_order)
            print(decrypted_order)
            decrypted_order = decrypted_order.decode()
            print("Decrypted order:", decrypted_order)

    except Exception as e:
        print("Error decrypting order.txt:", e)
        sys.exit(1)

    encrypted_original_data = b""

    if technique.lower() == "ads":
        ordered_files = decrypted_order.split(',')
        for file in ordered_files:
            file_path = str(path.absolute())+'\\'+ file
            print(file_path)
            data = ads.read_ads(file_path, "1")
            encrypted_original_data += data

    elif technique.lower() == "lsb":
        ordered_files = decrypted_order.split(',')
        for file in ordered_files:
            file_path = Path(str(path.absolute())+'\\'+ file)
            target_folder = file_path.parent.parent / "LSB"  # Move to the "LSB" folder in the same directory as "images"

            if not target_folder.exists():
                print(f"The target folder '{target_folder}' does not exist.")
            else:
                # Move the file if the folder exists
                shutil.move(str(file_path), str(target_folder / file_path.name))
                print(f"Moved {file_path} to {target_folder}")
        encrypted_original_data = lsb.extract_data_from_png(ordered_files)
        pass

    elif technique.lower() == "dct":
        ordered_files = decrypted_order.split(',')
        for file in ordered_files:
            file_path = Path(path.absolute()) / file  # Convert to a Path object
            target_folder = file_path.parent.parent  # Access the parent.parent attribute
            shutil.move(str(file_path), str(target_folder / file_path.name))  # Use Path for consistency
            print(f"Moved {file_path} to {target_folder}")

        encrypted_original_data = dctDecode.main()
        pass

    elif technique.lower() == "eol":
        ordered_files = decrypted_order.split(',')
        for file in ordered_files:
            jpeg_file = str(path.absolute())+'\\'+ file
            jpeg_bytes = eol.read_jpeg(jpeg_file)
            eol_position = eol.eol_jpeg(jpeg_bytes)
            hidden_data = eol.retrieve(jpeg_bytes, eol_position)
            print(hidden_data)
            encrypted_original_data += hidden_data
            remove_data = eol.remove(jpeg_bytes, eol_position)
            # overwrite(remove_data, jpeg_file)

    elif technique.lower() == "default":
        encrypted_original_data_pt1 = b""
        encrypted_original_data_pt2 = b""

        ordered_files = decrypted_order.split(',')
        for file in ordered_files:
            if(Path(file).suffix in [".jpg"]):
                file_path = Path(str(path.absolute())+'\\'+ file)
                target_folder = file_path.parent.parent 
                shutil.move(str(file_path), str(target_folder / file_path.name))
                print(f"Moved {file_path} to {target_folder}")
        encrypted_original_data_pt1 = dctDecode.main()
        ordered_files = decrypted_order.split(',')
        for file in ordered_files:
            print(file)
            if(Path(file).suffix not in [".jpg"]):
                file_path = str(path.absolute())+'\\'+ file
                print(file_path)
                data = ads.read_ads(file_path, "1")
                encrypted_original_data_pt2 += data

        encrypted_original_data = encrypted_original_data_pt1 + encrypted_original_data_pt2
        pass
    else:
        print("Technique Doesn't Exist")
        sys.exit(1)

    cipher = AES.new(key, AES.MODE_EAX, iv)

    original_data = cipher.decrypt(encrypted_original_data)
    print(f'the original data is {original_data}')

    decoded_text = original_data.decode('utf-8')
    print(f'the decoded data is {decoded_text}')

    with open("output.txt", "w") as output_file:
        output_file.write(decoded_text)
    print("Data written to output.txt in original text form.")
    pass


def wipe_file(file_path):
    with open(file_path, 'r+b') as file:
        file.seek(0, 2) 
        size = file.tell()  
        file.seek(0)
        file.write(b'\x00' * size)
        file.truncate()


# Main function
def main():
    print(f"Arguments passed: {sys.argv}")
    if sys.argv[1] == "hide":
        if len(sys.argv) < 4:
            print("Usage for hide mode: python main.py hide <steg_technique> <data> <number of files>")
            sys.exit(1)
        print("Entering hide mode")
        hide_mode(sys.argv[2],sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "unhide":
        if len(sys.argv) < 2:
            print("Usage for unhide mode: python main.py unhide <technique>")
            sys.exit(1)
        print("Entering unhide mode")
        unhide_mode(sys.argv[2])
    else:
        print("Invalid mode. Use 'hide' or 'unhide'.")


if __name__ == "__main__":
    print("Calling main...")
    main()
