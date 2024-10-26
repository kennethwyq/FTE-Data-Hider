#Libraries
import bitstring
import numpy as np

def embed_encoded_data_dct(encoded_bits, dct_blocks):
    data_complete = False
    encoded_bits.bitpos = 0  # Use bitpos instead of pos
    encoded_data_length = bitstring.pack('uint:32', len(encoded_bits))

    print(f"Encoded data length (bits): {len(encoded_bits)}")
    print(f"Encoded data length (packed): {encoded_data_length.bin}")

    converted_blocks = []

    for current_dct_block in dct_blocks:
        for i in range(1, len(current_dct_block)):
            current_coefficient = np.int32(current_dct_block[i])
            if current_coefficient > 1:
                current_coefficient = np.uint8(current_dct_block[i])
                if encoded_bits.bitpos == (len(encoded_bits) - 1):
                    data_complete = True
                    break
                pack_coefficient = bitstring.pack('uint:8', current_coefficient)

                # Embedding the length first
                if encoded_data_length.bitpos <= len(encoded_data_length) - 1:
                    bit = encoded_data_length.read(1)
                    pack_coefficient[-1] = bit  # Embed the length bit
                else:
                    bit = encoded_bits.read(1)
                    pack_coefficient[-1] = bit  # Embed the data bit

                # Debugging print
                print(f"Embedding bit: {bit}")

                # Replace converted coefficient
                current_dct_block[i] = np.float32(pack_coefficient.read('uint:8'))

        converted_blocks.append(current_dct_block)

    if not data_complete:
        raise ValueError("Data didn't fully embed into cover image!")
    return converted_blocks


def extract_encoded_data_dct(dct_blocks):
    extracted_data = bitstring.BitArray()
    for current_dct_block in dct_blocks:
        for i in range(1, len(current_dct_block)):
            current_coefficient = np.int32(current_dct_block[i])
            if current_coefficient > 1:
                bit = np.uint8(current_dct_block[i]) & 0x01  # Extract the LSB
                extracted_data.append('0b' + str(bit))
                # Debugging print
                print(f"Extracted bit: {bit}")
    return extracted_data



