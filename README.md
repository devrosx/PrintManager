# PrintManager
PrintManager for Macosx (written in Python and Pyqt5, with some handy features)

![alt text](https://raw.githubusercontent.com/devrosx/PrintManager/master/wiki/screenshot.png)

## Features
- Print PDF files from table (LP command)
- Debug text window with informations
- Basic printing settings (format, collating, fit to page, twosided, number of copies)
- Basic pdf operations (split, merge, compress, view, rasterize)
- PDF info in table (number of pages, colors, filesize, name, size)
- Convert various formats to PDF (currenty using OpenOffice convertor)
- Basic image operations
 - OCR (thanks to pytesseract)
 - Convert to PDF
 - Resize image
 - Identify images in image and extract (thanks to OpenCV)

# Installation
Use Pip3 to install these libraries
pytesseract, OpenCv(opencv-python-headless), PyPDF2, Pillow, Numpy, PyQt5.
Use Brew or other installer to install Ghostscript

 # Warning
Some features are experimental unfinished and buggy
I'm a newbie with python and PyQt5 :)
