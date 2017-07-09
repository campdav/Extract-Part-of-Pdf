"""
by D. Campion

Objective:
  Extract part of pdf and save them to images.

usage example:
python PoPDF2Img.py
    --pdf ./data/paleo/documents/
    --pdflist ./data/paleo/ml/file
    --boxes ./data/paleo/ml/file.bbox
    --margin 0.15 (optional)
    --quality 200 (optional)
    --output ./data/output (optional)
    --temp ./data/temp (optional)

it will save images of boxes from the list of pdf.
images will be named:
pdfname-uuid-number_pn-[integer]_pw-[integer]_ph-[integer]_t-[integer]_l-[integer]_b-[integer]_r-[integer].jpg
where:
 - pn: the page number of the box
 - pw: the width of the page
 - ph: the height of the page
 - t: the top pixel of the box
 - l: the left pixel of the box
 - b: the bottom pixel of the box
 - r: the right pixel of the box

the bbox file is generated using the table-extraction/ml/extract_tables.py python file.

Pre-requisites:
  - ImageMagick [http://www.imagemagick.org/script/index.php] to Convert The PDF file

    $ sudo apt-get install libmagickwand-dev
    $ pip install Wand

  - Pillow:
    $ pip install Pillow
  More Installation http://sorry-wand.readthedocs.org/en/latest/guide/install.html
  More about wand https://pypi.python.org/pypi/Wand
"""

from PIL import Image as Img
from wand.image import Image
import uuid
import time
import numpy as np
import glob
import os
import sys
import argparse

#function to convert pdf files to images.
def create_box(filepdf, page_num, page_width, page_height, top, left, bottom, right, quality=200, margin=0.1):
    #extract filename:
    filebasename = os.path.basename(pdf_path + filepdf)

    print("extracting box from %s..." % filepdf)

    #used to generate temp file name.
    uuid_set = str(uuid.uuid4().fields[-1])[:5]
    img = Image(filename = pdf_path + filepdf, resolution=200)
    #resize image
    img.resize(page_width,page_height)
    #crop image
    img.compression_quality = int(quality)
    #save box
    img.save(filename = path_temp + "%s.jpg" % (uuid_set))
    print("temp pages saved.")

    #search all image in temp path. file name ends with uuid_set value
    list_im = glob.glob(path_temp + "%s*.jpg" % uuid_set)

    img_page = Image(filename = path_temp + "%s-%s.jpg" % (uuid_set ,str(page_num-1)), resolution=200)

    width, height = img_page.size

    #define zone to crop
    left = round(left * width / page_width)
    right = round(right * width / page_width)
    top = round(top * height / page_height)
    bottom = round(bottom * height / page_height)

    box_width = right-left
    box_height = bottom - top

    #add a margin around box
    left = round(left - margin * box_width) if round(left - margin * box_width)  > 1 else 1
    right = round(right + margin * box_width) if round(right + margin * box_width) < width - 1 else width - 1
    top = round(top - margin * box_height) if round(top - margin * box_height) > 1 else 1
    bottom = round(bottom + margin * box_height) if round(bottom + margin * box_height) < height - 1 else height - 1

    #crop the file
    img_page.crop(left, top, right, bottom)

    print("saving the image...")
    img_page.compression_quality = quality
    img_page.save(filename = path_boxs + filepdf + "-%s_pn-%s_pw-%s_ph-%s_t-%s_l-%s_b-%s_r-%s.jpg" % (uuid_set ,str(page_num),str(page_width), str(page_height), str(top), str(left), str(bottom), str(right)))

    for i in list_im:
        os.remove(i)
    return

def read_pdflist(pdf_list):
    print("Loading pdf list...")
    # load pickled data
    PDFs = open(pdf_list,encoding='UTF-8').readlines()

    #initiate array
    pdfarray = []

    for line in PDFs:
        line=line.replace("\n", "")
        pdfarray.append(line)

    return pdfarray

def read_boxeslist(boxes_list):
    print("Loading boxes list...")
    BOXs = open(boxes_list,encoding='UTF-8').readlines()

    array = []
    i = 0
    for line in BOXs:
        X = []
        for item in line.split(';'):
            for char in item:
                if char in ["(",")","\n"]:
                    item = item.replace(char,"")
            item = str(i) + "," + item
            X.append(item)

        for item in X:
            array.append(item.split(","))
        i+=1
    return array

def generate_box(pdfarray,boxarray,quality,margin):
    for item in boxarray:
        pdf_id = int(item[0])
        if item[1] != "NO_TABLES":
            pdf_id = int(item[0])
            page_num = int(item[1])
            page_width = int(item[2])
            page_height = int(item[3])
            top = int(item[4])
            left = int(item[5])
            bottom = int(item[6])
            right = int(item[7])
            print("create an image of a box from pdf: ",pdfarray[pdf_id], " page ", page_num)
            create_box(pdfarray[pdf_id], page_num, page_width, page_height, top, left, bottom, right,quality,margin)
        else:
            print("No boxes for the pdf: ",pdfarray[pdf_id])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--pdf", required=True,
        help="path to the folder where are stored pdf")
    ap.add_argument("-l", "--pdflist", required=True,
     	help="path to the document contening the list of pdf")
    ap.add_argument("-b", "--boxes", required=True,
     	help="path to the document contening the list of boxes to extract from pdf")
    ap.add_argument("-o", "--output", required=False,
     	help="path to the folder where will be stored output images")
    ap.add_argument("-t", "--temp", required=False,
     	help="path to the folder where will be stored temp images")
    ap.add_argument("-q", "--quality", required=False,
     	help="quality of the compression for output images")
    ap.add_argument("-m", "--margin", required=False,
     	help="margin to take around boxes to extract from pdf (% of the box)")

    args, leftovers = ap.parse_known_args()

    pdf_path = args.pdf
    path_boxs = args.output if args.output is not None else "./data/output/"
    path_temp = args.temp if args.temp is not None else "./data/temp/"
    quality = int(args.quality) if args.quality is not None else 200
    margin = float(args.margin) if args.margin is not None else 0.15

    pdfarray = read_pdflist(args.pdflist)
    boxarray = read_boxeslist(args.boxes)
    generate_box(pdfarray, boxarray,quality,margin)

    print("images created")
