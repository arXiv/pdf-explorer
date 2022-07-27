import PyPDF2
from PyPDF2 import PdfFileReader
from PyPDF2.generic import *

# reader = PdfFileReader("2207.05758.pdf")
# list(reader.pages)

def replace_indirect_objects (obj):
    #print (f"{obj}, {type(obj)}")
    if type(obj) == IndirectObject:
        #print (f"generation: {obj.generation}, id: {obj.idnum}")
        return replace_indirect_objects(reader.get_object(obj))
    elif type(obj) == ArrayObject:
        return [replace_indirect_objects(i) for i in obj]
    elif type(obj) == DictionaryObject or type(obj) == EncodedStreamObject:
        dict = {}
        for i in obj.keys():
            dict[i] = replace_indirect_objects(obj[i])
        return dict
    else:
        return obj

def print_page_tree (dict, indentation_level):
    tab = '\t'
    for name in dict.keys():
        if type(dict[name]) == DictionaryObject:
            print (f"{indentation_level * tab}{name}:")
            print_page_tree(dict[name], indentation_level + 1)
        elif type(dict[name] == EncodedStreamObject):
            try:
                print_page_tree(dict[name], indentation_level + 1)
            except:
                print (f"{indentation_level * tab}{name}: {dict[name]}")
        else:
            print (f"{indentation_level * tab}{name}: {dict[name]}")
        
def build_tree_list (dict, indentation_level, ret):
    tab = '\t'
    for name in dict.keys():
        if type(dict[name]) == DictionaryObject:
            ret += f"{indentation_level * tab}<li><span class=\"caret\">{name}:</span>\n"
            ret += f"{(indentation_level + 1) * tab}<ul class=\"nested\">\n"
            ret = build_tree_list(dict[name], indentation_level + 2, ret)
            ret += f"{(indentation_level + 1) * tab}</ul>\n"
            ret += f"{indentation_level * tab}</li>\n"
        elif type(dict[name] == EncodedStreamObject):
            try:
                ret = build_tree_list(dict[name], indentation_level + 1, ret)
            except:
                ret += f"{indentation_level * tab}<li>{name}: {dict[name]}</li>\n"
        # elif type(dict[name] == ArrayObject):
        #     f.write(f"{indentation_level * tab}<li><span class=\"caret\">{name}:</span>\n")
        #     f.write(f"{(indentation_level + 1) * tab}<ul class=\"nested\">\n")
        #     f.write(print_page_tree(dict[name], indentation_level + 2))
        #     f.write(f"{(indentation_level + 1) * tab}</ul>\n")
        #     f.write(f"{indentation_level * tab}</li>\n")
        else:
            ret += f"{indentation_level * tab}<li>{name}: {dict[name]}</li>\n"
    return ret    
    

from PIL import Image

from jinja2 import Environment, PackageLoader, select_autoescape

env = Environment (
    loader=PackageLoader("pdf_gui"),
    trim_blocks=True
    #autoescape=select_autoescape()
)
template = env.get_template("template.html")

def generate_html (page_tree, fname):
    f = open(fname, "w+")
    pages = []
    for i in page_tree:
        pages.append(build_tree_list(replace_indirect_objects(i), 1, ""))
    page_images = []
    
    f.write (template.render(pages=pages))
    f.close()

# generate_html (reader.pages, "2207.07175.html")
# t = reader.pages[0]["/Contents"]
#print (replace_indirect_objects(t))
#print (reader.cache_get_indirect_object(t.generation, t.idnum))
#c=0
# for obj in reader.pages[1]["/Resources"]["/XObject"]["/Im1"]["/Resources"]:
#     print (f"{c}: {obj}")
#     c+=1

# for page in doc:
#     get_images(page)

#print (replace_indirect_objects(reader.pages[2]['/Annots'][0]))