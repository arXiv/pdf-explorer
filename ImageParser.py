from typing import Dict
from flask import url_for
import numpy as np
from PyPDF2 import PdfReader
from PyPDF2.filters import _xobj_to_image
from PIL import Image
import io

class ImageObject:

    img_properties = [('/Type', False), 
                      ('/Subtype', True), 
                      ('/Width', True), 
                      ('/Height', True),
                      ('/ColorSpace', False), # Required for all but images which use JPXDecode Filter (JPEG2000 format) and image masks (/ImageMask = true)
                      ('/BitsPerComponent', False), # Same as above
                      ('/Intent', False),
                      ('/ImageMask', False),
                      ('/Mask', False),
                      ('/Decode', False),
                      ('/Interpolate', False),
                      ('/Alternates', False),
                      ('/Smask', False),
                      ('/SmaskInData', False),
                      ('/Name', False),
                      ('/StructParent', False),
                      ('/ID', False),
                      ('/OPI', False),
                      ('/Metadata', False),
                      ('/OC', False),
                      ('/Filter', False)] # (property_name, is_required)


    def __init__ (self, width, height, size, color_depth, format, data, ext):
        self.width = width
        self.height = height
        self.size = size # byte size
        self.color_depth = color_depth
        self.format = format
        self.ext = ext
        self.data = data
        
    def get_xobj_images (xobj, images):
        if '/Subtype' in xobj:
            if xobj['/Subtype'] == '/Form':
                if '/XObject' in xobj['/Resources']:
                    for obj in xobj['/Resources']['/XObject']:
                        ImageObject.get_xobj_images(xobj['/Resources']['/XObject'][obj], images)
                else:
                    # raise Exception ("Not an image")
                    print ("Not an image")
            elif xobj['/Subtype'] == '/Image':
                images.append(ImageObject._xobj_img_2_png(xobj))
            else:
                raise Exception("Invalid XObject")
        else:
            for obj in xobj:
                ImageObject.get_xobj_images(xobj[obj], images)

    def _xobj_img_2_png (xobj):
        state = {}
        for (property_name, is_required) in ImageObject.img_properties:
            if property_name in xobj:
                state[property_name] = xobj[property_name]
            elif is_required:
                raise Exception (f"Invalid Image XObject, {property_name} property is missing")
        # if '/ColorSpace' in state:
        #     bpc = state['/BitsPerComponent'] 
        #     if bpc < 8:
        #         raise Exception (f"Less than 8 bit color channels is unsupported")
        #     if state['/ColorSpace'] == '/DeviceGray':
        #         image_mat = np.zeros((state['/Height'], state['/Width']), dtype='uint8')
        #         bpp = bpc
        #     elif state['/ColorSpace'] == '/DeviceRGB':
        #         image_mat = np.zeros((state['/Height'], state['/Width'], 3), dtype='uint8')
        #         bpp = 3 * bpc
        #     elif state['/ColorSpace'] == '/DeviceCMYK':
        #         image_mat = np.zeros((state['/Height'], state['/Width'], 4), dtype='uint8')
        #         bpp = 4 * bpc
        #     else:
        #         raise Exception (f"/ColorSpace: {state['/ColorSpace']} is currently unsupported")
        # else:
        #     raise Exception ("JPEG2000 format and image masks are currently unsupported")
        # data = xobj.get_data()
        # for row in range(state['/Height']):
        #     for column in range(state['/Width']):
        #         start_i = (row * state['/Width'] + column) * bpp
        #         if bpp == bpc:
        #             image_mat[row][column] = int.from_bytes(data[start_i:(start_i+(bpc/8))], byteorder='big', signed=False)
        #         for i in range((int)(bpp / bpc)):
        #             image_mat[row][column][i] = int.from_bytes(data[start_i + (i * (int)(bpc/8)): start_i + ((i+1) * (int)(bpc/8))], byteorder='big', signed=False)
                    
        # print (image_mat[0][0])
        # img = Image.fromarray(image_mat)
        # if state['/Filter'] == '/DCTDecode':
        #     img.save("im1.jpg")
        # else:
        #     img.save("im1.png")
        return _xobj_to_image(xobj)
        


reader = PdfReader("2207.07654.pdf")

c = 0
for page in range(len(reader.pages)):
    resources = reader.pages[page]['/Resources']
    if '/XObject' in resources:
        a = []
        ImageObject.get_xobj_images(resources['/XObject'], a)
        for (ext, data) in a:
            img = Image.open(io.BytesIO(data))
            img.save(str(c) + ext)
            #img.show()
            c += 1

import os
def build_page_images_dict (page, page_num, dir):
    resources = page['/Resources']
    if '/XObject' in resources:
        new_dir = dir + "/page" + str(page_num)
        ret = []
        cur = 0
        try:
            os.mkdir(new_dir)
        except:
            pass
        a = []
        ImageObject.get_xobj_images(resources['/XObject'], a)
        print (f"{len(a)} images on page {page_num}")
        for (ext, data) in a:
            img = Image.open(io.BytesIO(data))
            img.save(new_dir + "/" + str(cur) + ext)
            img_data = {}
            img_data['location'] = url_for('static', filename=(new_dir + "/" + str(cur) + ext))
            img_data['height'] = img.height
            img_data['width'] = img.width
            img_data['size'] = len(data)
            img_data['page_num'] = page_num
            ret.append(img_data)
            cur += 1
    else:
        return None
    return ret