from PyPDF2 import PdfFileReader
from PyPDF2.generic import *
import PyPDF2
from flask import url_for
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
    abs = f"{os.getcwd()}/static/{dir}"
    try:
        os.mkdir(abs)
    except:
        pass
    for i in range(len(images)):
        images[i].save(abs+f"/{i}.png")
    return dir




def generate_two_col (fname):
    env = Environment (
    loader=PackageLoader("pdf_gui"),
    trim_blocks=True
    )
    env.filters['commafy'] = lambda x: "{:,}".format(x)
    template = env.get_template("two_col.html")
    f = open(fname[:-4]+".html", "w+")
    dir = get_page_images (fname)
    abs = f"{os.getcwd()}/static/{dir}"
    image_dict = {}
    first_image = url_for('static', filename=(dir + "/0.png"))
    reader = PdfFileReader(fname)
    for i, filename in enumerate(os.listdir(abs)):
        if (os.path.isdir(abs + "/" + filename)):
            continue
        page_num = int(filename.split(".")[0])
        image_dict[page_num] = build_page_images_dict(reader.pages[page_num], page_num, abs)
    treeview = [build_tree_list(reader.pages[i], 1, "") for i in range(len(reader.pages))]
    print (len(image_dict))
    return template.render(image_dict=image_dict, first_image=first_image, image_dir=f'/static/{dir}', treeview=treeview)

#generate_two_col(sys.argv[1])