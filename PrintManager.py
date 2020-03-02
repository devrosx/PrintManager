#!/usr/bin/env python3
import sys
import os
import subprocess
import json
from PyPDF2 import PdfFileReader, PdfFileMerger, PdfFileWriter
# from PyQt5.QtWidgets import QHBoxLayout,QTableWidget,QWidget,QApplication,QGridLayout,QGroupBox,QVBoxLayout,QListWidget,QSpinBox,QComboBox,QCheckBox,QPushButton, QTextEdit, QAbstractItemView, QTableWidgetItem
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDropEvent, QKeySequence, QPalette, QColor, QIcon, QPixmap, QBrush, QPainter, QFont, QCursor
from PyQt5.QtCore import *
from libs.colordetector import *
from libs.ocr_module import ocr_core
from libs.crop_module import processFile

version = '0.20'
# Eng localization
# BASIC OCR SUPPORT (jpg png tif bmp)
# pytesseract
# resize
# smart cut for images
# https://github.com/mstamy2/PyPDF2/issues/51
import time
start_time = time.time()

mm = '0.3527777778'
office_ext = ['csv', 'db', 'odt', 'doc', 'gif', 'pcx', 'docx', 'dotx', 'fodp', 'fods', 'fodt', 'odb', 'odf', 'odg', 'odm', 'odp', 'ods', 'otg', 'otp', 'ots', 'ott', 'oxt', 'pptx', 'psw', 'sda', 'sdc', 'sdd', 'sdp', 'sdw', 'slk', 'smf', 'stc', 'std', 'sti', 'stw', 'sxc', 'sxg', 'sxi', 'sxm', 'sxw', 'uof', 'uop', 'uos', 'uot', 'vsd', 'vsdx', 'wdb', 'wps', 'wri', 'xls', 'xlsx']
image_ext = ['jpg', 'jpeg', 'png', 'tif', 'bmp']
info = []
name = []
size = []
extension = []
file_size = []
pages = []
price = []
colors = []
filepath = []
papers = ['A4', 'A5', 'A3', '480x320', '450x320', 'original']
username = os.getlogin()

# PREFERENCES BASIC
def save_preferences(*settings):
	print ('JSON save on exit')
	preferences = []
	for items in settings:
		preferences.append(items)
	with open('config.json', 'w', encoding='utf-8') as data_file:
		json.dump(preferences, data_file)
	startup = 1
	return startup

def load_preferences():
	print ('JSON load on boot')
	try:
		with open('config.json', encoding='utf-8') as data_file:
			json_pref = json.loads(data_file.read())
	except:
		print ('json loading error')
		json_pref = [["tiskarna", 1]]
		print (type(json_pref))
	return json_pref

def humansize(size):
	filesize = ('%.1f' % float(size/1000000) + 'MB')
	return filesize

def openfile(list_path):
	if isinstance (list_path, list):
		for items in list_path:
			subprocess.call(['open', items]) # open converted
	else:
		subprocess.call(['open', list_path]) # open converted

def open_printer(file):
	subprocess.call(['subl', '/private/etc/cups/ppd/'+file+'.ppd']) # open converted

def revealfile(list_path):
	if isinstance (list_path, list):
		# print ('Input is list :)' + str(list_path))
		for items in list_path:
			subprocess.call(['open', '-R', items]) # open converted
			print (['open', '-R', items])
	else:
		subprocess.call(['open', '-R', list_path]) # open converted
		print (['open', '-R', list_path])

def mergefiles(list_path):
	print ('Merge file')
	head, ext = os.path.splitext(list_path[0])
	outputfile = head + '_m' + ext
	merger = PdfFileMerger()
	for pdf in list_path:
		merger.append(pdf)
	merger.write(outputfile)
	merger.close()
	return outputfile

def splitfiles(file):
	print ('Split file')
	outputfiles = []
	pdf_file = open(file,'rb')
	pdf_reader = PdfFileReader(file)
	pageNumbers = pdf_reader.getNumPages()
	head, ext = os.path.splitext(file)
	outputfile = head + 's_'
	for i in range (pageNumbers):
		pdf_writer = PdfFileWriter()
		pdf_writer.addPage(pdf_reader.getPage(i))
		outputpaths = outputfile + str(i+1) + '.pdf'
		split_motive = open(outputfile + str(i+1) + '.pdf','wb')
		outputfiles.append(outputpaths)
		pdf_writer.write(split_motive)
		split_motive.close()
	pdf_file.close()
	return outputfiles

def resizeimage(original_file, percent):
	# outputfiles = []
	head, ext = os.path.splitext(original_file)
	outputfile = head + '_' + str(percent) + ext
	command = ["convert", original_file, "-resize", str(percent)+'%', outputfile]
	subprocess.run(command)
	# outputfiles.append(outputfile)
	return command, outputfile

def compres_this_file(original_file):
	outputfiles = []
	head, ext = os.path.splitext(original_file)
	outputfile = head + '_c' + ext
	command = ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4", "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-sOutputFile="+outputfile, original_file]
	subprocess.run(command)
	outputfiles.append(outputfile)
	return command, outputfiles

def raster_this_file(original_file):
	outputfiles = []
	head, ext = os.path.splitext(original_file)
	outputfile = head + '_raster' + ext
	command_gs = ["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dNOCACHE", "-sDEVICE=pdfwrite", "-sColorConversionStrategy=/LeaveColorUnchanged", "-dAutoFilterColorImages=true", "-dAutoFilterGrayImages=true", "-dDownsampleMonoImages=true", "-dDownsampleGrayImages=true", "-dDownsampleColorImages=true", "-sOutputFile="+outputfile, original_file]
	command = ["convert", "-density",  "300", "+antialias", str(original_file), str(outputfile)]
	# command = ["pdf2ps", original_file]
	# cmd = "pdf2ps " +  str(original_file) + " - | ps2pdf - " + str(outputfile)
	# ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
	# output = ps.communicate()[0]
	# print(output)
	subprocess.run(command)
	outputfiles.append(outputfile)
	return command, outputfiles

def print_this_file(print_file, printer, lp_two_sided, orientation, copies, p_size, fit_to_size, collate):
	# https://www.cups.org/doc/options.html
	# COLATE
	if collate == 1:
		print ('collate ON')
		_collate =  ('-o collate=true')
	else: 
		print ('collate OFF')
		_collate = ('-o collate=false')
	# PAPER SHRINK
	if fit_to_size == 1:
		# print ('fit_to_size ON')
		fit_to_size =  ('-o fit-to-page')
	else: 
		# fix cant be null or empty
		# print ('fit_to_size OFF ')
		fit_to_size = ('-o job-priority=10')
	# PAPER SIZE WIP
	if p_size == 'A4':
		p_size_ = ('-o media=A4')
	if p_size == 'A3':
		p_size_ = ('-o media=A3')
	if p_size == 'A5':
		p_size_ = ('-o media=A5')
	if p_size == '480x320':
		p_size_ = ('-o media=480x320')
	if p_size == '450x320':
		p_size_ = ('-o media=450x320')
	if p_size_ == ('original'):
		p_size_ = ('-o media=XXXX')
	# na canonu nefunguje pocet kopii... vyhodit -o sides=one-sided
	if lp_two_sided == 1:
		# print ('two sided')
		lp_two_sided_ = ('-o sides=two-sided')
		if orientation == 1:
			lp_two_sided_ = ('-o sides=two-sided-long-edge')
		else:
			lp_two_sided_ = ('-o sides=two-sided-short-edge')
	else:
		lp_two_sided_ = ('-o sides=one-sided')
	# if isinstance (print_file, list):
	for printitems in print_file:
		# subprocess.run("lp", "-d", printer + str(print_file[0]) + lp_two_sided_ + p_size_ + fit_to_size + _collate + "-n=" + copies)
		command = ["lp", "-d", printer, printitems, "-n" + copies, lp_two_sided_, p_size_, fit_to_size, _collate]
		subprocess.run(command)
		print (username)
		# window.update_Debug_list(str(debugstring))
	try:
		subprocess.run(["open", "/Users/" + username + "/Library/Printers/" + str(printer) + ".app"])
	except:
		print ('printer not found')
	return command

# extract printer info as list for preferences only
def load_printers(): 
	output = (subprocess.check_output(["lpstat", "-a"]))
	outputlist = (output.splitlines())
	tolist = [] # novy list
	for num in outputlist:  # prochazeni listem
		first, *middle, last = num.split()
		tiskarna = str(first.decode())
		tolist.append(tiskarna)
	return (tolist)
printers = load_printers()

argy = []
def basic_parse(inputs, *args):
	for item in inputs:
		# print (item)
		oldfilename = (os.path.basename(item))
		ext_file = os.path.splitext(oldfilename)
		dirname = (os.path.dirname(item) + '/')
		with open(item, mode='rb') as f:
			pdf_input = PdfFileReader(f, strict=False)
			if pdf_input.isEncrypted:
				print ('encrypted...')
				d_info = '<font color=red>Encrypted PDF</font>'
				break
			else:
				qsizedoc = (pdf_input.getPage(0).mediaBox)
				sirka = (float(qsizedoc[2]) * float(mm))
				vyska = (float(qsizedoc[3]) * float(mm))
				page_size = (str(round(sirka)) + 'x' + str(round(vyska)) + 'mm')
				pdf_pages = pdf_input.getNumPages()
				velikost = size_check(page_size)
				newfilename = ('[' + str(round(sirka)) + 'x' + str(round(vyska)) + 'mm_' + str(pdf_pages) + 'str]' + oldfilename)
				name.append(ext_file[0])
				size.append(size_check(page_size))
				price.append(price_check(pdf_pages, velikost))
				file_size.append(humansize(os.path.getsize(item)))
				pages.append(int(pdf_pages))
				filepath.append(item)
				info.append('')
				colors.append('')
				extension.append(ext_file[1][1:])
				d_info = 'All ok'
	rows = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
	return rows, d_info

def getimageinfo (filename):
	output = (subprocess.check_output(["identify", filename]))
	outputlist = (output.splitlines())
	getimageinfo = []
	for num in outputlist:  # prochazeni listem
		first, *middle, last = num.split()
		getimageinfo.append(str(middle[1].decode()) + ' pixels')
		getimageinfo.append(str(middle[4].decode()))
	return getimageinfo
	
def basic_parse_image(inputs, *args):
	for item in inputs:
		oldfilename = (os.path.basename(item))
		filesize = humansize(os.path.getsize(item))
		ext_file = os.path.splitext(oldfilename)
		dirname = (os.path.dirname(item) + '/')
		info.append('')
		image_info = getimageinfo(item)
		name.append(ext_file[0])
		size.append(str(image_info[0]))
		extension.append(ext_file[1][1:])
		file_size.append(humansize(os.path.getsize(item)))
		pages.append(1)
		price.append('')
		colors.append(str(image_info[1]))
		filepath.append(item)
		d_info = 'All ok'
	rows = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
	return rows, d_info


def size_check(page_size):
	velikost = 0
	if page_size == '210x297mm':
		velikost = 'A4'
	elif page_size == '420x297mm':
		velikost = 'A3'
	elif page_size == '148x210mm':
		velikost = 'A5'
	elif page_size == '420x594mm':
		velikost = 'A2'
	elif page_size == '594x841mm':
		velikost = 'A1'
	elif page_size == '841x1188mm':
		velikost = 'A0'
	else:
		velikost = page_size
	return velikost

def price_check(pages, velikost):
	price = []
	if velikost == 'A4':
		if pages >= 50:
			pricesum = (str(pages * 1.5) + ' Kč')
		elif pages >= 20:
			pricesum = (str(pages * 2) + ' Kč')
		elif pages >= 0:
			pricesum = (str(pages * 3) + ' Kč')
	elif velikost == 'A3':
		if pages >= 50:
			pricesum = (str(pages * 2) + ' Kč')
		elif pages >= 20:
			pricesum = (str(pages * 3) + ' Kč')
		elif pages >= 0:
			pricesum = (str(pages * 4) + ' Kč')
	else:
		pricesum = '/'
	return pricesum

class ImgWidget1(QLabel):
	def __init__(self, parent=None):
		super(ImgWidget1, self).__init__(parent)
		imagePath = "icons/pdf.png"
		pic = QPixmap(imagePath)
		self.setPixmap(pic)

class Customdialog(QDialog):
	def __init__(self):
		super(RegisterPage, self).__init__()
		loadUi('RegisterPage.ui', self)

# GUISTUFF
def darkmode():
	app.setStyle("Fusion")
	palette = QPalette()
	palette.setColor(QPalette.Window, QColor(53, 53, 53))
	palette.setColor(QPalette.WindowText, Qt.white)
	palette.setColor(QPalette.Base, QColor(25, 25, 25))
	palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
	palette.setColor(QPalette.ToolTipBase, Qt.white)
	palette.setColor(QPalette.ToolTipText, Qt.white)
	palette.setColor(QPalette.Text, Qt.white)
	palette.setColor(QPalette.Button, QColor(53, 53, 53))
	palette.setColor(QPalette.ButtonText, Qt.white)
	palette.setColor(QPalette.BrightText, Qt.red)
	palette.setColor(QPalette.Link, QColor(42, 130, 218))
	palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
	palette.setColor(QPalette.HighlightedText, Qt.black)
	app.setPalette(palette)

class TableWidgetDragRows(QTableWidget):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setAcceptDrops(True)
		self.viewport().setAcceptDrops(True)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setSelectionBehavior(QAbstractItemView.SelectRows)
		self.setEditTriggers(QAbstractItemView.NoEditTriggers)

class InputDialog(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.first = QSpinBox(self)
		self.first.setRange(1, 50)
		self.first.setValue(1)
		self.second = QSpinBox(self)
		self.second.setRange(1, 255)
		self.second.setValue(220)
		buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self);
		layout = QFormLayout(self)
		layout.addRow("Number of images", self.first)
		layout.addRow("Treshold", self.second)
		layout.addWidget(buttonBox)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)

	def getInputs(self):
		return (self.first.text(), self.second.text())

class Window(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)
		# Create menu options
		menubar = self.menuBar()
		menu = QMenu('File', self) # title and parent
		open_action = QAction("Open file", self) # title and parent
		open_action.triggered.connect(self.openFileNamesDialog)
		open_action.setShortcut('Ctrl+O')
		close_action = QAction(' &Exit', self)
		close_action.triggered.connect(self.close)
		menu.addAction(open_action)
		menu.addAction(close_action)
		menubar.addMenu(menu)

		self.central_widget = QWidget()               # define central widget
		self.setCentralWidget(self.central_widget)    # set QMainWindow.centralWidget
		self.mainLayout = QGridLayout()
		self.centralWidget().setLayout(self.mainLayout)
		self.createTop_layout()
		self.createDebug_layout()
		self.createExtra_layout()
		# load files to tab...
		# rows = basic_parse(argy)
		rows = []
		# print (rows)
		# print (type(rows))
		self.table_reload(rows)

		self.mainLayout.addLayout(self.top_layout, 0,0)
		self.mainLayout.addLayout(self.debug_layout, 2, 0)
		self.mainLayout.addLayout(self.extra_layout, 3, 0)

		self.setAcceptDrops(True)
		self.resize(638, 600)
		self.setFixedSize(self.size())
		self.setWindowTitle("PrintManager " + version)



	def closeEvent(self, event):
		preferences = []
		if self.printer_table.currentItem() != None:
			preferences.append('tiskarna')
			preferences.append(self.printer_table.currentRow())
		save_preferences(preferences)
		close = QMessageBox()
		close.setText("You sure?")
		close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
		close = close.exec()
		if close == QMessageBox.Yes:
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		items = ["to PDF", "SmartCut", "OCR", "Resize"]
		# print ('Drop event')
		for url in event.mimeData().urls():
			soubor = (url.toLocalFile())
			extension = os.path.splitext(soubor)[1][1:].lower()
			if extension == 'pdf':
				soubor = []
				for url in event.mimeData().urls():
					file = (url.toLocalFile())
					soubor.append(file)
				try:	
					files, d_info = basic_parse(soubor)
				except:
					QMessageBox.about(self, "Warning", "File " + str(file) + " import error")
					break
				self.debuglist.setText(d_info)
				rows = files
				Window.table_reload(self, rows)
				break
			elif extension in office_ext:
				soubor = []
				self.debuglist.setText("Converting to PDF:" + extension)
				for url in event.mimeData().urls():
					file = (url.toLocalFile())
					soubor.append(file)
				files = self.external_convert(extension, soubor)
				break
			# for images.... 
			elif extension in image_ext :
				soubor = []
				self.debuglist.setText("File:" + extension)
				for url in event.mimeData().urls():
					file = (url.toLocalFile())
					soubor.append(file)
				text, ok = QInputDialog.getItem(self, "Action", "Action", items, 0, False)
				if not ok:
					break
				if text == 'to PDF':
					files = self.external_convert(extension, soubor)
				if text == 'OCR':
					ocr_output = []
					for items in soubor:
						ocr = ocr_core(items, 'ces')
						ocr_output.append(ocr)
					# print ('pocet je' + str(len(ocr_output)))
					ocr_output =  ''.join(ocr_output)
					self.update_Debug_list(ocr_output)
				if text == 'SmartCut':
					smartcut_files = []
					dialog = InputDialog()
					if dialog.exec():
						n_images, tresh = dialog.getInputs()
					for items in soubor:
						outputfiles = processFile(items, n_images, tresh)
						# print ('takle to vypada outputfiles' + str(outputfiles))
						smartcut_files.append(outputfiles)
					# merge lists inside lists 
					smartcut_files = [j for i in smartcut_files for j in i]
					files, d_info = basic_parse_image(smartcut_files)
					rows = files
					Window.table_reload(self, rows)
					self.update_Debug_list(str(smartcut_files))
				if text == 'Resize':
					resize_files = []
					percent,ok = QInputDialog.getInt(self,"Resize image","Enter a percent", 50, 1, 100)
					# if ok:
	 #     				self.le2.setText(str(num))
					for items in soubor:
						command, outputfiles = resizeimage(items, percent)
						resize_files.append(outputfiles)
					files, d_info = basic_parse_image(resize_files)
					rows = files
					Window.table_reload(self, rows)
					self.update_Debug_list(str(resize_files))
				break
			else:
				QMessageBox.about(self, "Warning", "One of files isnt supported:" + extension)
				break

	def update_Debug_list(self, command):
		if isinstance (command, list):
			if len(command) == 1:
				command = (' '.join('\n'.join(elems) for elems in command))
			else:
				command = ' '.join(command)
				# print (command)
				if command[0] != '/':
					(firstWord, rest) = command.split(maxsplit=1)
					command = ('<font color=red><b>' + firstWord + '</b></font> ' + rest)
		self.debuglist.append(str(command))

	# for pretty debug output
	def splitlinesdebug(self, conv_output):
		outputlist = (conv_output.splitlines())
		outputlist = str(outputlist[0])
		# print (outputlist)
		for char in outputlist:
			if char in "b'":
					outputlist = outputlist.replace(char,'')
		self.update_Debug_list(str(outputlist))

	def external_convert(self, ext, inputfile):
		outputdir = "/Users/jandevera/pc/"
		converts = []
		for items in inputfile:
			conv_output = (subprocess.check_output(["/Applications/LibreOffice.app/Contents/MacOS/soffice", "--headless", "--convert-to", "pdf", items,"--outdir", outputdir]))
			self.splitlinesdebug(conv_output)
			base = os.path.basename(items)
			base = os.path.splitext(base)[0]
			new_file = outputdir + base + '.pdf'
			converts.append(new_file)
			# import converted
		files, d_info = basic_parse(converts)
		rows = files
		# print (rows)
		self.table.setCellWidget(0, 0, ImgWidget1(self))
		# if_fixed = len(inputfile)+1
		# HACK FOR NEW FILES LIST ICONS
		# if_fixed = len(inputfile)+1
		# # print ('if:' + str(len(inputfile)))
		# # print ('rows:' + str(len(rows)))
		# for i in range(if_fixed,len(rows)-if_fixed,-1):
		# 	self.insert_icon(QStyle.SP_FileIcon, 0, i)
		# Window.table_reload(self, rows)
		# for i in range(if_fixed,len(rows)-if_fixed,-1):
		# 	print (i)
		# 	self.icon_row(QStyle.SP_FileIcon, 0, i)
		Window.table_reload(self, rows)

	def icon_row(self, nameicon, colum_number, row):
		self.table.setCellWidget(row, colum_number, ImgWidget1(self))




# FIX THIS
	def insert_icon(self, nameicon, colum_number, row):
			print ('eeeekl')
			desktop_icon = QIcon(QApplication.style().standardIcon(nameicon))
			# print (rows)


	def table_reload(self, inputfile):
		# if debug == 1:
		# print ('Tabulka=' + str(inputfile))
		# print (len(inputfile))
		# self.table.setContextMenuPolicy(Qt.CustomContextMenu)
		self.table = TableWidgetDragRows()
		headers = ["Info", "File", "Size", "Kind", "Filesize", "Pages", "Price", "Colors", 'Filepath']
		self.table.setColumnCount(len(headers))
		self.table.setHorizontalHeaderLabels(headers)
		self.table.doubleClicked.connect(self.open_table)
		self.table.setColumnWidth(0, 25)
		self.table.setColumnWidth(1, 230)
		self.table.setColumnWidth(3, 35)
		self.table.setColumnWidth(4, 70)
		self.table.setColumnWidth(5, 35)
		self.table.setColumnWidth(6, 55)
		self.table.setColumnWidth(7, 64)
		self.table.verticalHeader().setVisible(False)
		self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		# icon wip
		pic = QPixmap("icons/pdf.png")
		self.label = QLabel()
		self.label.setPixmap(pic)

		self.table.setRowCount(len(inputfile))
		for i, (Info, File, Size, Kind, Filesize, Pages, Price, Colors, Filepath) in enumerate(inputfile):
			# print (i)
			# self.table.setCellWidget(i, 0, self.label)
			self.table.setItem(i, 1, QTableWidgetItem(File))
			self.table.setItem(i, 2, QTableWidgetItem(Size))
			self.table.setItem(i, 3, QTableWidgetItem(Kind))
			self.table.setItem(i, 4, QTableWidgetItem(Filesize))
			self.table.setItem(i, 5, QTableWidgetItem(str(Pages)))
			self.table.setItem(i, 6, QTableWidgetItem(Price))
			self.table.setItem(i, 7, QTableWidgetItem(Colors))
			self.table.setItem(i, 8, QTableWidgetItem(Filepath))
		self.table.setColumnHidden(8, True)
		# RIGHT CLICK MENU
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.contextMenuEvent)	 	
		self.mainLayout.addWidget(self.table,1,0)
		self.update()

	def dragEnterEvent(self, event):
		p = self.mapFromGlobal(QCursor().pos())
		# print (p)
		# it = self.table(p)
		# self.table.horizontalHeaderItem(0).setBackgroundColor(QColor(255,100,0,255))
		print ('drag event')
		if event.mimeData().hasUrls():
			event.accept()
			self.debuglist.setText('loading files, please wait....')

	def contextMenuEvent(self, pos):
			if self.table.selectionModel().selection().indexes():
					for i in self.table.selectionModel().selection().indexes():
							row, column = i.row(), i.column()
					menu = QMenu()
					openAction = menu.addAction('Open')
					revealAction = menu.addAction('Reveal in finder')
					printAction = menu.addAction('Print')
					action = menu.exec_(self.mapToGlobal(pos))
					if action == openAction:
						index=(self.table.selectionModel().currentIndex())
						row = self.table.currentRow()
						cesta_souboru=index.sibling(row,8).data()
						openfile(cesta_souboru)
					if action == revealAction:
						index=(self.table.selectionModel().currentIndex())
						row = self.table.currentRow()
						cesta_souboru=index.sibling(row,8).data()
						revealfile(cesta_souboru)
					if action == printAction:
						index=(self.table.selectionModel().currentIndex())
						row = self.table.currentRow()
						cesta_souboru=index.sibling(row,8).data()
						self.table_print()

	def createDebug_layout(self):
		self.debug_layout = QHBoxLayout()
		# debug
		self.debuglist = QTextEdit("<b>Debug:</b>", self)
		self.debuglist.setAlignment(Qt.AlignJustify)
		self.debuglist.acceptRichText()
		self.debuglist.setReadOnly(1)
		self.debuglist.setFixedHeight(90)
		self.debug_layout.addWidget(self.debuglist)

	def createExtra_layout(self):
		self.extra_layout = QHBoxLayout()
		# OPEN FILES
		self.qbtn_open = QPushButton('Open', self)
		self.qbtn_open.clicked.connect(self.openFileNamesDialog)
		self.extra_layout.addWidget(self.qbtn_open)
		# LOAD COLORS INFO
		self.qbtn_color = QPushButton('Colors', self)
		self.qbtn_color.clicked.connect(self.loadcolors)
		self.extra_layout.addWidget(self.qbtn_color)
		# SPOJ PDF
		self.combine_pdf_b = QPushButton('Join', self)
		self.combine_pdf_b.clicked.connect(self.combine_pdf)
		self.extra_layout.addWidget(self.combine_pdf_b)
		# ROZDEL PDF
		self.split_pdf_b = QPushButton('Split', self)
		self.split_pdf_b.clicked.connect(self.split_pdf)
		self.extra_layout.addWidget(self.split_pdf_b)
		# COMPRES PDF
		self.compres_pdf_b = QPushButton('Compres', self)
		self.compres_pdf_b.clicked.connect(self.compres_pdf)
		self.extra_layout.addWidget(self.compres_pdf_b)
		# RASTROVANI PDF
		self.raster_b = QPushButton('Rastering', self)
		self.raster_b.clicked.connect(self.rasterize_pdf)
		self.extra_layout.addWidget(self.raster_b)
		# POCITANI TABULKY PDF
		self.count_b = QPushButton('Count', self)
		self.count_b.clicked.connect(self.count_table)
		self.extra_layout.addWidget(self.count_b)

		# # SPACE
		self.labl = QLabel()
		self.labl.setText(version)
		self.labl.setAlignment(Qt.AlignCenter)
		self.labl.setFixedSize(50, 10)
		self.extra_layout.addWidget(self.labl)

		# # EXIT SCRIPT
		# self.qbtn_exit = QPushButton('Konec', self)
		# self.qbtn_exit.clicked.connect(QCoreApplication.instance().quit)
		# self.extra_layout.addWidget(self.qbtn_exit)
		# # # PRINT SCRIPT
		self.qbtn_print = QPushButton('Print', self)
		self.qbtn_print.clicked.connect(self.table_print)
		self.extra_layout.addWidget(self.qbtn_print)

	def compres_pdf(self):
		print ('PDF compress WIP')
		# green_ = (QColor(80, 80, 80))
		# black_ = (QBrush(QColor(0, 0, 0)))
		outputfiles = []
		if self.table.currentItem() == None:
			QMessageBox.information(self, 'Error', 'No files selected', QMessageBox.Ok)
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			# self.table.setItemDelegateForColumn(0, self.delegate)
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
			# print ('toto je row:' + str(row))
			desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DialogResetButton))
			# self.table.item(0, row).setIcon(desktop_icon)
			# self.insert_icon(QStyle.SP_DialogResetButton, 0, row)
		# print (outputfiles)
		debugstring, outputfiles = compres_this_file(cesta_souboru)
		files, d_info = basic_parse(outputfiles)
		rows = files
		Window.table_reload(self, rows)
		# print (debugstring)
		self.update_Debug_list(debugstring)

	def rasterize_pdf(self):
		print ('PDF rasterzie WIP')
		outputfiles = []
		if self.table.currentItem() == None:
			QMessageBox.information(self, 'Error', 'No files selected', QMessageBox.Ok)
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			# self.table.setItemDelegateForColumn(0, self.delegate)
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
			# print ('toto je row:' + str(row))
			desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DialogResetButton))
			# self.table.item(0, row).setIcon(desktop_icon)
			# self.insert_icon(QStyle.SP_DialogResetButton, 0, row)
		# print (outputfiles)
		debugstring, outputfiles = raster_this_file(cesta_souboru)
		files, d_info = basic_parse(outputfiles)
		rows = files
		Window.table_reload(self, rows)
		self.update_Debug_list(str(debugstring))

	def count_table(self):
		print ('PDF counting')
		soucet = []
		stranky = []
		for items in sorted(self.table.selectionModel().selectedRows()):
			# self.table.setItemDelegateForColumn(0, self.delegate)
			row = items.row()
			soucet.append(row)
			index=(self.table.selectionModel().currentIndex())
			info=index.sibling(items.row(),5).data()
			stranky.append(int(info))
			# outputfiles.append(cesta_souboru)
			# print ('toto je row:' + str(row))
			# desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DialogResetButton))
		celkem = (str(len(soucet)) + '  PDF files, number of pages ' + str(sum(stranky)))
		self.update_Debug_list(celkem)

	def split_pdf(self):
		green_ = (QColor(10, 200, 50))
		print ('Split pdf')
		# combinefiles = []
		# merged_pdf_list = []
		for items in sorted(self.table.selectionModel().selectedRows()):
			index=(self.table.selectionModel().currentIndex())
			row = items.row()
			if int(index.sibling(items.row(),5).data()) < 2:
				QMessageBox.information(self, 'Error', 'Not enough files to split', QMessageBox.Ok)
			else:
				index=(self.table.selectionModel().currentIndex())
				cesta_souboru=index.sibling(items.row(),8).data()
				split_pdf = splitfiles(cesta_souboru)
				files, d_info = basic_parse(split_pdf)
				self.update_Debug_list(split_pdf)
				rows = files
				Window.table_reload(self, rows)
				# self.table.item((len(rows)-1), 1).setForeground(green_)
				# self.insert_icon(QStyle.SP_DialogOpenButton, 0, (len(rows)-1))

	def combine_pdf(self):
		green_ = (QColor(10, 200, 50))
		merged_pdf_list = []
		table = sorted(self.table.selectionModel().selectedRows())
		if len(table) <= 1:
			QMessageBox.information(self, 'Error', 'Choose two or more files to combine PDFs. At least two files....', QMessageBox.Ok)
		else:
			for items in table:
				row = items.row()
				print (row)
				index=(self.table.selectionModel().currentIndex())
				cesta_souboru=index.sibling(items.row(),8).data()
				combinefiles.append(cesta_souboru)
			merged_pdf = mergefiles(combinefiles)
			self.update_Debug_list('New combined PDF created: ' + merged_pdf)
			merged_pdf_list.append(merged_pdf)
			files, d_info = basic_parse(merged_pdf_list)
			rows = files
			Window.table_reload(self, rows)
			# self.table.item((len(rows)-1), 1).setForeground(green_)
			# self.insert_icon(QStyle.SP_DialogOpenButton, 0, (len(rows)-1))

	def loadcolors(self):
		green_ = (QColor(10, 200, 50))
		black_ = (QBrush(QColor(200, 200, 200)))
				# widgetText =  QLabel('<font color="cyan">C</font><font color="magenta">M</font><font color="yellow">Y</font><font color="white">K</font>')
		outputfiles = []
		font = QFont()
		font.setBold(True)
		if self.table.currentItem() == None:
			QMessageBox.information(self, 'Error', 'Choose files to convert', QMessageBox.Ok)
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
			 # self.debuglist.setText(str(outputfiles))
			for items in outputfiles:
				nc = count_page_types(items)
				if not nc:
					print ('gray')
					self.table.item(row, 7).setText('BLACK')
					self.table.item(row, 7).setForeground(black_)
					self.debuglist.setText('Document is in grayscale')
					self.table.item(row, 7).setFont(font)
					self.table.clearSelection()
				else:
					self.table.item(row, 7).setText('CMYK')
					self.table.item(row, 7).setForeground(green_)
					self.table.item(row, 7).setFont(font)
					self.update_Debug_list('Color pages: ' +  ', '.join(map(str, nc)))
					self.table.clearSelection()

	def createTop_layout(self):
		self.top_layout = QHBoxLayout()
		json_pref = load_preferences()
		last_printer = (json_pref[0][1])
		# PRINTERS GROUPBOX
		groupbox_printers = QGroupBox("Printes")
		vbox = QVBoxLayout()
		groupbox_printers.setLayout(vbox)
		groupbox_printers.setFixedHeight(150)
		groupbox_printers.setFixedWidth(250)

		self.printer_table = QListWidget()
		self.printer_table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		# self.printer_table.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		# self.printer_table.insertItem(0, "Red")
		self.printer_table.clear()
		self.printer_table.setFixedHeight(106)
		self.printer_table.doubleClicked.connect(self.open_printer_table)
		self.printer_table.addItems(printers)
		self.printer_table.setCurrentRow(last_printer);
		vbox.addWidget(self.printer_table)
		self.top_layout.addWidget(groupbox_printers)
		self.top_layout.addStretch()

		# SETTINGS GROUPBOX
		groupbox_setting = QGroupBox("Printer setting")
		vbox2 = QGridLayout()
		groupbox_setting.setFixedHeight(150)
		groupbox_setting.setFixedWidth(350)

		# # POČET KOPII
		self.copies = QSpinBox()
		self.copies.setValue(1)
		self.copies.setMinimum(1)
		self.copies.setMaximum(999)
		self.copies.setFixedSize(60, 25)
		groupbox_setting.setLayout(vbox2)
		# PAPERFORMAT
		self.papersize = QComboBox(self)
		self.papersize.clear()
		for items in papers:
			self.papersize.addItem(items)
		# self.papersize.addItem("A3")
		# self.papersize.addItem("A5")
		# self.papersize.addItem("450x320")
		# self.papersize.addItem("480x325")
		self.papersize.activated[str].connect(self.papersize_box_change) 
		# # SIDES
		self.lp_two_sided = QCheckBox('two-sided', self)
		self.lp_two_sided.toggled.connect(self.togle_btn)
		self.lp_two_sided.move(20, 20)
		# FIT 
		self.fit_to_size = QCheckBox('Fit to page', self)
		# self.fit_to_size.toggled.connect(self.togle_btn)
		# ORIENTATION L/T
		self.btn_orientation = QPushButton()
		self._icon = QIcon()
		self._icon.addPixmap(QPixmap('icons/long.png'))
		self.btn_orientation.setCheckable(True)
		self.btn_orientation.setIcon(self._icon)
		# self.btn_orientation.setFixedHeight(24)
		# self.btn_orientation.setFixedWidth(24)
		self.btn_orientation.setIconSize(QSize(23,38))
		self.btn_orientation.setChecked(True)
		self.btn_orientation.setVisible(False)
		self.btn_orientation.toggled.connect(lambda: self.icon_change('icons/long.png','icons/short.png',self.btn_orientation))

		# COLLATE
		self.btn_collate= QPushButton()
		self._icon_collate = QIcon()
		self._icon_collate.addPixmap(QPixmap('icons/collate_on.png'))
		self.btn_collate.setIcon(self._icon_collate)

		self.btn_collate.setCheckable(True)
		self.btn_collate.setIconSize(QSize(23,38))
		self.btn_collate.setChecked(True)
		self.btn_collate.toggled.connect(lambda: self.icon_change('icons/collate_on.png','icons/collate_off.png',self.btn_collate))

		vbox2.addWidget(self.copies, 0,0)
		vbox2.addWidget(self.papersize, 0,1)
		vbox2.addWidget(self.fit_to_size, 0,2)
		vbox2.addWidget(self.lp_two_sided, 1,0)
		vbox2.addWidget(self.btn_orientation, 1,1)
		vbox2.addWidget(self.btn_collate, 1,2)

		self.top_layout.addWidget(groupbox_setting)
		self.top_layout.addStretch()


	def papersize_box_change(self, text):
			self.update_Debug_list(text)
			return text

	def togle_btn(self):
		if self.lp_two_sided.isChecked():
			self.btn_orientation.setVisible(True)
		else:
			self.btn_orientation.setVisible(False)
	#TODO def icon_change(self, on_, off_):

	def icon_change(self, _on, _off, name):
		print (name.isChecked())
		if name.isChecked():
			# print ('long')
			self._icon = QIcon()
			self._icon.addPixmap(QPixmap(_on))
			name.setIcon(self._icon)
		else:
			# print ('short')
			self._icon = QIcon()
			self._icon.addPixmap(QPixmap(_off))
			name.setIcon(self._icon)

	def table_print(self):
		green_ = (QColor(80, 80, 80))
		black_ = (QBrush(QColor(0, 0, 0)))
		outputfiles = []
		if self.table.currentItem() == None:
			QMessageBox.information(self, 'Error', 'Choose file to print', QMessageBox.Ok)
			return
		if self.printer_table.currentItem() == None:
			QMessageBox.information(self, 'Error', 'Choose printer!', QMessageBox.Ok)
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			# self.table.item(0, 0).setIcon(desktop_icon)
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
			# self.insert_icon(QStyle.SP_DialogApplyButton, 0, row)
			# self.setColortoRow(self.table, row, green_, black_)
			# WOP
			tiskarna_ok = self.printer_table.currentItem()
			tiskarna_ok = (tiskarna_ok.text())
			# print ('INFOJE:' + str(self.lp_two_sided.isChecked()))
			# print (debugstring)
			# self.update_Debug_list(str(debugstring))
		# print (outputfiles)
		debugstring = print_this_file(outputfiles, tiskarna_ok, self.lp_two_sided.isChecked(), self.btn_orientation.isChecked(), str(self.copies.value()), self.papersize.currentText(), self.fit_to_size.isChecked(), self.btn_collate.isChecked())
		self.update_Debug_list(debugstring)

	def open_table(self):
		green_ = (QColor(80, 80, 80))
		black_ = (QBrush(QColor(0, 0, 0)))
		outputfiles = []
		# desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon))
		self.table.setCellWidget(0, 0, ImgWidget1(self))
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
		openfile(outputfiles)
		self.update_Debug_list(str(cesta_souboru))

	def open_printer_table(self):
		for items in sorted(self.printer_table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			tiskarna = (printers[row])
		open_printer(tiskarna)
		self.update_Debug_list(str(tiskarna))

	def keyPressEvent(self,e):
		if e.key() == Qt.Key_Delete:
			for items in sorted(self.table.selectionModel().selectedRows()):
				row = items.row()
				print ('row is' + str(row))
				print (str(argy))
				self.table.removeRow(row)
				# self.table.updateTable()
				# vymyslet líp
				# print ('mazu radek' + str(row))
				# rows.pop(row)
				# print (rows)
	# @QtCore.pyqtSlot()
	def deleteClicked(self):
		row = self.table.currentRow()
		self.table.removeRow(row)

	def openFileNamesDialog(self):
		options = QFileDialog.Options()
		# options |= QFileDialog.DontUseNativeDialog
		soubor, _ = QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "",";Pdf Files (*.pdf)", options=options)
		if soubor:
			print (soubor)
			files, d_info = basic_parse(soubor)
			self.debuglist.setText(d_info)
			print (files)
			# rows2 = combine_lists(rows, files)
			rows = files
			print (rows)
			self.table_reload(rows)

if __name__ == '__main__':
	app = QApplication(sys.argv)
	path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'icons/printer.png')
	app.setWindowIcon(QIcon(path))
	form = Window()
	darkmode()
	time_boot = (str((time.time() - start_time))[:5] + ' seconds')
	form.update_Debug_list(time_boot)
	form.show()
	sys.exit(app.exec_())