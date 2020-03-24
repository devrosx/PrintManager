# PrintManager
PrintManager for Macosx (written in Python and Pyqt5, with some handy features).  My goal is to create tool with usefull graphic/printing comandline functions. Patches and ideas are welcomed.

![alt text](https://raw.githubusercontent.com/devrosx/PrintManager/master/wiki/screenshot.png)

## Features
- Print PDF files from table (LP command)
- Debug text window with informations
- Basic printing settings (format, collating, fit to page, twosided, number of copies)
- Basic pdf operations (split, merge, compress, view, rasterize)
- PDF info in table (number of pages, colors, filesize, name, size)
- Convert various formats to PDF (currenty using OpenOffice convertor)
- Extract images from PDF without resampling
- Simple winmail dat extraction
- Basic image operations
 - OCR (thanks to pytesseract)
 - Convert to PDF
 - Resize image
 - Identify images in image and extract (thanks to OpenCV)

# Installation
Use Pip3 to install these libraries
pytesseract, OpenCv(opencv-python-headless), PyPDF2, Pillow, Numpy, PyQt5, tnefparse
Use Brew or other installer to install Ghostscript

 # Warning
Some features are experimental unfinished and buggy
I'm a newbie with python and PyQt5 :)

 # Todo
- Fix bugs
- Interface polishing
~~- Preferences panel~~
~~- CloudConvert api support (as alternative to OpenOffice)~~
~~- support fileformat icons~~
- better file and drag and drop highligting
- app bundle configuration
- drag and drop on app icon
- More image operations
- Localizations..
- Finish print settings
 - Grayscale/color switch
- ...

# Updates:
0.24
- new preferences panel (curently you can change OCR language and rastering resoltion, cloudconvert it WIP)
- Cloudconvert support
0.21
- Fixed icons (pdf and image files) and better text aling in table
- Debug box (Command+D) and print setting box (Command+P) can be set hiden now...
- Added preview fucntion (F1 key) and contextual menu
- New Drag and drop indicators
- New function to extract individual images from PDF file
- Adeded simple resize function for images
- Contextual menu fix
- Added support for winmail dat encoding (tnefparse)
- Added pdfextract module for extracting images from PDF (untested, more https://stackoverflow.com/questions/2693820/extract-images-from-pdf-without-resampling-in-python)

