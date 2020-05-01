import os
import subprocess
import numpy
res = 72

def pdf_preview_generator(input_file,generate_marks):
	# print ("generate_marks:" + str(generate_marks)), "+antialias"
	cmd = ["convert", "-density", str(res), input_file+'[0]', "jpg:-"]
	fconvert = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = fconvert.communicate()
	assert fconvert.returncode == 0, stderr
	# now stdout is TIF image. let's load it with OpenCV
	filebytes = numpy.asarray(bytearray(stdout), dtype=numpy.uint8)
	return filebytes
	# 

if __name__ == '__main__':
	print ('testing')
	test = '/Users/jandevera/Desktop/x/pr.pdf'
	filebytes = pdf_preview_generator(test)
	import cv2
	image = cv2.imdecode(filebytes, cv2.IMREAD_GRAYSCALE)
	cv2.imshow('test',image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
