#!/usr/bin/env python3
# crop PDF (convert to JPG saved to TMP folder (you can specify witch page tu use to crop rest pages or crop all pages individualy))
import cv2
import numpy as np
import os
import subprocess
from PyPDF2 import PdfFileWriter,PdfFileReader,PdfFileMerger

debug_mode = False
window_name = 'debug'
pdf_input = '/Users/jandevera/Desktop/testy/Vizitky2_raster.pdf'

def raster_this_file(pdf_input, res, croppage, multipage, pages):
	outputfiles = []
	outputdir = "/private/tmp/"
	head, ext = os.path.splitext(pdf_input)
	filename = os.path.basename(pdf_input)
	file, ext = os.path.splitext(filename)
	outputfile = outputdir + file + '_r.jpg'
	outputpdf = head + 'croped' + ext
	if multipage == 1 and pages > 1:
		print ('converting all pages in PDF (multipage)')
		command = ["convert", "-density", str(res), "+antialias", str(pdf_input), str(outputfile)]
		for i in range(pages):
			newfile = outputdir + (str(os.path.splitext(file)[0])+'_r-'+str(i)+'.jpg')
			outputfiles.append(newfile)
	else:
		multipages = 0
		print ('converting only specific pages (singlepage)')
		pdf_input = pdf_input+'['+str(croppage)+']'
		command = ["convert", "-density", str(res), "+antialias", str(pdf_input), str(outputfile)]
		outputfiles.append(outputfile)
	subprocess.run(command)
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
	cv2.rectangle(image, (best_box[0]-margin, best_box[1]-margin), (best_box[2]+margin, best_box[3]+margin), (255, 255, 0), 2)
	cropbox = ([best_box[1]-margin,best_box[3]+margin, best_box[0]-margin,best_box[2]+margin])
	if (debug_mode):
		show_image(image, window_name)
	return image, cropbox

# Show image for debug
def show_image(image, window_name):
	cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
	cv2.imshow(window_name, image)
	image_width, image_height = get_image_width_height(image)
	print ('velikost obrazku:' + str(image_width) + ' x ' +  str(image_height) + ' points')
	cv2.resizeWindow(window_name, image_width, image_height)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

def pdf_cropper(pdf_input,cropboxes, multipage,outputpdf):
	pdf_file = PdfFileReader(open(pdf_input, 'rb'))
	output = PdfFileWriter()
	pages = pdf_file.getNumPages()
	if multipage == 1:
		for i in range(pages):
			# print (cropboxes[i][0])
			page = pdf_file.getPage(i)
			page.cropBox.upperLeft = (cropboxes[i][3], cropboxes[i][1])
			page.cropBox.lowerRight = (cropboxes[i][2], cropboxes[i][0])
			output.addPage(page)
		with open(outputpdf, "wb") as out_f:
			output.write(out_f)
			# print ('Saved file: '+outputpdf)
	else:
		for i in range(pages):
			print (cropboxes[0][0])
			page = pdf_file.getPage(i)
			page.cropBox.upperLeft = (cropboxes[0][3], cropboxes[0][1])
			page.cropBox.lowerRight = (cropboxes[0][2], cropboxes[0][0])
			output.addPage(page)
		with open(outputpdf, "wb") as out_f:
			output.write(out_f)
			# print ('Saved file: '+ outputpdf)

def pdf_get_num_pages(pdf_input):
	pdf_file = PdfFileReader(open(pdf_input, 'rb'))
	pages = pdf_file.getNumPages()
	return pages

def detect_cropboxes(pages,file,margin,multipage):
	cropboxes = []
	if multipage == 1:
		for i in range(pages):
			# print (file[i])
			images = cv2.imread(file[i])
			image, cropbox = detect_box(images, margin)
			cropboxes.append(cropbox)
		return cropboxes
	else:
		for i in range(pages):
			# print (file[0])
			images = cv2.imread(file[0])
			image, cropbox = detect_box(images, margin)
			cropboxes.append(cropbox)
		return cropboxes		

def convertor(pdf_input,res,croppage,multipage,margin):
	# print ('starting supercrop / ' + 'margin je: ' + str(margin))
	pages = pdf_get_num_pages(pdf_input)
	file,outputpdf = raster_this_file(pdf_input, res, croppage, multipage, pages)
	print ('Rasterized file (JPG): ' + str(file))
	cropboxes = detect_cropboxes(pages,file,margin,multipage)
	# print (cropboxes)
	pdf_cropper(pdf_input,cropboxes,multipage,outputpdf)
	debugstring = 'file croped'
	return debugstring, outputpdf

if __name__ == '__main__':
	convertor(pdf_input,72,croppage=0,multipage=1,margin=0)