#Libraries
import bitstring
import numpy as np

def extract_encoded_data_dct(dct_blocks):
    extracted_data = ""
    for current_dct_block in dct_blocks:
        for i in range(1, len(current_dct_block)):
            current_coefficient = np.int32(current_dct_block[i])
            if current_coefficient > 1:
                extracted_data += bitstring.pack('uint:1', np.uint8(current_dct_block[i]) & 0x01)
    return extracted_data

def embed_encoded_data_dct(encoded_bits, dct_blocks):
    data_complete = False; encoded_bits.pos = 0
    encoded_data_length = bitstring.pack('uint:32', len(encoded_bits))
    converted_blocks = []
    for current_dct_block in dct_blocks:
        for i in range(1, len(current_dct_block)):
            current_coefficient = np.int32(current_dct_block[i])
            if current_coefficient > 1:
                current_coefficient = np.uint8(current_dct_block[i])
                if encoded_bits.pos == (len(encoded_bits) - 1):
                    data_complete = True;
                    break

                pack_coefficient = bitstring.pack('uint:8', current_coefficient)

                if encoded_data_length.pos <= len(encoded_data_length) - 1:
                    pack_coefficient[-1] = encoded_data_length.read(1)
                else:
                    pack_coefficient[-1] = encoded_bits.read(1)

                # Replace converted coefficient
                current_dct_block[i] = np.float32(pack_coefficient.read('uint:8'))
        converted_blocks.append(current_dct_block)

    if not data_complete:
        raise ValueError("Data didn't fully embed into cover image!")

    return converted_blocks