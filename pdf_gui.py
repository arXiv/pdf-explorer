from PyPDF2 import PdfFileReader
from PyPDF2.generic import *
import PyPDF2
from jinja2 import Environment, PackageLoader, select_autoescape
import json
from ImageParser import build_page_images_dict
from treeview import build_tree_list
from pdf2image import convert_from_path
import sys
import os

def get_page_images (fname):
    images = convert_from_path (fname)
    dir = fname[:-4] + "_images"
    try:
        os.mkdir(dir)
    except:
        pass
    abs = f"{os.getcwd()}/{dir}"
    for i in range(len(images)):
        images[i].save(abs+f"/{i}.png")
    return abs


env = Environment (
    loader=PackageLoader("pdf_gui"),
    trim_blocks=True
)
template = env.get_template("two_col.html")

def generate_two_col (fname):
    f = open(fname[:-4]+".html", "w+")
    dir = get_page_images (fname)
    image_dict = {}
    first_image = dir + "/0.png"
    reader = PdfFileReader(fname)
    for i, filename in enumerate(os.listdir(dir)):
        if (os.path.isdir(dir + "/" + filename)):
            continue
        page_num = int(filename.split(".")[0])
        image_dict[page_num] = build_page_images_dict(reader.pages[page_num], page_num, dir)
    treeview = [build_tree_list(reader.pages[i], 1, "") for i in range(len(reader.pages))]
    f.write(template.render(image_dict=image_dict, first_image=first_image, image_dir=dir, treeview=treeview))
    f.close()

generate_two_col(sys.argv[1])