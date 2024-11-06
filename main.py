import sys
import winreg
import random
from pathlib import Path
from binascii import hexlify, unhexlify
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.SecretSharing import Shamir
import LSB.LSB as lsb
import ADS.ads as ads
import DCT.dctMain as dct
import DCT.dctZigZag as zigzag
import DCT.dct as dct
import DCT.dctEmbed_Extract as dctEncode
import DCT.dctDecode as dctDecode
import EOI.jpegeoi as eoi


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

# Encrypt and hide data in PNG
def hide_mode(steg_technique, path_of_data, number_of_files):
    if not check_registry_for_key():
        key, iv = generate_secret_key()
        split_and_store_key(key, iv)
    key, iv = reconstruct_key()

    number_of_files = int(number_of_files)
    with open(path_of_data, 'rb') as file:
        file_data = file.read()

    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(file_data)
    nonce = cipher.nonce

    path = Path("images") #TODO: let user choose which folder of files to use as hiding medium or default
    
    splitted_data = split_byte_data(ciphertext, number_of_files)


    if steg_technique.lower() == "lsb":
        # List comprehension to retrieve file names
        list_of_used_files = [file.name for file in path.iterdir() if file.is_file() and file.suffix in ['jpg']]
        list_of_used_files = list_of_used_files[:len(splitted_data)]
        if len(list_of_used_files) != len(splitted_data):
            print(f"Not enough images to be used. Number of images needed is {len(splitted_data)}.")
            sys.exit(1)
        for i in range(len(splitted_data)):
            data = splitted_data[i]
            file_path = str(path.absolute())+'\\'+ list_of_used_files[i]
            # Hide the encrypted data in the image
            # hide_data_in_jpg(file, )

        
    elif steg_technique.lower() == "dct":
        #TODO: Eddie
        # List comprehension to retrieve file names
        list_of_used_files = [file.name for file in path.iterdir() if file.is_file() and file.suffix in ['jpg']]
        list_of_used_files = list_of_used_files[:len(splitted_data)]
        if len(list_of_used_files) != len(splitted_data):
            print(f"Not enough images to be used. Number of images needed is {len(splitted_data)}.")
            sys.exit(1)
        for i in range(len(splitted_data)):
            data = splitted_data[i]
            file_path = str(path.absolute())+'\\'+ list_of_used_files[i]
            # Hide the encrypted data in the image
            # hide_data_in_png(file, )
            dct.embed_secret_message_into_image(file_path, data)

    
    elif steg_technique.lower() == "ads":
        #TODO: Eric
        # List comprehension to retrieve file names
        list_of_used_files = [file.name for file in path.iterdir() if file.is_file()]
        list_of_used_files = list_of_used_files[:len(splitted_data)]
        if len(list_of_used_files) != len(splitted_data):
            print(f"Not enough images to be used. Number of images needed is {len(splitted_data)}.")
            sys.exit(1)
        for i in range(len(splitted_data)):
            data = splitted_data[i]
            file_path = str(path.absolute())+'\\'+ list_of_used_files[i]
            # Hide the encrypted data in the image
            # ads.write_data(data,file_path,"s")

    elif steg_technique.lower() =="default":
        # Split the ciphertext into chunks of 32 bytes each
        split_point = (number_of_files + 1) // 2 
        half = len(ciphertext) // 2
        chunks_DCT = ciphertext[:half]
        chunks_ADS = ciphertext[half:]
        splitted_data_DCT = [chunks_DCT[i:i + 32] for i in range(0, len(chunks_DCT), 32)]
        splitted_data_ADS = [chunks_ADS[i:i + 32] for i in range(0, len(chunks_ADS), 32)]
        files_LSB = list_of_used_files[:split_point]
        if len(files_LSB) < len(splitted_data_DCT):
            print(f"Not enough images for LSB steganography. Needed: {len(splitted_data_DCT)}")
            sys.exit(1)
        for data_chunk in splitted_data_DCT:
            random_index = random.randint(0, len(files_LSB) - 1)
            file = files_LSB.pop(random_index)
            list_of_used_files.append(file)
            # Hide the encrypted data chunk in the image using LSB

        files_ADS = list_of_used_files[split_point:]
        if len(files_ADS) < len(splitted_data_ADS):
            print(f"Not enough files for ADS steganography. Needed: {len(splitted_data_ADS)}")
            sys.exit(1)
        for data_chunk in splitted_data_ADS:
            random_index = random.randint(0, len(files_ADS) - 1)
            file = files_ADS.pop(random_index)
            list_of_used_files.append(file)
            # Hide the encrypted data chunk in the file using ADS
        pass


    with open('order.txt', "w") as file:
        for i, files in enumerate(list_of_used_files):
            if i < len(list_of_used_files) - 1:
                file.write(files + ',')
            else:
                file.write(files)
        file.close()


    # wipe_file(path_of_data)
    # print(f"Data from {file_path} has been hidden and the original file securely wiped.")


def unhide_mode():
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
    if len(sys.argv) < 4:
        print("Usage for hide mode: python main.py hide <steg_technique> <data> <number of files>")
        print("Usage for unhide mode: python main.py unhide <files>")
        sys.exit(1)

    if sys.argv[1] == "hide":
        print("Entering hide mode")
        hide_mode(sys.argv[2],sys.argv[3], sys.argv[4])
    elif sys.argv[1] == "unhide":
        print("Entering unhide mode")
        unhide_mode(sys.argv[2])
    else:
        print("Invalid mode. Use 'hide' or 'unhide'.")



if __name__ == "__main__":
    print("Calling main...")
    main()
