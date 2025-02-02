import os
import subprocess
import numpy
res = 72

def pdf_preview_generator(input_file,generate_marks,page):
	if page == 0:
		pass
	else:
		page = page - 1
	cmd = ["/usr/local/bin/convert", "-density", str(res), input_file+'['+str(page)+']', "jpg:-"]
	fconvert = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	stdout, stderr = fconvert.communicate()
	assert fconvert.returncode == 0, stderr
	filebytes = numpy.asarray(bytearray(stdout), dtype=numpy.uint8)
	return filebytes

if __name__ == '__main__':
	print ('testing')
	test = '/Users/xxx/Desktop/x/pr.pdf'
	filebytes = pdf_preview_generator(test,generate_marks=1,page=0)
	import cv2
	image = cv2.imdecode(filebytes, cv2.IMREAD_GRAYSCALE)
	cv2.imshow('test',image)
	cv2.waitKey(0)
	cv2.destroyAllWindows()
