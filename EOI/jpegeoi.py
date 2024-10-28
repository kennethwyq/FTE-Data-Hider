# Function to read jpeg
def read_jpeg(jpeg_file):
    with open(jpeg_file, 'rb') as jpg:
        jpeg_bytes = jpg.read()

    return jpeg_bytes


# Function to find End of Line marker
def eol_jpeg(jpeg_bytes_array):
    for i in range(0, len(jpeg_bytes_array)):
        # EOL MARKER 0xFFD9
        if jpeg_bytes_array[i] == 255 and jpeg_bytes_array[i + 1] == 217:
            position = i + 1
            return position


# Function to insert bytes
def insert(jpeg_bytes_array, position, data):
    data_bytes = bytes.fromhex(data)
    jpeg_bytes_array = bytearray(jpeg_bytes_array)
    # insert position is after the last byte therefore need to + 1
    jpeg_bytes_array[position + 1:position + 1] = data_bytes
    jpeg_bytes_array = bytes(jpeg_bytes_array)
    return jpeg_bytes_array


# Function to overwrite the original jpeg file
def overwrite(data, jpeg_file):
    with open(jpeg_file, 'wb') as jpg:
        jpg.write(data)


# Function to retrieve bytes
def retrieve(position, jpeg_file):
    with open(jpeg_file, 'rb') as jpg:
        jpeg_bytes = jpg.read()

    # + 1 so D9 is not included
    data = jpeg_bytes[position+1:-3]
    return data


# file = read_jpeg("gnar.jpg")
# place = eol_jpeg(file)
# hex_values = '8b8786e7c8' + ffd9
# modified = insert(file, place, hex_values)
# overwrite(modified, "gnar.jpg")
# print(retrieve(place, "gnar.jpg"))

# To meet forensic worst, another indicator of EOL 0xFF 0xD9 can be inserted
# at the end together with the data.
