import sys
import winreg
from binascii import hexlify, unhexlify
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.SecretSharing import Shamir

REG_PATH = r"SOFTWARE\f3832454-4b20-4e14-a1b9-0f614e507aa5"
AES_KEY_SIZE = 32  # 256 bits for AES-256
THRESHOLD = 3  # Minimum number of shares required to recover the key
TOTAL_SHARES = 5  # Total number of shares


def create_fake_registry_key():
    key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
    
    # Define fake values for the key
    winreg.SetValueEx(key, "DisplayName", 0, winreg.REG_SZ, "Fake Software")
    winreg.SetValueEx(key, "DisplayVersion", 0, winreg.REG_SZ, "1.0.0")
    winreg.SetValueEx(key, "Publisher", 0, winreg.REG_SZ, "Fake Publisher Inc.")
    winreg.SetValueEx(key, "InstallDate", 0, winreg.REG_SZ, "20240925")
    winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, r"C:\Program Files\Fake Software")

    winreg.CloseKey(key)

# Function to generate a new AES key and split it into parts using SSS
def generate_secret_key():
    key = get_random_bytes(AES_KEY_SIZE)
    print(key)
    return key

def split_and_store_key(key):
    key_parts_1 = Shamir.split(THRESHOLD, TOTAL_SHARES, key[:16])
    key_parts_2 = Shamir.split(THRESHOLD, TOTAL_SHARES, key[16:])
    create_fake_registry_key()
    for idx, part in key_parts_1:
        print(idx, part)
        reg_name = f"Cache{idx}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as reg_key:
            winreg.SetValueEx(reg_key, reg_name, 0, winreg.REG_SZ, hexlify(part).decode())
    for idx, part in key_parts_2:
        print(idx, part)
        reg_name = f"Config{idx}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as reg_key:
            winreg.SetValueEx(reg_key, reg_name, 0, winreg.REG_SZ, hexlify(part).decode())

def retrieve_key_from_registry():
    key_parts_1 = []
    key_parts_2 = []
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as reg_key:
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
    return key_parts_1, key_parts_2

def reconstruct_key(key_parts_1, key_parts_2):
    if len(key_parts_1)>=THRESHOLD and len(key_parts_2)>=THRESHOLD:
        key_parts_1 = Shamir.combine(key_parts_1)
        key_parts_2 = Shamir.combine(key_parts_2)
        return key_parts_1 + key_parts_2
    else:
        print("Something has gone wrong! Number of shares is less than the required threshold.")
        sys.exit(1)

def clean_up_registry():
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_PATH)

def hide_mode(data, files_to_use):
    key = generate_secret_key()
    split_and_store_key(key)
    key_parts_1, key_parts_2 = retrieve_key_from_registry()
    for idx, part in key_parts_1:
        print(idx, part)
    for idx, part in key_parts_2:
        print(idx, part)
    print(reconstruct_key(key_parts_1,key_parts_2))
    # clean_up_registry()

def unhide_mode(data, files_to_use):
    pass

def main():
    hide_mode()
   
if __name__ == "__main__":
    main()
