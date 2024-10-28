import subprocess


# Write data into the alternate data stream
def write_data(data, file, stream_name):
    command_write = f'echo {data} > "{file}:{stream_name}"'
    subprocess.run(command_write, shell=True)
    print(f"Data written to {file}:{stream_name}")


# Read data from alternate data steam
def read_data(file, stream_name):
    command_read = f'more < "{file}:{stream_name}"'
    result = subprocess.run(command_read, shell=True, capture_output=True, text=True)
    if result.stdout:
        print("Data retrieved from ADS:", result.stdout)
    else:
        print("Error or no data:", result.stderr)


# file_path = 'gnar.jpg'
# stream_name = '1'
# hex_data = b'48656c6c6f'
# write_data(hex_data, file_path, stream_name)
# read_data(file_path, stream_name)
