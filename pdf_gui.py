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

def get_images_dir (fname):
    dir = fname[:-4] + "_images"
    abs = f"{os.getcwd()}/static/{dir}"
    try:
        os.mkdir(abs)
    except:
        pass
    return (dir, abs)

def get_page_image (fname, page_num, path):
    image = convert_from_path (fname, first_page=page_num+1, last_page=page_num+1)[0]
    image.save(path)

def get_bboxes (fname, page_num):
    page = PdfFileReader(fname).pages[page_num]
    if '/XObject' in page['/Resources']:
        xobj_bbox = page['/Resources']['/XObject']['/BBox']

def generate_two_col (fname, page_num):
    env = Environment (
        loader=PackageLoader("pdf_gui"),
        trim_blocks=True
    )
    env.filters['commafy'] = lambda x: "{:,}".format(x)
    template = env.get_template("single_page.html")
    #if os.path.exists() TODO: ADD OS EXISTS CHECK SO WE DONT DO SAME WORK TWICE
    dir, abs = get_images_dir(fname)
    if not os.path.exists(abs+f"/{page_num}.png"):
        get_page_image (fname, page_num, abs+f"/{page_num}.png")
    page_img = url_for('static', filename=(dir + f"/{page_num}.png"))
    reader = PdfFileReader(fname)
    image_dict = build_page_images_dict(reader.pages[page_num], page_num, abs)
    print(image_dict)
    treeview = build_tree_list(reader.pages[page_num], 1, "")
    left_arrow = url_for('explorer', doc_id=fname, page_num=(page_num - 1 if page_num != 0 else len(reader.pages) - 1))
    right_arrow = url_for('explorer', doc_id=fname, page_num=(page_num + 1 if page_num != len(reader.pages) - 1 else 0))
    return template.render(
        image_dict=image_dict, 
        page_img=page_img, 
        image_dir=f'/static/{dir}', 
        treeview=treeview, 
        left_arrow=left_arrow, 
        right_arrow=right_arrow
    )

#generate_two_col(sys.argv[1])