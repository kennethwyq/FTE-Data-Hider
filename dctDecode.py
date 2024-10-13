#Libraries
import cv2
import struct
import bitstring
import numpy as np

#Files
import dctZigZag as zigzag
import encode as encode
import dctMain as main
import dct as dct

stego_image     = cv2.imread(main.STEGO_IMAGE_FILEPATH, flags=cv2.IMREAD_COLOR)
stego_image_f32 = np.float32(stego_image)
stego_image_YCC = dct.YCC_Image(cv2.cvtColor(stego_image_f32, cv2.COLOR_BGR2YCrCb))

# FORWARD DCT STAGE
dct_blocks = [cv2.dct(block) for block in stego_image_YCC.channels[0]]  # Only care about Luminance layer

# QUANTIZATION STAGE
dct_quants = [np.around(np.divide(item, dct.JPEG_STD_LUM_QUANT_TABLE)) for item in dct_blocks]

# Sort DCT coefficients by frequency
sorted_coefficients = [zigzag.zigzag(block) for block in dct_quants]

# DATA EXTRACTION STAGE
recovered_data = encode.extract_encoded_data_dct(sorted_coefficients)
recovered_data.pos = 0

# Determine length of secret message
data_len = int(recovered_data.read('uint:32') / 8)

# Extract secret message from DCT coefficients
extracted_data = bytes()
for _ in range(data_len): extracted_data += struct.pack('>B', recovered_data.read('uint:8'))

# Print secret message back to the user
print(extracted_data.decode('ascii'))