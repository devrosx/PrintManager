#!/usr/bin/env python3
try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract

def ocr_core(filename, lang):
    """
    This function will handle the core OCR processing of images.
    """
    text = pytesseract.image_to_string(Image.open(filename), lang=lang)  # We'll use Pillow's Image class to open the image and pytesseract to detect the string in the image
    if(len(text)==0):
    	text = 'OCR did not find any text'
    return text

if __name__ == '__main__':
	filename = '/private/tmp/pm.jpg'
	lang = 'ces'
	print (ocr_core(filename, lang))