# PDF To JSON Data Extracting using OCR

## Getting Started

### Setup
```
$ git clone https://github.com/xploiter-projects/PDF2JSON.git
$ cd PDF2JSON
$ pip install -r requirements.txt
```

### Usage
```
usage: pdf2json.py [-h] -i PDF_FILE [-s] [-d]

optional arguments:
  -h, --help         show this help message and exit
  -i PDF_FILE        enter the path to pdf file
  -s, --save_images  save images of pdf file
  -d, --debug        turn on the debug mode

```

### Run for a pdf file

```example: python pdf2json.py -i tests/example1.pdf```

### Run for a folder containing pdf files

```
usage: ./run_for_folder.sh PATH/TO/FOLDER [-s] [-d]
```
```
example: ./run_for_folder.sh tests -s -d
```
