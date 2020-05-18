# PrintManager
PrintManager for Macosx (written in Python and PyQt5, with some handy features).  My goal is to create tool with usefull graphic/printing comandline functions. Patches and ideas are welcomed.

![alt text](https://raw.githubusercontent.com/devrosx/PrintManager/master/wiki/screenshot.png)

## Features
- Fast print PDF and image files from table (LP command)
- Debug text window with informations
- Preview window with page preview and detailed infotable
- Basic printing settings (format, collating, fit to page, twosided, number of copies)
- Basic pdf operations (split, merge, compress, view, rasterize,crop, ocr)
- PDF info in table (number of pages, colors, filesize, name, size)
- Convert various formats to PDF (OpenOffice and Cloudconvert supported)
- Extract images from PDF without resampling
- Simple winmail data extraction
- Basic image operations
 - OCR (thanks to pytesseract)
 - Convert to PDF
 - Resize image
 - Rotate
 - Identify images in image and extract (thanks to OpenCV)

# Installation
Use Pip3 to install these libraries: pytesseract, OpenCv(opencv-python-headless), PyPDF2, Pillow, Numpy, PyQt5, tnefparse, cloudconvert, beautifulsoup
Use Brew or other installer to install Ghostscript
to fix opencv and pyqt5 confict use:
pip uninstall opencv-contrib-python
pip install opencv-contrib-python-headless

 # Warning
Some features are experimental unfinished and buggy
I'm a newbie with python and PyQt5 :)

 # Todo
- Fix bugs
- Optimize code
- Interface polishing
- app bundle configuration (drag and drop on app icon)
- pdf and image rotations
- More image operations
- Finish print settings
- Support other platforms
- rewrite process to QProcess
- Rework pricing
- Support native printing presets (dont know if possible)
- ...

# Updates:
0.30
- added remove cropmarks from pdf files (works on multiple files at once all pagesizes are detected) :)
- fixed counting pages, preview image, merging image files on import
- preferences for alway on top (restart required)
- added select all for all items (ctr+A)
- fixed duplicates bug
- rotating files (pdf and image files works) in edit menu
- bugfixes in context menu and deleting from tab...
- added option to flatten transparency (convert to PDF 1.3 version)

0.29
- merge and split pdf is back
- added page selecter for preview panel and window
- big rewrite (something may not work)
- fixed extract image from PDF (CMYK/RGB)
- new compact menu
- cloudconvert should now finally work
- Find similar image (works on image search on google for visual similar images...) now even return picture name from google (beautifulsoup)
- added function to remove diacritics from filename (context menu)
- now you can open printer description (when you double click on printer name)
- added info how much pdf pages is selected

0.28
- Added OCR button (now supports PDF images and multiple files convert)
- Table sorting, fixed preview size height
- Drop files handling improved (you can now  drop multiple type files (jpg, doc, pdf together))

0.27
- Optional preview (commad+A) , should work on PDF and images with info like finder (with all atributes)
- rewrited preview
- supercrop isnt working
- cleaned code
- Fixes spaces in CloudConvert
- Fixed printing with (exmpty string bug)
- updates button states for image/ pdf files
- added grayscale for images support
- imroved preview detail

0.26
- Big feature # SuperCrop
  How it works: (file is converted to JPG saved to TMP folder (you can specify witch page tu use (not in gui yet) to crop rest pages or crop all pages individualy, then opencv detect image border and use it as crop region in PDF)
  This module requires Numpy and OpenCV. Added simple gui
- Rastering and compresing setting works again on multiple selection
- Added To Gray (convert pdf to grayscale...)
- Bugfixes in superCrop
- Fixes in printing and support for original size as paper size (paper size dropbox)

0.25
- removed predefined filepath (file is saved in current directory, custom directory will be added later)
- you can now import text files or images files with merge function - one PDF from multiple files is created (cloudconvert and OpenOffice is supported)
- basic platform detection (preparing for other platforms support)
- better drag and drop
- Window is always on TOP
- Fixed window bar on new macOS
- Added detailed info generated in tab (Info button) image and PDF files are supported
- Note: delete item in list is buggu after drop another file deleted file appears again (have to find bug)
- Experimental support for all clouconvert supported files https://cloudconvert.com/pdf-converter (like EPS, CDR, HEIC, PSD etc...)

0.24
- Rewrited debug output, red color errors, green main info...
- new preferences panel (curently you can change OCR language and rastering resoltion, cloudconvert it WIP)
- Cloudconvert support
- Added API_KEY and error handling for Cloudconvert


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

