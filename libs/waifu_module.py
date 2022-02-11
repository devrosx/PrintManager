#!/usr/bin/env python3
import os
import subprocess

def img_upscale(original_file, scale, denoise, imagetype):
	outputfiles = []
	for item in original_file:
		head, ext = os.path.splitext(item)
		outputfile = head+'_upscaled_'+'.png'
		print (outputfile)
		# check if waifu binary exist...
		if cmd_exists('waifu2x') == 1:
			print ('waifu found')
		else:
			print ('install https://github.com/nagadomi/waifu2x')
		command = ["waifu2x", "-t", imagetype, "-s", str(scale), "-n", str(denoise), "-i", str(item), "-o", str(outputfile)]
		fconvert = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		stdout, stderr = fconvert.communicate()
		outputfiles.append(outputfile)
	return command, outputfiles

def cmd_exists(cmd):
	return subprocess.call("type " + cmd, shell=True, 
		stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0

if __name__ == '__main__':
	filename = ['image.jpg']
	print (' '.join(filename))
	if os.path.isfile(str(' '.join(filename))) == 1:
		print ('file found')
		img_upscale(filename, 2, 0, 'a')
	else:
		print ('no file found')
	
