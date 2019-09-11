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
usage: pdf2json.py [-h] -i PDF_FILE [-c CONFIG_FILE] [-s] [-d] [--dev]

optional arguments:
  -h, --help         show this help message and exit
  -i PDF_FILE        enter the path to pdf file
  -c CONFIG_FILE     enter the path to config file
  -s, --save_images  save images of pdf file
  -d, --debug        turn on the debug mode
  --dev              turn on the developer mode

```

Following parameters are loaded from ```config.yaml``` and may be edited there:

    -output_json_dir:	Output directory for JSON files extracted from PDF files.
    -pdf_images_dir:	Output directory for images extracted from PDF files.
    -debug_images_dir:	Output directory for debug images. 
    -language:		Language to be used for applying tesseract
    -tessdata:		Directory containing the traineddata files for tesseract

### Run for a pdf file

```example: python pdf2json.py -i tests/example1.pdf```

### Run the python script for a batch of pdf files

```
usage: ./run_batch.sh PATH/TO/FOLDER [-c CONFIG_FILE] [-s] [-d] [--dev]
```
```
example: ./run_batch.sh ./tests/ -s -d
```

