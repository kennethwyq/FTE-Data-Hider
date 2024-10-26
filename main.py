import sys
import winreg
import random
from pathlib import Path
from binascii import hexlify, unhexlify
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.SecretSharing import Shamir
from LSB.LSB import (
    extract_data_from_png,
)  # Import PNG functions

REG_PATH = r"SOFTWARE\f3832454-4e14-a1b9-0f614e507aa5"
AES_KEY_SIZE = 32  # 256 bits for AES-256
IV_SIZE = 16
THRESHOLD = 3  # Minimum number of shares required to recover the key
TOTAL_SHARES = 5  # Total number of shares
LIST_OF_FILES = ['sample2.png', 'sample.png']
FILENAME = "main.py"
image_extensions = ['.jpeg', '.jpg', '.png']


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


# Encrypt and hide data in PNG
def hide_mode(steg_technique, data):
    if not check_registry_for_key():
        key, iv = generate_secret_key()
        split_and_store_key(key, iv)
    key, iv = reconstruct_key()

    # TODO: Encrypt the data using AES (Andersen)
    # cipher = AES.new(key, AES.MODE_EAX)
    # ciphertext, tag = cipher.encrypt_and_digest(data.encode("utf-8"))
    # nonce = cipher.nonce

    #TODO: Split Data (Andersen)
    splitted_data = [1,2] # temp values for testing

    # Create a Path object for the folder
    path = Path("images") #TODO: let user choose which folder of files to use as hiding medium or default
    
    list_of_used_files = []


    if steg_technique.lower() == "lsb":
        # List comprehension to retrieve file names
        files = [file.name for file in path.iterdir() if file.is_file() and file.suffix in image_extensions]
        if len(files) != len(splitted_data):
            print(f"Not enough images to be used. Number of images needed is {len(splitted_data)}.")
            sys.exit(1)
        for data in splitted_data:
            random_index = random.randint(0, len(files) - 1)
            file = files.pop(random_index)
            list_of_used_files.append(file)
            # Hide the encrypted data in the image
            # hide_data_in_png(file, )
        
    elif steg_technique.lower() == "dct":
        #TODO: Eddie
        # List comprehension to retrieve file names
        files = [file.name for file in path.iterdir() if file.is_file() and file.suffix in image_extensions]
        if len(files) != len(splitted_data):
            print(f"Not enough images to be used. Number of images needed is {len(splitted_data)}.")
            sys.exit(1)
        for data in splitted_data:
            random_index = random.randint(0, len(files) - 1)
            file = files.pop(random_index)
            list_of_used_files.append(file)
            # Hide the encrypted data in the image
    
    elif steg_technique.lower() == "ads":
        #TODO: Eric
        # List comprehension to retrieve file names 
        files = [file.name for file in path.iterdir() if file.is_file()]
        if len(files) != len(splitted_data):
            print(f"Not enough files to be used. Number of files needed is {len(splitted_data)}.")
            sys.exit(1)
        for data in splitted_data:
            random_index = random.randint(0, len(files) - 1)
            file = files.pop(random_index)
            list_of_used_files.append(file)
            # Hide the encrypted data in the image

    else:
        #TODO: Mixed method
        pass

    hide_list(list_of_used_files)
    print("Data hidden successfully!")


def unhide_mode(image_path):
    # Retrieve the nonce, tag, and ciphertext length from the registry
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ
    ) as reg_key:
        nonce, _ = winreg.QueryValueEx(reg_key, "Nonce")
        tag, _ = winreg.QueryValueEx(reg_key, "Tag")
        ciphertext_length, _ = winreg.QueryValueEx(reg_key, "CiphertextLength")

    # Convert the retrieved values back into their original formats
    nonce = bytes.fromhex(nonce)
    tag = bytes.fromhex(tag)
    expected_ciphertext_length = int(ciphertext_length)

    # Extract the hidden data from the image
    extracted_data = extract_data_from_png(image_path, expected_ciphertext_length)

    print(
        f"Trying to decrypt: {extracted_data.hex()} with tag: {tag.hex()} and nonce: {nonce.hex()}"
    )

    # Retrieve the AES key from the registry
    key_parts_1, key_parts_2 = retrieve_key_from_registry()
    key = reconstruct_key(key_parts_1, key_parts_2)

    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)

    try:
        decrypted_data = cipher.decrypt_and_verify(extracted_data, tag)
        print(f"Decrypted data: {decrypted_data.decode('utf-8')}")
    except ValueError as e:
        print(f"Decryption failed: {e}")


# Main function
def main():
    print(f"Arguments passed: {sys.argv}")
    if len(sys.argv) < 3:
        print("Usage for hide mode: python main.py hide <steg_technique> <data>")
        print("Usage for unhide mode: python main.py unhide <file>")
        sys.exit(1)

    if sys.argv[1] == "hide":
        print("Entering hide mode")
        hide_mode(sys.argv[2],sys.argv[3])
    elif sys.argv[1] == "unhide":
        print("Entering unhide mode")
        unhide_mode(sys.argv[2])
    else:
        print("Invalid mode. Use 'hide' or 'unhide'.")


def hide_list(value):
    new_values_str = f"LIST_OF_FILES = {value}\n"
    # Read the current content of the file
    with open(FILENAME, "r") as file:
        lines = file.readlines()

    # Write back the lines, replacing the old LIST_OF_FILES definition
    with open(FILENAME, "w") as file:
        for line in lines:
            # Check if the line starts with LIST_OF_FILES
            if line.startswith("LIST_OF_FILES ="):
                file.write(new_values_str)  # Replace with the new value
            else:
                file.write(line)  # Keep the original line



if __name__ == "__main__":
    print("Calling main...")
    main()
