#!/usr/bin/env python3
# crop PDF (convert to JPG saved to TMP folder (you can specify witch page tu use to crop rest pages or crop all pages individualy))
import cv2
import numpy as np
import os
import subprocess
from PyPDF2 import PdfFileWriter,PdfFileReader,PdfFileMerger

debug_mode = False

def pdf_cropper(pdf_input,multipage,outputpdf,pages):
	pdf_file = PdfFileReader(open(pdf_input, 'rb'))
	output = PdfFileWriter()
	if multipage == 1:
		for i in range(pages):
			page = pdf_file.getPage(i)
			# print ('TRIMBOX'+ str(i) + ':' +str(page.trimBox))
			# print ('CROPBOX'+ str(i) + ':' +str(page.cropBox))
			# print ('cropbox to crop' + str(cropboxes[0]))
			page.cropBox.upperLeft = (page.trimBox[0], page.trimBox[1])
			page.cropBox.lowerRight = (page.trimBox[2], page.trimBox[3])
			page.mediaBox.upperLeft = (page.trimBox[0], page.trimBox[1])
			page.mediaBox.lowerRight = (page.trimBox[2], page.trimBox[3])
			# print (page.trimBox.upperLeft, page.trimBox.lowerRight)
			# print ('output cropbox XXXX' +str(page.cropBox))
			output.addPage(page)
			# print ('CROPBOX _fixed'+ str(i) + ':' +str(page.cropBox))
		with open(outputpdf, "wb") as out_f:
			output.write(out_f)
			print ('Saved file: '+outputpdf)
	else:
		print ('off')

def pdf_get_num_pages(pdf_input):
	pdf_file = PdfFileReader(open(pdf_input, 'rb'))
	pages = pdf_file.getNumPages()
	return pages

def remove_cropmarks_mod(pdf_input,multipage):
	head, ext = os.path.splitext(pdf_input)
	outputpdf = head + '_crop' + ext
	# print (outputpdf)
	# print ('starting supercrop / ' + 'margin je: ' + str(margin))
	pages = pdf_get_num_pages(pdf_input)
	# print (cropboxes)
	pdf_cropper(pdf_input,multipage,outputpdf,pages)
	debugstring = 'file croped'
	return debugstring, outputpdf

if __name__ == '__main__':
	pdf_input = '/Users/jandevera/Desktop/843_150x_tisk.pdf'
	remove_cropmarks_mod(pdf_input,multipage=True)