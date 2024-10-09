import sys
import winreg
from binascii import hexlify, unhexlify
from Cryptodome.Cipher import AES
from Cryptodome.Random import get_random_bytes
from Cryptodome.Protocol.SecretSharing import Shamir
from Steganography import hide_data_in_png, extract_data_from_png  # Import PNG functions

REG_PATH = r"SOFTWARE\f3832454-4e14-a1b9-0f614e507aa5"
AES_KEY_SIZE = 32  # 256 bits for AES-256
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
    winreg.SetValueEx(key, "InstallLocation", 0, winreg.REG_SZ, r"C:\Program Files\Fake Software")
    winreg.CloseKey(key)

def clean_up_registry():
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, REG_PATH)

# Function to generate a new AES key and split it into parts using SSS
def generate_secret_key():
    key = get_random_bytes(AES_KEY_SIZE)
    print(f"Generated AES Key: {key.hex()}")
    return key

def split_and_store_key(key):
    key_parts_1 = Shamir.split(THRESHOLD, TOTAL_SHARES, key[:16])
    key_parts_2 = Shamir.split(THRESHOLD, TOTAL_SHARES, key[16:])
    
    # Create fake registry key (anti-forensics)
    create_fake_registry_key()

    # Store real encryption-related values in the registry
    for idx, part in key_parts_1:
        reg_name = f"Cache{idx}"
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as reg_key:
            winreg.SetValueEx(reg_key, reg_name, 0, winreg.REG_SZ, hexlify(part).decode())
    for idx, part in key_parts_2:
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
    if len(key_parts_1) >= THRESHOLD and len(key_parts_2) >= THRESHOLD:
        key_part_1 = Shamir.combine(key_parts_1)
        key_part_2 = Shamir.combine(key_parts_2)
        return key_part_1 + key_part_2
    else:
        print("Number of shares is less than the required threshold.")
        sys.exit(1)

# Encrypt and hide data in PNG
def hide_mode(data, image_path):
    key = generate_secret_key()

    # Encrypt the data using AES
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data.encode('utf-8'))
    nonce = cipher.nonce

    print(f"Ciphertext: {ciphertext.hex()}")
    print(f"Tag: {tag.hex()}")
    print(f"Nonce: {nonce.hex()}")

    # Hide the encrypted data in the image
    hide_data_in_png(image_path, ciphertext)

    # Store the nonce, tag, and ciphertext length in the registry
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH) as reg_key:
        winreg.SetValueEx(reg_key, "Nonce", 0, winreg.REG_SZ, nonce.hex())
        winreg.SetValueEx(reg_key, "Tag", 0, winreg.REG_SZ, tag.hex())
        winreg.SetValueEx(reg_key, "CiphertextLength", 0, winreg.REG_SZ, str(len(ciphertext)))

    # Store the encryption key in the registry
    split_and_store_key(key)

    print("Data hidden successfully!")

def unhide_mode(image_path):
    # Retrieve the nonce, tag, and ciphertext length from the registry
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_READ) as reg_key:
        nonce, _ = winreg.QueryValueEx(reg_key, "Nonce")
        tag, _ = winreg.QueryValueEx(reg_key, "Tag")
        ciphertext_length, _ = winreg.QueryValueEx(reg_key, "CiphertextLength")

    # Convert the retrieved values back into their original formats
    nonce = bytes.fromhex(nonce)
    tag = bytes.fromhex(tag)
    expected_ciphertext_length = int(ciphertext_length)

    # Extract the hidden data from the image
    extracted_data = extract_data_from_png(image_path, expected_ciphertext_length)

    print(f"Trying to decrypt: {extracted_data.hex()} with tag: {tag.hex()} and nonce: {nonce.hex()}")

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
print("Starting the script...")

def main():
    print(f"Arguments passed: {sys.argv}")
    if len(sys.argv) < 3:
        print("Usage for hide mode: python main.py hide <data> <file>")
        print("Usage for unhide mode: python main.py unhide <file>")
        sys.exit(1)

    if sys.argv[1] == 'hide':
        print("Entering hide mode")
        hide_mode(sys.argv[2], sys.argv[3])
    elif sys.argv[1] == 'unhide':
        print("Entering unhide mode")
        unhide_mode(sys.argv[2])
    else:
        print("Invalid mode. Use 'hide' or 'unhide'.")

if __name__ == "__main__":
    print("Calling main...")
    main()
