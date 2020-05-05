#!/usr/bin/env python3
import requests
import webbrowser
from bs4 import BeautifulSoup
headers_Get = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:49.0) Gecko/20100101 Firefox/49.0',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }


def find_this_file(filename, *args):
	debugstring = []
	for items in filename:
		searchUrl = 'http://www.google.com/searchbyimage/upload'
		multipart = {'encoded_image': (items, open(items, 'rb')), 'image_content': ''}
		response = requests.post(searchUrl, files=multipart, allow_redirects=False)
		fetchUrl = response.headers['Location']
		webbrowser.open(fetchUrl)
		input_url = requests.get(fetchUrl, headers=headers_Get)
		img_name = getname(input_url)
		debugstring.append(img_name)
	# debugstring = None
	outputfiles = None 
	return debugstring, outputfiles

def getname(input_url):
	soup = BeautifulSoup(input_url.text, "html.parser")
	output = []
	# print (soup.prettify())
	elements = soup.findAll('input')
	# print (elements)
	for link in elements:
		output.append(link.get('value'))
	# print (output[-2])
	return output[-2]

if __name__ == '__main__':
	filePath = ['/Users/jandevera/Desktop/sc.png']
	debugstring, outputfiles, imagename = find_this_file(filePath)
	print (imagename)
