#!/usr/bin/env python3
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
from PIL import Image
from PyPDF2 import PdfFileReader, generic
import zlib
import PIL.ImageOps 
import os

def get_color_mode(obj):
    try:
        cspace = obj['/ColorSpace']
    except KeyError:
        return None
    if cspace == '/DeviceRGB':
        return "RGB"
    elif cspace == '/DeviceCMYK':
        return "CMYK"
    elif cspace == '/DeviceGray':
        return "P"
    if isinstance(cspace, generic.ArrayObject) and cspace[0] == '/ICCBased':
        color_map = obj['/ColorSpace'][1].getObject()['/N']
        if color_map == 1:
            return "P"
        elif color_map == 3:
            return "RGB"
        elif color_map == 4:
            return "CMYK"

def get_object_images(x_obj):
    images = []
    for obj_name in x_obj:
        sub_obj = x_obj[obj_name]
        if '/Resources' in sub_obj and '/XObject' in sub_obj['/Resources']:
            images += get_object_images(sub_obj['/Resources']['/XObject'].getObject())
        elif sub_obj['/Subtype'] == '/Image':
            zlib_compressed = '/FlateDecode' in sub_obj.get('/Filter', '')
            if zlib_compressed:
               sub_obj._data = zlib.decompress(sub_obj._data)
            images.append((
                get_color_mode(sub_obj),
                (sub_obj['/Width'], sub_obj['/Height']),
                sub_obj._data
            ))
    return images

def get_pdf_images(pdf_fp):
    images = []
    try:
        pdf_in = PdfFileReader(open(pdf_fp, "rb"))
    except:
        return images
    for p_n in range(pdf_in.numPages):
        page = pdf_in.getPage(p_n)
        try:
            page_x_obj = page['/Resources']['/XObject'].getObject()
        except KeyError:
            continue
        images += get_object_images(page_x_obj)
    return images

def CMYKInvert(img) :
    return Image.merge(img.mode, [PIL.ImageOps.invert(b.convert('L')) for b in img.split()])

def extractfiles(original_file):
    x = 0
    fileslist = []
    head, ext = os.path.splitext(original_file)
    for image in get_pdf_images(original_file):
        (mode, size, data) = image
        try:
            img = Image.open(StringIO(data))
            # CMYK CONVERT
            img = CMYKInvert(img)
            x += 1
            # input_path = os.path.splitext(input_files)
            # files = input_path+str(x)+'.jpg'
            files = head+str(x)+'.jpg'
            img.save(files, 'JPEG')
            fileslist.append(files)
        except Exception as e:
            print ("Failed to read image with PIL: {}".format(e))
            continue
    return fileslist

if __name__ == "__main__":
    print ('ok')
    # fileslist = extractfiles(pdf_fp)