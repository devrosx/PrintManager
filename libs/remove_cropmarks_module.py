#!/usr/bin/env python3
# crop PDF (convert to JPG saved to TMP folder (you can specify which page to use to crop rest pages or crop all pages individually))
import os
from PyPDF2 import PdfWriter, PdfReader

def pdf_cropper(pdf_input, multipage, outputpdf, pages):
    pdf_file = PdfReader(open(pdf_input, 'rb'))
    output = PdfWriter()

    if multipage:
        for i in range(pages):
            page = pdf_file.pages[i]
            # Update the crop box based on the trim box
            page.cropbox.lower_left = (page.trimbox.lower_left[0], page.trimbox.lower_left[1])
            page.cropbox.upper_right = (page.trimbox.upper_right[0], page.trimbox.upper_right[1])
            page.mediabox.lower_left = (page.trimbox.lower_left[0], page.trimbox.lower_left[1])
            page.mediabox.upper_right = (page.trimbox.upper_right[0], page.trimbox.upper_right[1])
            output.add_page(page)

        with open(outputpdf, "wb") as out_f:
            output.write(out_f)
            print('Saved file: ' + outputpdf)
    else:
        print('Multipage option is off')

def pdf_get_num_pages(pdf_input):
    pdf_file = PdfReader(open(pdf_input, 'rb'))
    pages = len(pdf_file.pages)
    return pages

def remove_cropmarks_mod(pdf_input, multipage):
    head, ext = os.path.splitext(pdf_input)
    outputpdf = head + '_crop' + ext
    pages = pdf_get_num_pages(pdf_input)
    pdf_cropper(pdf_input, multipage, outputpdf, pages)
    debugstring = 'File cropped'
    return debugstring, outputpdf

if __name__ == '__main__':
    pdf_input = '/Users/jandevera/Desktop/843_150x_tisk.pdf'
    remove_cropmarks_mod(pdf_input, multipage=True)
