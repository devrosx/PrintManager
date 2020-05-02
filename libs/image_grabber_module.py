#!/usr/bin/env python3
import requests
import webbrowser

def find_this_file(filename, *args):
	for items in filename:
		searchUrl = 'http://www.google.com/searchbyimage/upload'
		multipart = {'encoded_image': (items, open(items, 'rb')), 'image_content': ''}
		response = requests.post(searchUrl, files=multipart, allow_redirects=False)
		fetchUrl = response.headers['Location']
		webbrowser.open(fetchUrl)
	debugstring = None
	outputfiles = None 
	return debugstring, outputfiles

if __name__ == '__main__':
	filePath = '/Users/jandevera/Desktop/X/test.jpg'
	find_this_file(filePath)
