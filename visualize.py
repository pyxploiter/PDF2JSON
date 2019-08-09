import argparse
import json
from glob import glob
import os
import sys

import numpy as np
import cv2
import pdf2image


def drawRects(jsonFile, images, ocr=False):
    # loading json file into python dictionary
    with open(jsonFile, "r") as f:
        data = json.load(f)

    # rescaling factors
    scale = 0.36 if not ocr else 1
    tconst = 6 if not ocr else 0
    color = (0, 255, 0) if not ocr else (0, 0, 255)

    # drawing rescaled bounding boxes
    for rect in data["blocks"]:
        x1 = int(rect["topleft"]["x"] / scale)
        y1 = int(rect["topleft"]["y"] / scale) - tconst
        x2 = int(rect["bottomright"]["x"] / scale)
        y2 = int(rect["bottomright"]["y"] / scale) + tconst
        cv2.rectangle(images[rect["page"] - 1], (x1, y1), (x2, y2), color, 2)

    # save images
    for page_no, img in enumerate(images):
        cv2.imwrite(
            os.path.join(image_dir, file_name + "_Page_" + str(page_no) + ".png"), img
        )

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p",
        dest="pdf_files_dir",
        help="enter the directory path containing pdf and json files",
        required=True,
    )

    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()
    print(args)

    # directory listings
    pdf_files = glob(os.path.join(args.pdf_files_dir, "*.pdf"))
    
    json_blocks_path = os.path.join(args.pdf_files_dir, "blocks")
    json_blocks_files = glob(os.path.join(json_blocks_path, "*.json"))

    json_tessblocks_path = os.path.join(args.pdf_files_dir, "tesseractJSON")
    json_tessblocks_files = glob(os.path.join(json_tessblocks_path, "*.json"))

    image_path = os.path.join(args.pdf_files_dir, "blockImages")
    if not os.path.exists(image_path):
        os.mkdir(image_path)

    # process each pdf file
    for tessblock in json_tessblocks_files:
        # extracting file name from json file path
        file_name = tessblock.split("/")[-1][:-5]
        # pdf file path
        pdf_path = os.path.join(args.pdf_files_dir, file_name+".pdf")
        print("Processing File: ", pdf_path)
        
        # convert pdf file to images
        pages = pdf2image.convert_from_path(pdf_path)
        # convert PIL images to numpy arrays
        pages = list(map(np.array, pages))

        image_dir = os.path.join(image_path, file_name)
        
        if not os.path.exists(image_dir):
        	os.mkdir(image_dir)

        # get json file name
        json_block_file = os.path.join(json_blocks_path, file_name + ".json")

        if (os.path.isfile(json_block_file)):
            drawRects(json_block_file, pages, ocr=False)
            drawRects(tessblock, pages, ocr=True)
        else:
            print("File not found: ", json_block_file)
