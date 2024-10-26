# Libraries
import cv2
import numpy as np

# Numpy Macros
HORIZONTAL_AXIS = 1  # Constant for horizontal axis
VERTICAL_AXIS  = 0  # Constant for vertical axis

# Standard quantization table as defined by JPEG
JPEG_STD_LUM_QUANT_TABLE = np.asarray([
                                        [16, 11, 10, 16,  24, 40,   51,  61],
                                        [12, 12, 14, 19,  26, 58,   60,  55],
                                        [14, 13, 16, 24,  40, 57,   69,  56],
                                        [14, 17, 22, 29,  51, 87,   80,  62],
                                        [18, 22, 37, 56,  68, 109, 103,  77],
                                        [24, 36, 55, 64,  81, 104, 113,  92],
                                        [49, 64, 78, 87, 103, 121, 120, 101],
                                        [72, 92, 95, 98, 112, 100, 103,  99]
                                      ],
                                      dtype = np.float32)  # Define the JPEG standard luminance quantization table

# Image container class
class YCC_Image(object):
    def __init__(self, cover_image):
        self.height, self.width = cover_image.shape[:2]  # Get the dimensions of the image
        self.channels = [
                         split_image_into_8x8_blocks(cover_image[:,:,0]),  # Split Y channel into 8x8 blocks
                         split_image_into_8x8_blocks(cover_image[:,:,1]),  # Split Cb channel into 8x8 blocks
                         split_image_into_8x8_blocks(cover_image[:,:,2]),  # Split Cr channel into 8x8 blocks
                        ]

# Function to stitch 8x8 blocks back together
# param NP: Number of pixels in the image (length-wise)
# param block_segments: List of 8x8 blocks
def stitch_8x8_blocks_back_together(NP, block_segments):

    image_rows = []  # List to hold rows of blocks
    temp = []  # Temporary list to hold a row of blocks

    for i in range(len(block_segments)):
        if i > 0 and not(i % int(NP / 8)):  # Check if the current block is the start of a new row
            image_rows.append(temp)  # Add the completed row to image_rows
            temp = [block_segments[i]]  # Start a new row with the current block
        else:
            temp.append(block_segments[i])  # Add the current block to the current row

    image_rows.append(temp)  # Add the last row to image_rows
    return np.block(image_rows)  # Combine all rows into a single image

# Function to split an image into 8x8 blocks
def split_image_into_8x8_blocks(image):

    blocks = []  # List to hold 8x8 blocks

    for vert_slice in np.vsplit(image, int(image.shape[0] / 8)):  # Split image vertically into 8-pixel high slices
        for horiz_slice in np.hsplit(vert_slice, int(image.shape[1] / 8)):  # Split each vertical slice into 8-pixel wide slices
            blocks.append(horiz_slice)  # Add the 8x8 block to the list

    return blocks  # Return the list of 8x8 blocks
