import argparse
import json
from glob import glob
import os

import cv2
import pdf2image
import pytesseract
import numpy as np
from PIL import Image

import yaml


def getConfig():
    configs = None
    with open("config.yaml", 'r') as stream:
        try:
            configs = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    return configs

def createDirs(imageDir=None, fileName=None):
    pdf_file_name = fileName
    # creating debug directory
    if not os.path.exists(imageDir):
        os.mkdir(imageDir)
    # creating directory for each pdf file
    imgs_dir = os.path.join(imageDir, pdf_file_name)
    if not os.path.exists(imgs_dir):
        os.mkdir(imgs_dir)

    return imgs_dir
    
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
                                cv2.rectangle(page_image, (topL["topleft"]["x"], topL["topleft"]["y"]),(bottomR["bottomright"]["x"], bottomR["bottomright"]["y"]), (0, 0, 255), 2)
                    
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
                            line_topL = {}
                            line_bottomR = {}
                            for _, line_row in line.iterrows():
                                # at level = 4, rows contain bounding boxes on line level
                                if line_row["level"] == 4:
                                    line_topL = { "x": line_row["left"], "y": line_row["top"], }
                                    line_bottomR = { "x": line_row["left"] + line_row["width"], "y": line_row["top"] + line_row["height"],}

                                # select the non-empty words having confidence > 10%
                                if ( line_row["conf"] > -1
                                    and not str(line_row["text"]).isspace()
                                    and line_row["level"] == 5 ):
                                    # concatenate the words text into one line
                                    text += " " + str(line_row["text"])

                            # replace unicode characters from text to nearly ascii characters
                            line_dict["topleft"] = line_topL
                            line_dict["text"] = text[1:]
                            line_dict["bottomright"] = line_bottomR
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
    return output_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-i",
        dest="pdf_file",
        help="enter the path to pdf file",
        required=True,
    )

    parser.add_argument(
        "-s", "--save_images", help="save images of pdf file", action="store_true"
    )

    parser.add_argument(
        "-d", "--debug", help="turn on the debug mode", action="store_true"
    )

    args = parser.parse_args()
    
    configs = getConfig()

    os.environ['TESSDATA_PREFIX'] = configs['tessdata']  # os.path.join(os.getcwd(), configs['tessdata'])

    file = args.pdf_file
    print("File Path:", file)
    pdf_file_name = file.split("/")[-1][:-4]
    
    if args.save_images:
        pdf_img_dir = createDirs(imageDir=configs["pdf_images_dir"], fileName=pdf_file_name)

    if args.debug:
        debug_img_dir = createDirs(imageDir=configs["debug_images_dir"], fileName=pdf_file_name)

    if not os.path.exists(os.environ['TESSDATA_PREFIX']):
        os.mkdir(os.environ['TESSDATA_PREFIX'])

    # creating blocks directory to store json files
    if not os.path.exists(configs["output_json_dir"]):
        os.mkdir(configs["output_json_dir"])   

    # convert pdf file to images
    pages = pdf2image.convert_from_path(file)
    data = {}
    data["blocks"] = []

    # download tesseract traineddata file for language if it doesn't exist 
    if not os.path.isfile(os.path.join(os.environ['TESSDATA_PREFIX'], configs['language'] + ".traineddata")):
        print(configs['language'] + ".traineddata not found in " + configs['tessdata']  + ". Downloading file:")
        url = 'https://github.com/tesseract-ocr/tessdata_best/raw/master/' + configs['language'] + '.traineddata'
        cmd = "sudo wget -O" + os.path.join(os.environ['TESSDATA_PREFIX'], configs['language'] + ".traineddata") + " " + url
        os.system(cmd)
        
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
                img, lang=configs['language'], output_type=pytesseract.Output.DATAFRAME
            )
        except Exception as e:
            print("OCR Failed:", e)
            continue

        # get the data dictionary for json file
        data = getDataForJson(ocr_data, img, page_no, data)
            
        # save output images with bounding boxes
        if args.debug:
            img_path = os.path.join(
                debug_img_dir, pdf_file_name + "_Page" + str(page_no + 1) + ".png"
            )
            cv2.imwrite(img_path, img)

    # writing python dictionary to json file
    with open(os.path.join(configs["output_json_dir"], pdf_file_name + ".json"), "w", encoding="UTF-8") as f:
        json.dump(data, f, ensure_ascii=False)