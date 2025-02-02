#!/usr/local/opt/python@3.12/bin/python3.12
# crop PDF (convert to JPG saved to TMP folder (you can specify which page to use to crop rest pages or crop all pages individually))
import cv2
import numpy as np
import os
import sys
import subprocess
from PyPDF2 import PdfWriter, PdfReader
system = str(sys.platform)
os.environ['PATH'] += ':/usr/bin:/usr/local/bin'
debug_mode = False
window_name = 'debug'

def raster_this_file_(pdf_input, res, croppage, multipage, pages):
    outputfiles = []
    outputdir = "/tmp/"
    head, ext = os.path.splitext(pdf_input)
    filename = os.path.basename(pdf_input)
    file, ext = os.path.splitext(filename)
    outputfile = outputdir + file + '_r.jpg'
    outputpdf = head + '_cropped' + ext
    
    if multipage and pages > 1:
        print('Converting all pages in PDF (multipage)')
        command = ["convert", "-density", str(res), "+antialias", str(pdf_input), str(outputfile)]
        subprocess.run(command)
        for i in range(pages):
            newfile = outputdir + (str(os.path.splitext(file)[0]) + '_r-' + str(i) + '.jpg')
            outputfiles.append(newfile)
    else:
        print('Converting only specific pages (singlepage)')
        pdf_input = pdf_input + '[' + str(croppage) + ']'
        command = ["convert", "-density", str(res), "+antialias", str(pdf_input), str(outputfile)]
        subprocess.run(command)
        outputfiles.append(outputfile)

    return outputfiles, outputpdf

def get_image_width_height(image):
    image_width = image.shape[1]  # current image's width
    image_height = image.shape[0]  # current image's height
    return image_width, image_height

def detect_box(image, margin):
    image_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    image_y = np.zeros(image_yuv.shape[0:2], np.uint8)
    image_y[:, :] = image_yuv[:, :, 0]
    image_blurred = cv2.GaussianBlur(image_y, (3, 3), 0)
    edges = cv2.Canny(image_blurred, 100, 300, apertureSize=3)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    new_contours = []
    
    for c in contours:
        if cv2.contourArea(c) < 4000000:
            new_contours.append(c)

    # Get overall bounding box
    best_box = [-1, -1, -1, -1]
    for c in new_contours:
        x, y, w, h = cv2.boundingRect(c)
        if best_box[0] < 0:
            best_box = [x, y, x + w, y + h]
        else:
            if x < best_box[0]:
                best_box[0] = x
            if y < best_box[1]:
                best_box[1] = y
            if x + w > best_box[2]:
                best_box[2] = x + w
            if y + h > best_box[3]:
                best_box[3] = y + h

    cv2.rectangle(image, (best_box[0] - margin, best_box[1] - margin), (best_box[2] + margin, best_box[3] + margin), (255, 255, 0), 2)
    cropbox = ([best_box[1] - margin, best_box[3] + margin, best_box[0] - margin, best_box[2] + margin])
    if debug_mode:
        show_image(image, window_name)
    return image, cropbox

# Show image for debug
def show_image(image, window_name):
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, image)
    image_width, image_height = get_image_width_height(image)
    cv2.resizeWindow(window_name, image_width, image_height)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def pdf_cropper(pdf_input, cropboxes, multipage, outputpdf, pages):
    pdf_file = PdfReader(open(pdf_input, 'rb'))
    output = PdfWriter()
    
    for i in range(pages):
        page = pdf_file.pages[i]
        print('TRIMBOX' + str(page.trimbox))
        print('CROPBOX' + str(page.cropbox))
        print('cropbox to crop' + str(cropboxes[i]))
        page.trimbox.upper_left = (cropboxes[i][3], cropboxes[i][1])
        page.trimbox.lower_right = (cropboxes[i][2], cropboxes[i][0])
        print(page.trimbox.upper_left, page.trimbox.lower_right)

        output.add_page(page)

    with open(outputpdf, "wb") as out_f:
        output.write(out_f)
        print('Saved file: ' + outputpdf)

def pdf_get_num_pages(pdf_input):
    pdf_file = PdfReader(open(pdf_input, 'rb'))
    pages = len(pdf_file.pages)
    return pages

def detect_cropboxes(pages, file, margin, multipage):
    cropboxes = []
    if multipage:
        for i in range(pages):
            images = cv2.imread(file[i])
            image, cropbox = detect_box(images, margin)
            cropboxes.append(cropbox)
        return cropboxes
    else:
        for i in range(pages):
            images = cv2.imread(file[0])
            image, cropbox = detect_box(images, margin)
            cropboxes.append(cropbox)
        return cropboxes        

def super_crop(pdf_input, res, croppage, multipage, margin):
    pages = pdf_get_num_pages(pdf_input)
    file, outputpdf = raster_this_file_(pdf_input, res, croppage, multipage, pages)
    print('Rasterized file (JPG): ' + str(file))
    cropboxes = detect_cropboxes(pages, file, margin, multipage)
    pdf_cropper(pdf_input, cropboxes, multipage, outputpdf, pages)
    debugstring = 'file cropped'
    return debugstring, outputpdf

if __name__ == '__main__':
    pdf_input = '/Users/mac/Desktop/beginners_python_cheat_sheet_pcc_all 2.pdf'
    super_crop(pdf_input, 72, croppage=0, multipage=True, margin=0)