"""PDF2JSON: A script that extracts the blocks of text from PDF files["""
import argparse
import json
from glob import glob
import os
import sys

import cv2
import pdf2image
import pytesseract
import numpy as np
from PIL import Image
import yaml

COLOR = {"ERROR": "\033[1;31m", "WARNING": "\033[1;35m", "RESET": '\033[0m'}

def print_warning(message):
    print(COLOR["WARNING"] + "Warning: " + message + COLOR["RESET"], file=sys.stderr)

def print_error(message):
    print(COLOR["ERROR"] + "Error: " + message + COLOR["RESET"], file=sys.stderr)
    exit(0)

def get_config(configFilePath):
    """read the yaml file which contains configuration for script
    
    Keyword arguments:
    configFilePath  -- path to configuration yaml file

    Returns:
    configs     -- dictionary containing the configurations from config file  

    """
    configs = None
    with open(configFilePath, "r") as stream:
        try:
            configs = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return configs


def create_dirs(imageDir, fileName):
    """ensures the creation of directories before using or accessing them
    
    Keyword arguments:
    imageDir   -- path to directory where images of pdf files are to be stored
    fileName   -- pdf file name

    Returns:
    imgs_dir   -- path to output directory of pdf file

    """

    pdf_file_name = fileName
    # creating debug directory
    if not os.path.exists(imageDir):
        os.mkdir(imageDir)
    # creating directory for each pdf file
    imgs_dir = os.path.join(imageDir, pdf_file_name)
    if not os.path.exists(imgs_dir):
        os.mkdir(imgs_dir)

    return imgs_dir

def extract_blocks(df_ocr, page_image, page_num, output_data):
    """the main function that extracts the text blocks from the image

    Keyword arguments:
    df_ocr      -- dataframe extracted after apply OCR on image 
    page_image  -- image whose text blocks are being extracted
    page_num    -- page number of pdf file
    output_data -- dictionary where the blocks are stored, it contains data 
                   of previous images of same file

    Returns:
    output_data -- dictionary that contains text blocks of given image

    """
    
    # grouping blocks of text using ocr data
    block_group = df_ocr.groupby(["block_num"])
    # block number counter
    blk_no = 0
    for _, block in block_group:
        if block["level"].size > 1:
            # grouping paragraphs by paragraph number
            par_group = block.groupby(["par_num"])

            for _, par in par_group:
                if par["level"].size > 1:
                    blk_no += 1
                    block_dict = {}
                    topL = {}
                    bottomR = {}
                    # iterate through paragraphs
                    for _, par_row in par.iterrows():
                        # level 3 contains bounding boxes of paragraphs
                        if par_row["level"] == 3:
                            topL["topleft"] = {
                                "x": par_row["left"],
                                "y": par_row["top"],
                            }
                            bottomR["bottomright"] = {
                                "x": par_row["left"] + par_row["width"],
                                "y": par_row["top"] + par_row["height"],
                            }

                            if args.debug:
                                # draw block bounding boxes in green color
                                cv2.rectangle(
                                    page_image,
                                    (topL["topleft"]["x"], topL["topleft"]["y"]),
                                    (
                                        bottomR["bottomright"]["x"],
                                        bottomR["bottomright"]["y"],
                                    ),
                                    (0, 0, 255),
                                    2,
                                )

                    # add top_left block point
                    block_dict.update(topL)
                    # grouping the lines by line numbers
                    line_group = par.groupby(["line_num"])
                    block_dict["textlines"] = []
                    # flag to check if block is empty
                    flag = False
                    for _, line in line_group:
                        # check if line isn't NaN
                        if len(line["text"].str.cat()) > 0:
                            line_dict = {}
                            text = ""
                            line_topL = {}
                            line_bottomR = {}
                            for _, line_row in line.iterrows():
                                # at level = 4, rows contain bounding boxes on line level
                                if line_row["level"] == 4:
                                    line_topL = {
                                        "x": line_row["left"],
                                        "y": line_row["top"],
                                    }
                                    line_bottomR = {
                                        "x": line_row["left"] + line_row["width"],
                                        "y": line_row["top"] + line_row["height"],
                                    }

                                # select the non-empty words
                                if (
                                    line_row["conf"] > -1
                                    and not str(line_row["text"]).isspace()
                                    and line_row["level"] == 5
                                ):
                                    # concatenate the words text into one line
                                    text += " " + str(line_row["text"])

                            # replace unicode characters from text to nearly ascii characters
                            line_dict["topleft"] = line_topL
                            line_dict["text"] = text[1:]
                            line_dict["bottomright"] = line_bottomR
                            block_dict["textlines"].append(line_dict)
                            flag = True if len(line_dict["text"]) > 0 else False

                    block_dict["id"] = "P" + str(page_no) + "B" + str(blk_no)
                    block_dict["page"] = page_num + 1
                    block_dict.update(bottomR)
                    block_dict["font"] = ""
                    block_dict["image"] = pdf_file_name + "_Page" + str(page_num + 1) + ".png"
                    # add block only if it is not empty
                    if flag:
                        output_data["blocks"].append(block_dict)
                    else:
                        blk_no -= 1
    return output_data


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i", dest="pdf_file", help="enter the path to pdf file", required=True
    )

    parser.add_argument(
        "-c", dest="config_file", help="enter the path to config file", default="config.yaml"
    )

    parser.add_argument(
        "-s", "--save_images", help="save images of pdf file", action="store_true"
    )

    parser.add_argument(
        "-d", "--debug", help="turn on the debug mode", action="store_true"
    )

    parser.add_argument(
        "--dev", help="turn on the developer mode", action="store_true"
    )

    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(1)

    args = parser.parse_args()

    configs = get_config(args.config_file)

    file = args.pdf_file
    
    pdf_file_name = file.split("/")[-1][:-4]

    if args.save_images:
        pdf_img_dir = create_dirs(
            imageDir=configs["pdf_images_dir"], fileName=pdf_file_name
        )

    if args.debug:
        debug_img_dir = create_dirs(
            imageDir=configs["debug_images_dir"], fileName=pdf_file_name
        )

    if args.dev:
        # check if given tessdata directory does not exist
        if not os.path.exists(configs["tessdata"]):
            print_warning(configs["tessdata"] + " directory not found.")
            # check if local tessdata directory does not exist
            if not os.path.exists('tessdata'):
                os.mkdir("tessdata")
            print("Setting the TESSDATA_PREFIX = ./tessdata/ \n")
            configs["tessdata"] = "./tessdata"
            
        # download tesseract traineddata file for language if it doesn't exist
        if not os.path.isfile(
            os.path.join(
                configs["tessdata"], configs["language"] + ".traineddata"
            )
        ):
            print_warning(
                configs["language"]
                + ".traineddata not found in "
                + configs["tessdata"]
            )
            print(
                "Downloading "
                + configs["language"] + ".traineddata "
                + "file"
            )
            url = (
                "https://github.com/tesseract-ocr/tessdata_best/raw/master/"
                + configs["language"]
                + ".traineddata"
            )
            cmd = (
                "wget -O"
                + os.path.join(
                    os.environ["TESSDATA_PREFIX"], configs["language"] + ".traineddata"
                )
                + " "
                + url
            )
            os.system(cmd)

    else:
        if not os.path.exists(configs["tessdata"]):
            print_error(configs["tessdata"] + " directory not found.")

        elif not os.path.isfile(
            os.path.join(
                configs["tessdata"], configs["language"] + ".traineddata"
            )
        ):
            print_error(
                configs["language"]
                + ".traineddata not found in "
                + configs["tessdata"]
            )

    os.environ["TESSDATA_PREFIX"] = configs["tessdata"]

    # creating blocks directory to store json files
    if not os.path.exists(configs["output_json_dir"]):
        os.mkdir(configs["output_json_dir"])

    # convert pdf file to images
    pages = pdf2image.convert_from_path(file, dpi=300, fmt='png')
    data = {}
    data["blocks"] = []

    print("File Path:", file)
    # loop through every page image
    for page_no, page in enumerate(pages):
        print("Page No: " + str(page_no + 1) + "/" + str(len(pages)))
        img = np.array(page)

        # save pdf images
        if args.save_images:
            img_path = os.path.join(
                pdf_img_dir, pdf_file_name + "_Page" + str(page_no + 1) + ".png"
            )
            cv2.imwrite(img_path, img)

        try:
            # extracting ocra data from image
            ocr_data = pytesseract.image_to_data(
                img, lang=configs["language"], output_type=pytesseract.Output.DATAFRAME
            )
        except Exception as e:
            print_error("OCR Failed on " + file.split("/")[-1] + " | Page No "+ str(page_no+1))
            print("Trace:", e)
            continue

        # get the data dictionary for json file
        data = extract_blocks(ocr_data, img, page_no, data)

        # save output images with bounding boxes
        if args.debug:
            img_path = os.path.join(
                debug_img_dir, pdf_file_name + "_Page" + str(page_no + 1) + ".png"
            )
            cv2.imwrite(img_path, img)

    # writing python dictionary to json file
    with open(
        os.path.join(configs["output_json_dir"], pdf_file_name + ".json"),
        "w",
        encoding="UTF-8",
    ) as f:
        json.dump(data, f, ensure_ascii=False)
