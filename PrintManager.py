#!/usr/bin/env python3
import sys
import os
import subprocess
import json
from PyPDF2 import PdfFileReader, PdfFileMerger, PdfFileWriter
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDropEvent, QKeySequence, QPalette, QColor, QIcon, QPixmap, QBrush, QPainter, QFont, QCursor
from PyQt5.QtCore import *

from tnefparse.tnef import TNEF, TNEFAttachment, TNEFObject
from tnefparse.mapi import TNEFMAPI_Attribute

from libs.colordetector import *
from libs.ocr_module import ocr_core
from libs.crop_module import processFile
from libs.pdfextract_module import extractfiles

version = '0.24'
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
username = os.path.expanduser("~")

# extract printer info as list for preferences only
def load_printers():
	# print ('load printer list')
	output = (subprocess.check_output(["lpstat", "-a"]))
	outputlist = (output.splitlines())
	tolist = [] # novy list
	for num in outputlist:  # prochazeni listem
		first, *middle, last = num.split()
		tiskarna = str(first.decode())
		tolist.append(tiskarna)
	return (tolist)

# PREFERENCES BASIC
def load_preferences():
	print ('JSON load on boot')
	try:
		with open('config.json', encoding='utf-8') as data_file:
			json_pref = json.loads(data_file.read())
		if json_pref[0][6] == username:
			print ('preferences OK - using saved printers')
			printers = json_pref[0][7]
			default_pref = [json_pref[0][8],json_pref[0][9]]
		else: 
			print ('other machine loading printers')
			printers = load_printers()
	except:
		print ('json loading error')
		printers = load_printers()
		json_pref = [0,0,0,0,0,0]
		default_pref = ['eng',300]
	return json_pref, printers, default_pref

def save_preferences(*settings):
	print ('JSON save on exit')
	preferences = []
	for items in settings:
		preferences.append(items)
	with open('config.json', 'w', encoding='utf-8') as data_file:
		json.dump(preferences, data_file)
	startup = 1
	return startup


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

def previewimage(original_file):
	# outputfiles = []
	command = ["qlmanage", "-p", original_file]
	subprocess.run(command)
	# outputfiles.append(outputfile)
	return command

def compres_this_file(original_file):
	outputfiles = []
	head, ext = os.path.splitext(original_file)
	outputfile = head + '_c' + ext
	command = ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4", "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-sOutputFile="+outputfile, original_file]
	subprocess.run(command)
	outputfiles.append(outputfile)
	return command, outputfiles

def raster_this_file(original_file,resolution):
	outputfiles = []
	head, ext = os.path.splitext(original_file)
	outputfile = head + '_raster' + ext
	command_gs = ["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dNOCACHE", "-sDEVICE=pdfwrite", "-sColorConversionStrategy=/LeaveColorUnchanged", "-dAutoFilterColorImages=true", "-dAutoFilterGrayImages=true", "-dDownsampleMonoImages=true", "-dDownsampleGrayImages=true", "-dDownsampleColorImages=true", "-sOutputFile="+outputfile, original_file]
	command = ["convert", "-density", str(resolution), "+antialias", str(original_file), str(outputfile)]
	# command = ["pdf2ps", original_file]
	# cmd = "pdf2ps " +  str(original_file) + " - | ps2pdf - " + str(outputfile)
	# ps = subprocess.Popen(cmd,shell=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
	# output = ps.communicate()[0]
	# print(output)
	subprocess.run(command)
	outputfiles.append(outputfile)
	return command, outputfiles

def print_this_file(print_file, printer, lp_two_sided, orientation, copies, p_size, fit_to_size, collate, colors):
	# https://www.cups.org/doc/options.html
	# COLATE
	if collate == 1:
		print ('collate ON')
		_collate =  ('-o collate=true')
	else: 
		print ('collate OFF')
		_collate = ('-o collate=false')
	# COLORS 
	if colors == 'Auto':
		_colors =  ('-oColorModel=')
	if colors == 'Color':
		_colors =  ('-OColorMode=Color')
	if colors == 'Gray':
		_colors =  ('-OColorMode=GrayScale')
		# _colors =  ('-oColorModel=KGray')

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
		command = ["lp", "-d", printer, printitems,  "-n" + copies, lp_two_sided_, p_size_, fit_to_size, _collate]
		subprocess.run(command)
		print (username)
		# window.update_Debug_list(str(debugstring))
	try:
		subprocess.run(["open", username + "/Library/Printers/" + str(printer) + ".app"])
	except:
		print ('printer not found')
	return command

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
				d_info = ''
	rows = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
	return rows, d_info

def getimageinfo (filename):
	output = (subprocess.check_output(["identify", filename]))
	outputlist = (output.splitlines())
	getimageinfo = []
	for num in outputlist:  # prochazeni listem
		first, *middle, last = num.split()
		getimageinfo.append(str(middle[1].decode()) + ' px')
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

class Customdialog(QDialog):
	def __init__(self):
		super(RegisterPage, self).__init__()
		loadUi('RegisterPage.ui', self)

def darkmode():
	app.setStyle("Fusion")
	app.setStyleSheet('QPushButton:disabled {color: #696969;background-color:#272727;}')
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
# for icons
class IconDelegate(QStyledItemDelegate):
	def initStyleOption(self, option, index):
		super(IconDelegate, self).initStyleOption(option, index)
		if option.features & QStyleOptionViewItem.HasDecoration:
			s = option.decorationSize
			s.setWidth(option.rect.width())
			option.decorationSize = s

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
		buttonBox.rejected.connect(self.exit_dialog)

	def getInputs(self):
		return (self.first.text(), self.second.text())
	def exit_dialog(self):
		self.destroy()

class PrefDialog(QDialog):
	def __init__(self, prefs, parent=None):
		super().__init__(parent)
		self.setObjectName("Preferences")
		print ('default_pref' + str(prefs))
		self.layout = QFormLayout(self)
		self.text_link = QLineEdit(prefs[0], self)
		self.text_link.setMaxLength(3)
		self.text_link.setObjectName("text_lang")
		# resolution rasterubg
		self.res_box = QSpinBox(self)
		self.res_box.setRange(50, 1200)
		self.res_box.setValue(prefs[1])
		self.res_box.setObjectName("text_res")

		# file parser
		self.btn_convertor = QComboBox(self)
		self.btn_convertor.addItem('OpenOffice')
		self.btn_convertor.addItem('CloudConvert')
		self.btn_convertor.setObjectName("btn_conv")
		# self.btn_convertor.activated[str].connect(self.color_box_change) 

		self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self);
		self.layout.addRow("OCR language", self.text_link)
		self.layout.addRow("File convertor", self.btn_convertor)
		self.layout.addRow("Rastering resolution (DPI)", self.res_box)
		self.layout.addWidget(self.buttonBox)

		self.buttonBox.accepted.connect(self.accept)
		self.buttonBox.rejected.connect(self.reject)
		self.resize(50, 200)

	def getInputs(self):
		self.destroy()
		return self.text_link.text(), self.res_box.value()	

class Window(QMainWindow):
	def __init__(self, parent=None):
		super().__init__(parent)
		# Create menu options
		menubar = self.menuBar()
		file_menu = QMenu('File', self) # title and parent
		win_menu = QMenu('Windows', self) # title and parent
		open_action = QAction("Open file", self) # title and parent
		printing_setting_menu  = QAction("Printers", self) # title and parent
		printing_setting_menu.setShortcut('Ctrl+P')
		printing_setting_menu.setCheckable(True)
		printing_setting_menu.setChecked(True)
		printing_setting_menu.triggered.connect(self.togglePrintWidget)
		win_menu.addAction(printing_setting_menu)

		debug_setting_menu  = QAction("Debug", self) # title and parent
		debug_setting_menu.setShortcut('Ctrl+D')
		debug_setting_menu.setCheckable(True)
		debug_setting_menu.setChecked(True)
		debug_setting_menu.triggered.connect(self.toggleDebugWidget)
		win_menu.addAction(debug_setting_menu)

		# PREFERENCES
		pref_action = QAction("Preferences", self) # title and parent
		pref_action.triggered.connect(self.open_dialog)
		pref_action.setShortcut('Ctrl+W')
		file_menu.addAction(pref_action)

		open_action.triggered.connect(self.openFileNamesDialog)
		open_action.setShortcut('Ctrl+O')
		file_menu.addAction(open_action)
		close_action = QAction(' &Exit', self)
		close_action.triggered.connect(self.close)
		file_menu.addAction(close_action)
		menubar.addMenu(file_menu)
		menubar.addMenu(win_menu)

		self.central_widget = QWidget()               # define central widget
		self.setCentralWidget(self.central_widget)    # set QMainWindow.centralWidget
		self.mainLayout = QGridLayout()
		self.centralWidget().setLayout(self.mainLayout)
		self.createPrinter_layout()
		self.createDebug_layout()
		self.createButtons_layout()
		rows = []
		self.table_reload(rows)
		self.mainLayout.addLayout(self.printer_layout, 0,0)
		self.mainLayout.addLayout(self.debug_layout, 2, 0)
		self.mainLayout.addLayout(self.buttons_layout, 3, 0)
		self.setAcceptDrops(True)
		self.setFixedWidth(self.sizeHint().width())
		self.setWindowTitle("PrintManager " + version)

	def sizeHint(self):
		return QSize(620, 650)

	def open_dialog(self):
		# load setting first
		json_pref,printers,default_pref = load_preferences()
		print ('Default_pref:' + default_pref[0])
		form = PrefDialog(default_pref)
		try:
			if form.exec():
				self.localization, self.resolution = form.getInputs()
				# save and reload config 
				preferences = self.pref_generator()
				save_preferences(preferences)
				json_pref,printers,default_pref = load_preferences()
		except:
			print ('pref canceled')

	def pref_generator(self):
		try:
			print ('loc je:' + self.localization)
		except:
			self.localization = default_pref[0]
			self.resolution = default_pref[1]
		preferences = []
		if self.printer_tb.currentItem() != None:
			preferences.append('tiskarna')
			preferences.append(self.printer_tb.currentRow())
			preferences.append('printer_window')
			preferences.append(self.gb_printers.isHidden())
			preferences.append('debug_window')
			preferences.append(self.gb_debug.isHidden())
			preferences.append(username)
			preferences.append(printers)
			preferences.append(self.localization)
			preferences.append(self.resolution)
		return preferences

	def closeEvent(self, event):
		preferences = self.pref_generator()
		save_preferences(preferences)
		close = QMessageBox()
		close.setText("You sure?")
		close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
		close = close.exec()
		if close == QMessageBox.Yes:
			event.accept()
		else:
			event.ignore()

	def dragEnterEvent(self, event):
		p = self.mapFromGlobal(QCursor().pos())
		if event.mimeData().hasUrls():
			self.table.setStyleSheet("background-image: url(icons/drop.png);background-repeat: no-repeat;background-position: center center;background-color: #2c2c2c;")
			event.accept()
			self.debuglist.setText('loading files, please wait....')

	def dropEvent(self, event):
		# hack to update saved value....
		try:
			print ('loc je:' + self.localization)
		except:
			self.localization = default_pref[0]
		items = ["to PDF", "SmartCut", "OCR", "Resize", "Parse"]
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
					QMessageBox.about(self, "Warning", "File " + str(file) + " import error.")
					break
				self.debuglist.setText(d_info)
				rows = files
				Window.table_reload(self, rows)
				break
			if extension == 'dat':
				for url in event.mimeData().urls():
					file = (url.toLocalFile())
				dirname = (os.path.dirname(file) + '/')
				dirname = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
				with open(file, "rb") as tneffile:
					t = TNEF(tneffile.read())
					for a in t.attachments:
						with open(os.path.join(dirname,a.name.decode("utf-8")), "wb") as afp:
							afp.write(a.data)
					self.update_Debug_list("Successfully wrote %i files" % len(t.attachments) + ' to: ' + dirname)
				break
			elif extension in office_ext:
				soubor = []
				self.debuglist.setText("Converting to PDF:" + extension)
				for url in event.mimeData().urls():
					file = (url.toLocalFile())
					soubor.append(file)
				self.splitlinesdebug('converting:' + str(len(soubor)) + ' file(s)')
				files = self.external_convert(extension, soubor)
				break
			# for images.... 
			elif extension in image_ext :
				soubor = []
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
						ocr = ocr_core(items, self.localization)
						print (ocr)
						ocr_output.append(ocr)
					# print ('pocet je' + str(len(ocr_output)))
					ocr_output =  ''.join(ocr_output)
					self.debuglist.clear()
					self.update_Debug_list(str(ocr_output))
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
				if text == 'Parse':
					parse_files = []
					print (type(soubor))
					files, d_info = basic_parse_image(soubor)
					rows = files
					Window.table_reload(self, rows)
					self.update_Debug_list('imported:' + str(soubor))
				if text == 'Resize':
					resize_files = []
					percent,ok = QInputDialog.getInt(self,"Resize image","Enter a percent", 50, 1, 100)
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
		# QProcess object for external app
		self.process = QProcess(self)
		# self.process.readyRead.connect(self.dataReady)
		for items in inputfile:
			# self.process.start("/Applications/LibreOffice.app/Contents/MacOS/soffice", "--headless", "--convert-to", "pdf", items,"--outdir", outputdir)
			# self.process.setProgram("/Applications/LibreOffice.app/Contents/MacOS/soffice")
			# self.process.setArguments("--headless", "--convert-to", "pdf", items,"--outdir", outputdir)
			self.process.setProcessChannelMode(QProcess.MergedChannels)
			# self.process.readyReadStandardOutput.connect(self.readStdOutput)
			self.process.start("/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf" + items + "--outdir" + outputdir)
			# self.process.start(["/Applications/LibreOffice.app/Contents/MacOS/soffice", "--headless", "--convert-to", "pdf", items,"--outdir", outputdir])
			# conv_output = (subprocess.check_output()
			# self.splitlinesdebug(conv_output)
			base = os.path.basename(items)
			base = os.path.splitext(base)[0]
			new_file = outputdir + base + '.pdf'
			converts.append(new_file)
			self.update_Debug_list(str(new_file))
			# import converted
		files, d_info = basic_parse(converts)
		rows = files
		Window.table_reload(self, rows)

#		# for items in inputfile:
		# 	conv_output = (subprocess.check_output()
		# 	self.splitlinesdebug(conv_output)
		# 	base = os.path.basename(items)
		# 	base = os.path.splitext(base)[0]
		# 	new_file = outputdir + base + '.pdf'
		# 	converts.append(new_file)
		# 	self.update_Debug_list(str(new_file))
		# 	# import converted
		# files, d_info = basic_parse(converts)
		# rows = files
		# Window.table_reload(self, rows)

	def table_reload(self, inputfile):
		# if debug == 1:
		# print ('Tabulka=' + str(inputfile))
		# print (len(inputfile))
		# self.table.setContextMenuPolicy(Qt.CustomContextMenu)
		self.table = TableWidgetDragRows()
		headers = ["", "File", "Size", "Kind", "Filesize", "Pages", "Price", "Colors", 'Filepath']
		self.table.setColumnCount(len(headers))
		self.table.setHorizontalHeaderLabels(headers)
		# better is preview (printig etc)
		# self.table.doubleClicked.connect(self.preview)
		self.table.doubleClicked.connect(self.open_tb)
		self.table.verticalHeader().setDefaultSectionSize(35)
		self.table.setColumnWidth(0, 35)
		self.table.setColumnWidth(1, 230)
		self.table.setColumnWidth(3, 34)
		self.table.setColumnWidth(4, 67)
		self.table.setColumnWidth(5, 34)
		self.table.setColumnWidth(6, 50)
		self.table.setColumnWidth(7, 52)
		self.table.verticalHeader().setVisible(False)
		self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		# icon wip
		self.table.setIconSize(QSize(32, 32))
		delegate = IconDelegate(self.table) 
		self.table.setItemDelegate(delegate)
		pdf_file = "icons/pdf.png"
		pdf_item = QTableWidgetItem()
		pdf_icon = QIcon()
		pdf_icon.addPixmap(QPixmap(pdf_file))
		# pixmap = pdf_icon.pixmap(QSize(50, 50))
		pdf_item.setIcon(pdf_icon)
		jpg_file = "icons/jpg.png"
		jpg_item = QTableWidgetItem()
		jpg_icon = QIcon()
		jpg_icon.addPixmap(QPixmap(jpg_file))
		jpg_item.setIcon(jpg_icon)

		self.table.setRowCount(len(inputfile))
		for i, (Info, File, Size, Kind, Filesize, Pages, Price, Colors, Filepath) in enumerate(inputfile):
			self.table.setItem(i, 1, QTableWidgetItem(File))
			self.table.setItem(i, 2, QTableWidgetItem(Size))
			self.table.setItem(i, 3, QTableWidgetItem(Kind))
			self.table.setItem(i, 4, QTableWidgetItem(Filesize))
			self.table.setItem(i, 5, QTableWidgetItem(str(Pages)))
			self.table.setItem(i, 6, QTableWidgetItem(Price))
			self.table.setItem(i, 7, QTableWidgetItem(Colors))
			self.table.setItem(i, 8, QTableWidgetItem(Filepath))
		self.table.setColumnHidden(8, True)
		# print ('rowcount je:' + str(self.table.rowCount()))
		if self.table.rowCount() == 0:
			self.table.setStyleSheet("background-image: url(icons/drop.png);background-repeat: no-repeat;background-position: center center;background-color: #191919;")
		# icons 
		for row in range(0,self.table.rowCount()):
			item = self.table.item(row, 3)
			print (item.text())
			if item.text() == 'pdf':
				self.table.item(row, 2).setTextAlignment(Qt.AlignCenter)
				self.table.item(row, 3).setTextAlignment(Qt.AlignCenter)
				self.table.item(row, 4).setTextAlignment(Qt.AlignCenter)
				self.table.item(row, 5).setTextAlignment(Qt.AlignCenter)
				self.table.item(row, 6).setTextAlignment(Qt.AlignCenter)
				self.table.setItem(row,0, QTableWidgetItem(pdf_item))
			else:
				self.table.item(row, 2).setTextAlignment(Qt.AlignCenter)
				self.table.item(row, 3).setTextAlignment(Qt.AlignCenter)
				self.table.item(row, 4).setTextAlignment(Qt.AlignCenter)
				self.table.item(row, 5).setTextAlignment(Qt.AlignCenter)
				self.table.item(row, 6).setTextAlignment(Qt.AlignCenter)
				self.table.setItem(row,0, QTableWidgetItem(jpg_item))

		self.table.selectionModel().selectionChanged.connect(
			self.on_selection_changed
		)
		# RIGHT CLICK MENU
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.contextMenuEvent)	 	
		self.mainLayout.addWidget(self.table,1,0)
		self.update()

	@pyqtSlot()
	def on_selection_changed(self):
		self.print_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.color_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.combine_pdf_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.split_pdf_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.compres_pdf_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.raster_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.extract_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.split_pdf_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.count_b.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)
		self.gb_setting.setEnabled(
			bool(self.table.selectionModel().selectedRows())
		)

	def contextMenuEvent(self, pos):
			if self.table.selectionModel().selection().indexes():
					for i in self.table.selectionModel().selection().indexes():
							row, column = i.row(), i.column()
					menu = QMenu()
					openAction = menu.addAction('Open')
					revealAction = menu.addAction('Reveal in finder')
					printAction = menu.addAction('Print')
					previewAction = menu.addAction('Preview')
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
					if action == previewAction:
						self.preview()

	def togglePrintWidget(self):
		print (self.gb_printers.isHidden())
		self.gb_printers.setHidden(not self.gb_printers.isHidden())
		self.gb_setting.setHidden(not self.gb_setting.isHidden())
		return True

	def toggleDebugWidget(self):
		self.gb_debug.setHidden(not self.gb_debug.isHidden())

	def createDebug_layout(self):
		self.debug_layout = QHBoxLayout()
		# load setting
		try:
			pref_debug_state = (json_pref[0][5])
		except Exception as e:
			pref_debug_state = 0
		self.gb_debug = QGroupBox("Debug")
		self.gb_debug.setVisible(not pref_debug_state)
		self.gb_debug.setChecked(True)
		self.gb_debug.setTitle('')
		self.gb_debug.setFixedHeight(91)
		self.gb_debug.setContentsMargins(0, 0, 0, 0)
		self.gb_debug.setStyleSheet("border: 0px; border-radius: 0px; padding: 0px 0px 0px 0px;")
		dbox = QVBoxLayout()
		dbox.setContentsMargins(0, 0, 0, 0);
		self.gb_debug.setLayout(dbox)
		# debug
		self.debuglist = QTextEdit("<b>Debug:</b>", self)
		self.debuglist.setAlignment(Qt.AlignJustify)
		self.debuglist.acceptRichText()
		self.debuglist.setReadOnly(True)
		self.debuglist.setFixedHeight(90)
		dbox.addWidget(self.debuglist)
		self.gb_debug.toggled.connect(self.toggleDebugWidget)

		self.debug_layout.addWidget(self.gb_debug)

	def createButtons_layout(self):
		self.buttons_layout = QHBoxLayout()
		# OPEN FILES
		# self.preview_b = QPushButton('Preview', self)
		# self.preview_b.clicked.connect(self.preview)
		# self.buttons_layout.addWidget(self.preview_b)
		# LOAD COLORS INFO
		self.color_b = QPushButton('Colors', self)
		self.color_b.clicked.connect(self.loadcolors)
		self.buttons_layout.addWidget(self.color_b)
		self.color_b.setDisabled(True)

		# SPOJ PDF
		self.combine_pdf_b = QPushButton('Join', self)
		self.combine_pdf_b.clicked.connect(self.combine_pdf)
		self.buttons_layout.addWidget(self.combine_pdf_b)
		self.combine_pdf_b.setDisabled(True)

		# ROZDEL PDF
		self.split_pdf_b = QPushButton('Split', self)
		self.split_pdf_b.clicked.connect(self.split_pdf)
		self.buttons_layout.addWidget(self.split_pdf_b)
		self.split_pdf_b.setDisabled(True)

		# COMPRES PDF
		self.compres_pdf_b = QPushButton('Compres', self)
		self.compres_pdf_b.clicked.connect(self.compres_pdf)
		self.buttons_layout.addWidget(self.compres_pdf_b)
		self.compres_pdf_b.setDisabled(True)

		# RASTROVANI PDF
		self.raster_b = QPushButton('Rasterize', self)
		self.raster_b.clicked.connect(self.rasterize_pdf)
		self.buttons_layout.addWidget(self.raster_b)
		self.raster_b.setDisabled(True)

		# EXTRACT IMAGES
		self.extract_b = QPushButton('Extract', self)
		self.extract_b.clicked.connect(self.extract_pdf)
		self.buttons_layout.addWidget(self.extract_b)
		self.extract_b.setDisabled(True)

		# POCITANI TABULKY PDF
		self.count_b = QPushButton('Count', self)
		self.count_b.clicked.connect(self.count_tb)
		self.buttons_layout.addWidget(self.count_b)
		self.count_b.setDisabled(True)

		# # # SPACE
		# self.labl = QLabel()
		# self.labl.setText(version)
		# self.labl.setAlignment(Qt.AlignCenter)
		# self.labl.setFixedSize(50, 10)
		# self.buttons_layout.addWidget(self.labl)

		# # EXIT SCRIPT
		# self.qbtn_exit = QPushButton('Konec', self)
		# self.qbtn_exit.clicked.connect(QCoreApplication.instance().quit)
		# self.buttons_layout.addWidget(self.qbtn_exit)
		# # # PRINT SCRIPT
		self.print_b = QPushButton('Print', self)
		self.print_b.clicked.connect(self.table_print)
		self.print_b.setDisabled(True)
		self.buttons_layout.addWidget(self.print_b)

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
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
			desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DialogResetButton))
		debugstring, outputfiles = raster_this_file(cesta_souboru, self.resolution)
		files, d_info = basic_parse(outputfiles)
		rows = files
		Window.table_reload(self, rows)
		self.update_Debug_list(str(debugstring))

	def extract_pdf(self):
		print ('PDF extractor WIP')
		outputfiles = []
		if self.table.currentItem() == None:
			QMessageBox.information(self, 'Error', 'No files selected', QMessageBox.Ok)
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
			desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DialogResetButton))
		try:
			outputfiles = extractfiles(cesta_souboru)
		except Exception as e:
			QMessageBox.information(self, 'Error', 'Importing error', QMessageBox.Ok)
			return
		files, d_info = basic_parse_image(outputfiles)
		rows = files
		Window.table_reload(self, rows)
		self.update_Debug_list(str(outputfiles))

	def count_tb(self):
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
		celkem = (str(len(soucet)) + '  PDF files, ' + str(sum(stranky)) + ' pages')
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
		indexes = self.table.selectionModel().selectedRows()
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			druh=index.sibling(items.row(),3).data()
		print (druh)
		# if self.table.currentItem() == None:
		# 	QMessageBox.information(self, 'Error', 'Choose files to convert', QMessageBox.Ok)
		# 	return
		if druh == 'pdf':
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
		else:
			QMessageBox.information(self, 'Error', 'Not supported', QMessageBox.Ok)
			return			

	def createPrinter_layout(self):
		self.printer_layout = QHBoxLayout()
		try:
			pref_l_printer = (json_pref[0][1])
			pref_printers_state = (json_pref[0][3])
		except Exception as e:
			pref_l_printer = 0
			pref_printers_state = 0
		# PRINTERS GROUPBOX
		self.gb_printers = QGroupBox("Printers")
		vbox = QVBoxLayout()
		self.gb_printers.setLayout(vbox)
		self.gb_printers.setFixedHeight(150)
		self.gb_printers.setFixedWidth(250)
		self.gb_printers.setVisible(not pref_printers_state)
		self.printer_tb = QListWidget()
		self.printer_tb.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.printer_tb.clear()
		self.printer_tb.setFixedHeight(106)
		self.printer_tb.doubleClicked.connect(self.open_printer_tb)
		self.printer_tb.addItems(printers)
		self.printer_tb.setCurrentRow(pref_l_printer);
		vbox.addWidget(self.printer_tb)
		self.printer_layout.addWidget(self.gb_printers)
		self.printer_layout.addStretch()

		# SETTINGS GROUPBOX
		self.gb_setting = QGroupBox("Printer setting")
		vbox2 = QGridLayout()
		self.gb_setting.setFixedHeight(150)
		self.gb_setting.setFixedWidth(350)
		self.gb_setting.setVisible(not pref_printers_state)
		self.gb_setting.setDisabled(True)

		# # POČET KOPII
		self.copies = QSpinBox()
		self.copies.setValue(1)
		self.copies.setMinimum(1)
		self.copies.setMaximum(999)
		self.copies.setFixedSize(60, 25)
		self.gb_setting.setLayout(vbox2)
		# PAPERFORMAT
		self.papersize = QComboBox(self)
		self.papersize.clear()
		for items in papers:
			self.papersize.addItem(items)
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

		# COLORS
		self.btn_colors = QComboBox(self)
		self.btn_colors.addItem('Auto')
		self.btn_colors.addItem('Color')
		self.btn_colors.addItem('Gray')
		self.btn_colors.activated[str].connect(self.color_box_change)
		# self.btn_colors= QPushButton()
		# self._icon_colors = QIcon()
		# self._icon_colors.addPixmap(QPixmap('icons/colors_auto.png'))
		# self.btn_colors.setIcon(self._icon_colors)
		# self.btn_colors.setCheckable(True)
		# self.btn_colors.setIconSize(QSize(23,38))
		# self.btn_colors.setChecked(True)
		# self.btn_colors.toggled.connect(lambda: self.icon_change('icons/colors_on.png','icons/colors_off.png',self.btn_colors))


		vbox2.addWidget(self.copies, 0,0)
		vbox2.addWidget(self.papersize, 0,1)
		vbox2.addWidget(self.fit_to_size, 0,2)
		vbox2.addWidget(self.lp_two_sided, 1,0)
		vbox2.addWidget(self.btn_orientation, 1,1)
		vbox2.addWidget(self.btn_collate, 1,2)
		vbox2.addWidget(self.btn_colors, 2,0)


		self.printer_layout.addWidget(self.gb_setting)
		self.printer_layout.addStretch()

	def papersize_box_change(self, text):
			self.update_Debug_list(text)
			return text

	def color_box_change(self, text):
			self.update_Debug_list(text)
			return text

	def togle_btn(self):
		if self.lp_two_sided.isChecked():
			self.btn_orientation.setVisible(True)
		else:
			self.btn_orientation.setVisible(False)

	def icon_change(self, _on, _off, name):
		print (name.isChecked())
		if name.isChecked():
			self._icon = QIcon()
			self._icon.addPixmap(QPixmap(_on))
			name.setIcon(self._icon)
		else:
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
		if self.printer_tb.currentItem() == None:
			QMessageBox.information(self, 'Error', 'Choose printer!', QMessageBox.Ok)
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			# self.table.item(0, 0).setIcon(desktop_icon)
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
			# self.setColortoRow(self.table, row, green_, black_)
			# WOP
			tiskarna_ok = self.printer_tb.currentItem()
			tiskarna_ok = (tiskarna_ok.text())
			# print ('INFOJE:' + str(self.lp_two_sided.isChecked()))
			# print (debugstring)
			# self.update_Debug_list(str(debugstring))
		# print (outputfiles)
		debugstring = print_this_file(outputfiles, tiskarna_ok, self.lp_two_sided.isChecked(), self.btn_orientation.isChecked(), str(self.copies.value()), self.papersize.currentText(), self.fit_to_size.isChecked(), self.btn_collate.isChecked(), self.btn_colors.currentText())
		self.update_Debug_list(debugstring)

	def preview(self):
		outputfiles = []
		try:
			for items in sorted(self.table.selectionModel().selectedRows()):
				row = items.row()
				index=(self.table.selectionModel().currentIndex())
				cesta_souboru=index.sibling(items.row(),8).data()
				outputfiles.append(cesta_souboru)
			previewimage(cesta_souboru)
		except Exception as e:
			return

	def open_tb(self):
		green_ = (QColor(80, 80, 80))
		black_ = (QBrush(QColor(0, 0, 0)))
		outputfiles = []
		# desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_FileIcon))
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			cesta_souboru=index.sibling(items.row(),8).data()
			outputfiles.append(cesta_souboru)
		openfile(outputfiles)
		self.update_Debug_list(str(cesta_souboru))

	def open_printer_tb(self):
		for items in sorted(self.printer_tb.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			tiskarna = (printers[row])
		open_printer(tiskarna)
		self.update_Debug_list(str(tiskarna))

	def keyPressEvent(self,e):
		if e.key() == Qt.Key_Delete:
			for items in sorted(self.table.selectionModel().selectedRows()):
				row = items.row()
				# print ('row is' + str(row))
				print (str(argy))
				self.table.removeRow(row)
		if e.key() == Qt.Key_F1:
			self.preview()

	def deleteClicked(self):
		row = self.table.currentRow()
		self.table.removeRow(row)

	def openFileNamesDialog(self):
		options = QFileDialog.Options()
		soubor, _ = QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "",";Pdf Files (*.pdf)", options=options)
		if soubor:
			print (soubor)
			files, d_info = basic_parse(soubor)
			self.debuglist.setText(d_info)
			print (files)
			rows = files
			print (rows)
			self.table_reload(rows)

if __name__ == '__main__':
	# load config firts
	json_pref, printers,default_pref = load_preferences()
	app = QApplication(sys.argv)
	path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'icons/printer.png')
	app.setWindowIcon(QIcon(path))
	form = Window()
	darkmode()
	# time_boot = (str((time.time() - start_time))[:5] + ' seconds')
	# form.update_Debug_list(time_boot)
	form.show()
	sys.exit(app.exec_())