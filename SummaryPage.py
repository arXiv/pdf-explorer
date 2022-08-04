from re import S
from PyPDF2 import PdfFileReader
from PyPDF2.generic import *
from ImageParser import build_page_images_dict
from ImageParser import ImageObject
from jinja2 import Environment, PackageLoader

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
            s = sum(page_img_sizes[i])
            flat[i] = s
            if s > largest:
                largest = s
        else:
            flat[i] = 0
    for i in flat.keys():
        flat[i] /= largest
    return (flat, largest)

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
    page_sizes, largest = normalize_page_image_sizes(page_img_lens)
    return template.render(page_sizes=page_sizes, largest=largest, explorer_page=url)