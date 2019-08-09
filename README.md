# PDF To JSON Data Extracting using OCR

## Getting Started

### Setup
```
$ git clone https://github.com/xploiter-projects/PDF2JSON.git
$ cd PDF2JSON
$ pip install -r requirements.txt
```

### Convert PDF to JSON
```
usage: pdf2json.py [-h] -p PDF_FILES_DIR [-d]

optional arguments:
  -h, --help        show this help message and exit
  -p PDF_FILES_DIR  enter the path directory containing pdf files
  -d, --debug       turn on the debug mode

```
Example: ```python pdf2json.py -p tests```

#### Directory Structure
    .
    ├── tests                   # this directory contains pdf files 
    |   ├── file1.pdf
    |   ├── file2.pdf
    |   ├── file3.pdf
    |   └── ...                 # etc

### Visualize
```
usage: visualize.py [-h] -p PDF_FILES_DIR

optional arguments:
  -h, --help        show this help message and exit
  -p PDF_FILES_DIR  enter the directory path containing pdf and json files

```
Example: ```python visualize.py -p tests```

#### Directory Structure for Visualize
    .
    ├── tests                   # this directory contains pdf files 
    |   ├── tessblocks          # directory contains JSON files generated from above script 
    |   |   ├── file1.json
    |   |   ├── file2.json
    |   |   ...                 # etc
    |   ├── blocks              # directory contains JSON files that needs to be compared
    |   |   ├── file1.json
    |   |   ├── file2.json
    |   |   ...                 # etc
    |   ├── file1.pdf
    |   ├── file2.pdf
    |   └── ...                 # etc
