from re import S
from PyPDF2 import PdfFileReader
from PyPDF2.generic import *
from ImageParser import build_page_images_dict
from ImageParser import ImageObject
from jinja2 import Environment, PackageLoader
from FontInfo import FontInfo
import os
import subprocess

def replace_indirect_objects (obj, reader):
    #print (f"{obj}, {type(obj)}")
    if type(obj) == IndirectObject:
        #print (f"generation: {obj.generation}, id: {obj.idnum}")
        return replace_indirect_objects(reader.get_object(obj), reader)
    elif type(obj) == ArrayObject:
        return [replace_indirect_objects(i, reader) for i in obj]
    elif type(obj) == DictionaryObject or type(obj) == EncodedStreamObject:
        dict = {}
        for i in obj.keys():
            dict[i] = replace_indirect_objects(obj[i], reader)
        return dict
    else:
        return obj

def get_xobj_images (xobj, images):
        if '/Subtype' in xobj:
            if xobj['/Subtype'] == '/Form':
                if '/XObject' in xobj['/Resources']:
                    for obj in xobj['/Resources']['/XObject']:
                        get_xobj_images(xobj['/Resources']['/XObject'][obj], images)
                else:
                    # raise Exception ("Not an image")
                    print ("Not an image")
            elif xobj['/Subtype'] == '/Image':
                images.append(ImageObject._xobj_img_2_png(xobj))
            else:
                raise Exception("Invalid XObject")
        else:
            for obj in xobj:
                get_xobj_images(xobj[obj], images)

def get_page_stuff (reader, page_num):
    page = reader.pages[page_num]
    page_dict = {}
    for i in page:
        print (i)
        if i != '/Parent':
            page_dict[i] = replace_indirect_objects(page[i], reader)
    return page_dict

def get_doc_size (fname):
    return os.path.getsize(fname)

def get_num_words (reader):
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return len(text.split())

def get_page_images_size (reader, page_num):
    resources = reader.pages[page_num]['/Resources']
    a = []
    sizes = []
    try:
        get_xobj_images(resources['/XObject'], a)
        for (ext, data) in a:
            #img = Image.open(io.BytesIO(data))
            sizes.append(len(data))
        return sizes
    except:
        return None

def normalize_page_image_sizes (page_img_sizes):
    flat = {}
    largest = 0
    for i in page_img_sizes.keys():
        if page_img_sizes[i]:
            for size in page_img_sizes[i]:
                if size > largest:
                    largest = size
        else:
            page_img_sizes[i] = [0]
    for i in page_img_sizes.keys():
        if page_img_sizes[i]:
            for j in range(len(page_img_sizes[i])):
                page_img_sizes[i][j] /= largest
            page_img_sizes[i].sort(reverse=True)
    return largest

def get_pdfinfo (fname):
    cmd = ["pdfinfo", fname]
    completed_process = subprocess.run(cmd, capture_output=True)
    output = completed_process.stdout.decode("utf-8")
    output_list = output.split ("\n")
    ret_dict = {}
    for entry in output_list:
        for i, c in enumerate(entry):
            if c == ':':
                key = entry[:i].strip()
                val = entry[i+1:].strip()
                if len(val):
                    ret_dict[key] = val
                else:
                    ret_dict[key] = None
                break
    return ret_dict

def get_pdffonts (fname):
    cmd = ["pdffonts", fname]
    completed_process = subprocess.run(cmd, capture_output=True)
    output = completed_process.stdout.decode("utf-8")
    lines = output.split ("\n")
    part_lengths = list(map(lambda x: x.count('-'), lines[1].split()))
    fonts = []
    for line in lines[2:-1]:
        parts = []
        part_sum = 0
        for part_num, part_length in enumerate(part_lengths):
            if part_num == len(part_lengths) - 1:
                obj, id = line[part_sum:part_sum+part_length].split()
                parts.append(obj.strip())
                parts.append(id.strip())
            else:
                parts.append(line[part_sum:part_sum+part_length].strip())
                part_sum += part_length+1
        fi = FontInfo (parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6], parts[7])
        fonts.append(fi)
    return fonts
    


def build_summary_page(fname, url):
    env = Environment (
        loader=PackageLoader("pdf_gui"),
        trim_blocks=True
    )
    env.filters['commafy'] = lambda x: "{:,}".format(x)
    template = env.get_template("summary_page.html")
    reader = PdfFileReader(fname)
    page_img_lens = {}
    for i in range(len(reader.pages)):
        page_img_lens[i] = get_page_images_size(reader, i)
    largest = normalize_page_image_sizes(page_img_lens)
    num_words = get_num_words(reader)
    fsize = get_doc_size(fname)
    avg_words = num_words / len(reader.pages)
    pdf_metadata = get_pdfinfo (fname)
    pdf_fonts = get_pdffonts(fname)
    return template.render(
        page_sizes=page_img_lens, 
        largest=largest, 
        explorer_page=f'/explorer/{fname}/',
        num_words=num_words,
        fsize=fsize,
        avg_words=avg_words,
        pdf_metadata=pdf_metadata,
        fonts=pdf_fonts
    )

get_pdffonts ('2207.07654.pdf')