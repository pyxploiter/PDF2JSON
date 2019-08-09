import argparse
import json
from glob import glob
import os

import cv2
import pdf2image
import pytesseract
import numpy as np
from unidecode import unidecode
from PIL import Image


def getDataForJson(df_ocr, page_image, page_num, output_data):
    # grouping blocks of text using ocr data
    block_group = df_ocr.groupby(["block_num"])

    blk_no = 0
    for block_no, block in block_group:
        if block["level"].size > 1:
            par_group = block.groupby(["par_num"])

            for par_no, par in par_group:
                if par["level"].size > 1:
                    blk_no += 1
                    block_dict = {}
                    topL = {}
                    bottomR = {}

                    for _, par_row in par.iterrows():
                        if par_row["level"] == 3:
                            topL["topleft"] = { "x": par_row["left"], "y": par_row["top"],}
                            bottomR["bottomright"] = { "x": par_row["left"] + par_row["width"], "y": par_row["top"] + par_row["height"],}

                            if args.debug:
                                # draw block bounding boxes in green color
                                cv2.rectangle(page_image, (topL["topleft"]["x"], topL["topleft"]["y"]),(bottomR["bottomright"]["x"], bottomR["bottomright"]["y"]), (0, 255, 0), 2)
                    
                    # add top_left block point
                    block_dict.update(topL)

                    line_group = par.groupby(["line_num"])
                    block_dict["textlines"] = []
                    flag = False
                    for line_no, line in line_group:
                        # check if line isn't NaN
                        if len(line["text"].str.cat()) > 0:
                            line_dict = {}
                            text = ""
                            for _, line_row in line.iterrows():
                                # at level = 4, rows contain bounding boxes on line level
                                if line_row["level"] == 4:
                                    line_dict["topleft"] = { "x": line_row["left"], "y": line_row["top"], }
                                    line_dict["bottomright"] = { "x": line_row["left"] + line_row["width"], "y": line_row["top"] + line_row["height"],}

                                    if args.debug:
                                        # draw line bounding boxes in red color
                                        cv2.rectangle( page_image, (line_dict["topleft"]["x"], line_dict["topleft"]["y"]), (line_dict["bottomright"]["x"], line_dict["bottomright"]["y"]), (200, 100, 0), 1)
                                # select the non-empty words having confidence > 10%
                                if ( line_row["conf"] > -1
                                    and not str(line_row["text"]).isspace()
                                    and line_row["level"] == 5 ):
                                    # concatenate the words text into one line
                                    text += " " + str(line_row["text"])

                            # replace unicode characters from text to nearly ascii characters
                            line_dict["text"] = unidecode(text[1:])
                            block_dict["textlines"].append(line_dict)
                            flag = True if len(line_dict["text"])>0 else False

                    block_dict["id"] = "P" + str(page_no) + "B" + str(blk_no)
                    block_dict["page"] = page_num + 1
                    block_dict.update(bottomR)
                    block_dict["font"] = ""

                    if flag:
                        output_data["blocks"].append(block_dict)
                        # if block has no text lines (empty block)
                    else:
                        blk_no -= 1
                        # output_data["blocks"].append(block_dict)
    return output_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-p",
        dest="pdf_files_dir",
        help="enter the path directory containing pdf files",
        required=True,
    )

    parser.add_argument(
        "-d", "--debug", help="turn on the debug mode", action="store_true"
    )

    args = parser.parse_args()
    print(args)

    # creating blocks directory to store json files
    block_dir = os.path.join(args.pdf_files_dir, "tesseractJSON")
    if not os.path.exists(block_dir):
        os.mkdir(block_dir)

    pdf_files = glob(os.path.join(args.pdf_files_dir, "*.pdf"))

    for file in pdf_files:
        print("File Path:", file)
        pdf_file_name = file.split("/")[-1][:-4]

        if not os.path.isfile(os.path.join(block_dir, pdf_file_name + ".json")):
	        # convert pdf file to images
	        pages = pdf2image.convert_from_path(file)
	        data = {}
	        data["blocks"] = []

	        # loop through every page image
	        for page_no, page in enumerate(pages):
	            print("Page No: " + str(page_no + 1) + "/" + str(len(pages)))
	            img = np.array(page)

	            try:
	                # extracting ocra data from image
	                ocr_data = pytesseract.image_to_data(
	                    img, output_type=pytesseract.Output.DATAFRAME
	                )
	            except:
	                print("OCR Failed.")
	                continue

	            # get the data dictionary for json file
	            data = getDataForJson(ocr_data, img, page_no, data)

	            # save output images with bounding boxes
	            if args.debug:
	                debug_dir = os.path.join(args.pdf_files_dir, "debug")
	                # creating debug directory
	                if not os.path.exists(debug_dir):
	                    os.mkdir(debug_dir)
	                # creating directory for each pdf file
	                imgs_dir = os.path.join(debug_dir, pdf_file_name)
	                if not os.path.exists(imgs_dir):
	                    os.mkdir(imgs_dir)
	                img_path = os.path.join(
	                    imgs_dir, pdf_file_name + "_Page" + str(page_no + 1) + ".png"
	                )
	                cv2.imwrite(img_path, img)

	        # writing python dictionary to json file
	        with open(os.path.join(block_dir, pdf_file_name + ".json"), "w") as f:
	            json.dump(data, f)
