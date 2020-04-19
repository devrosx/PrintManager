#!/usr/bin/env python3
# crop PDF (convert to JPG saved to TMP folder (you can specify witch page tu use to crop rest pages or crop all pages individualy))
import cv2
import numpy as np
import os
import subprocess
from PyPDF2 import PdfFileWriter,PdfFileReader,PdfFileMerger

debug_mode = True
window_name = 'debug'

def raster_this_file(input_file, res, croppage, multipage, pages):
	file_name = os.path.basename(input_file)
	file, ext = os.path.splitext(file_name)
	cmd = ["convert", "-density", str(res), "+antialias", input_file+'[0]', "jpg:-"]
	fconvert = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = fconvert.communicate()
	assert fconvert.returncode == 0, stderr
	file_data = np.asarray(bytearray(stdout), dtype=np.uint8)
	return file_name, file_data

def get_image_width_height(image):
	image_width = image.shape[1]  # current image's width
	image_height = image.shape[0]  # current image's height
	return image_width, image_height

def detect_box(image, margin):
	image = cv2.imdecode(image, cv2.IMREAD_COLOR)
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
	cv2.rectangle(image, (best_box[0]-margin, best_box[1]-margin), (best_box[2]+margin, best_box[3]+margin), (255, 50, 0), 2)
	cropbox = ([best_box[1]-margin,best_box[3]+margin, best_box[0]-margin,best_box[2]+margin])
	if (debug_mode):
		print (cropbox)
		show_image(image, window_name)
	return image, cropbox

# Show image for debug
def show_image(image, window_name):
	cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
	cv2.imshow(window_name, image)
	image_width, image_height = get_image_width_height(image)
	print (image_width, image_height)
	# print ('velikost obrazku:' + str(image_width) + ' x ' +  str(image_height) + ' points')
	cv2.resizeWindow(window_name, image_width, image_height)
	cv2.waitKey(0)
	cv2.destroyAllWindows()

def pdf_cropper(pdf_input,cropboxes, multipage,outputpdf):
	pdf_file = PdfFileReader(open(pdf_input, 'rb'))
	output = PdfFileWriter()
	pages = pdf_file.getNumPages()
	# print (pages-1)
	for i in range(pages-1):
			page = pdf_file.getPage(i)
			page.cropBox.upperLeft = (cropboxes[i][3], cropboxes[i][1])
			page.cropBox.lowerRight = (cropboxes[i][2], cropboxes[i][0])
			output.addPage(page)
	with open(outputpdf, "wb") as out_f:
		output.write(out_f)
		print ('Saved file: '+outputpdf)
	# if multipage == 1:
	# 	for i in range(pages):
	# 		# print (cropboxes[i][0])
	# 		page = pdf_file.getPage(i)
	# 		page.cropBox.upperLeft = (cropboxes[i][3], cropboxes[i][1])
	# 		page.cropBox.lowerRight = (cropboxes[i][2], cropboxes[i][0])
	# 		output.addPage(page)
	# 	with open(outputpdf, "wb") as out_f:
	# 		output.write(out_f)
	# 		# print ('Saved file: '+outputpdf)
	# else:
	# 	for i in range(pages):
	# 		print (cropboxes[0][0])
	# 		page = pdf_file.getPage(i)
	# 		page.cropBox.upperLeft = (cropboxes[0][3], cropboxes[0][1])
	# 		page.cropBox.lowerRight = (cropboxes[0][2], cropboxes[0][0])
	# 		output.addPage(page)
	# 	with open(outputpdf, "wb") as out_f:
	# 		output.write(out_f)
	# 		# print ('Saved file: '+ outputpdf)

def pdf_get_num_pages(pdf_input):
	pdf_file = PdfFileReader(open(pdf_input, 'rb'))
	pages = pdf_file.getNumPages()
	return pages

def detect_cropboxes(file_data, margin):
	cropboxes = []
	image, cropbox = detect_box(file_data, margin)
	return cropbox
	# if multipage == True:
	# 	for i in range(pages):
	# 		# print (file[i])
	# 		images = cv2.imread(file[i])
	# 		image, cropbox = detect_box(images, margin)
	# 		cropboxes.append(cropbox)
	# 	return cropboxes
	# else:
	# 	for i in range(pages):
	# 		# print (file[0])
	# 		images = cv2.imread(file[0])
	# 		image, cropbox = detect_box(images, margin)
	# 		cropboxes.append(cropbox)
				

def convertor(pdf_input,res,croppage,multipage,margin):
	pages = pdf_get_num_pages(pdf_input)
	print ('STARTING SUPERCROP MODULE / ' + 'margin is: ' + str(margin) + ' / pages:' +str(pages) + ' / multipage is: ' +str(multipage))
	print ('INPUT FILE: ' +str(pdf_input))
	file_name,file_data = raster_this_file(pdf_input, res, croppage, multipage, pages)
	cropboxes = detect_cropboxes(file_data, margin)
	print ('FILE NAME: ' +str(file_name))
	print ('CROPBOX: ' +str(cropboxes))

	# print ('Rasterized file (JPG): ' + str(file_name))
	# debug
	# image_yuv = cv2.imdecode(file_data, cv2.COLOR_BGR2YUV)
	# cv2.imshow('test',image_yuv)
	# cv2.waitKey(0)
	# cv2.destroyAllWindows()
	head, ext = os.path.splitext(pdf_input)
	# file_name = os.path.basename(input_file)
	# file, ext = os.path.splitext(file_name)
	# outputfile = outputdir + file + '_r.jpg'
	outputpdf = head + '_croped' + ext
	print (outputpdf)
	# cropboxes = detect_cropboxes(pages,file,margin,multipage)
	# print (cropboxes)
	pdf_cropper(pdf_input,cropboxes,multipage,outputpdf)
	# debugstring = 'file croped'
	# return debugstring, outputpdf

if __name__ == '__main__':
	pdf_input = '/Users/jandevera/Desktop/X/Vizitky.pdf'
	convertor(pdf_input,72,croppage=0,multipage=True,margin=0)