# FTE-Data-Hider
## Description

The FTE data hider is designed to be an anti-forensics tool by combining encryption, steganography techniques, and secure data erasure to hinder forensics recovery efforts. It uses encryption on the data as the first layer of protection, then employs various steganography techniques to hide data across multiple files and file types, making recovery of data harder. It incorporates a secure data erasure technique to prevent the original data from being recovered, thereby hindering the forensics recovery effort.

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/kennethwyq/FTE-Data-Hider.git
cd FTE-Data-Hider
```

### 2. Create a Virtual Environment
(Optional but recommended)

```bash
python3 -m venv venv
```

### 3. Activate the Virtual Environment

**Windows:**
```bash
.\venv\Scripts\activate
```

**macOS/Linux:**
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Hide Mode
To hide data using a specified steganography technique:

```bash
python main.py hide <steg_technique> <data> <number_of_files>
```

Parameters:
- `<steg_technique>`: The steganography technique to use (e.g., `lsb`, `dct`, etc.)
- `<data>`: The data to hide
- `<number_of_files>`: The number of files to use for hiding the data

Example:
```bash
python main.py hide ads sample.txt 2
```

### Unhide Mode
To extract hidden data:

```bash
python main.py unhide <technique>
```

Parameters:
- `<technique>`: The steganography technique used for hiding the data

Example:
```bash
python main.py unhide ads
```

