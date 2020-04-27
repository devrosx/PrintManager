#!/usr/bin/env python3
import sys
import os
import subprocess
import json
from PyPDF2 import PdfFileReader, PdfFileMerger, PdfFileWriter
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QDropEvent, QKeySequence, QPalette, QColor, QIcon, QPixmap, QBrush, QPainter, QFont, QCursor, QTextCursor, QDrag
from PyQt5.QtCore import *
from tnefparse.tnef import TNEF, TNEFAttachment, TNEFObject
from tnefparse.mapi import TNEFMAPI_Attribute
# my modules import
from libs.colordetector import *
from libs.ocr_module import ocr_core
from libs.crop_module import processFile
from libs.pdfextract_module import extractfiles
from libs.cc_module import cc_convert
from libs.pdf_preview_module import pdf_preview_generator
from libs.super_crop_module import *
import webbrowser
version = '0.28'
import time
start_time = time.time()
info, name, size, extension, file_size, pages, price, colors, filepath = [],[],[],[],[],[],[],[],[]
mm = '0.3527777778'
office_ext = ['csv', 'db', 'odt', 'doc', 'gif', 'pcx', 'docx', 'dotx', 'fodp', 'fods', 'fodt', 'odb', 'odf', 'odg', 'odm', 'odp', 'ods', 'otg', 'otp', 'ots', 'ott', 'oxt', 'pptx', 'psw', 'sda', 'sdc', 'sdd', 'sdp', 'sdw', 'slk', 'smf', 'stc', 'std', 'sti', 'stw', 'sxc', 'sxg', 'sxi', 'sxm', 'sxw', 'uof', 'uop', 'uos', 'uot', 'vsd', 'vsdx', 'wdb', 'wps', 'wri', 'xls', 'xlsx', 'ppt']
image_ext = ['jpg', 'jpeg', 'png', 'tif', 'bmp']
next_ext = ['pdf','dat']
papers = ['A4', 'A5', 'A3', '480x320', '450x320', 'undefined']
username = os.path.expanduser("~")

# other os support
system = str(sys.platform)
if system == 'darwin':
	sys_support = 'supported'
else:
	sys_support = 'not supported'

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

# PREFERENCES BASIC
def load_preferences():
	print ('JSON load on boot')
	try:
		with open('config.json', encoding='utf-8') as data_file:
			json_pref = json.loads(data_file.read())
		if json_pref[0][8] == username:
			print ('preferences okPressed - using saved printers')
			printers = json_pref[0][9]
			default_pref = [json_pref[0][10],json_pref[0][11],json_pref[0][12]]
		else: 
			print ('other machine loading printers')
			printers = load_printers()
	except Exception as e:
		print (e)
		printers = load_printers()
		json_pref = [0,0,0,0,0,0,0]
		default_pref = ['eng',300,'OpenOffice']
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

def open_printer(file):
	subprocess.call(['subl', '/private/etc/cups/ppd/'+file+'.ppd'])

def revealfile(list_path,reveal): #reveal and convert
	if isinstance (list_path, list):
		for items in list_path:
			subprocess.call(['open', reveal, items])
	else:
		subprocess.call(['open', reveal, list_path])

def previewimage(original_file):
	command = ["qlmanage", "-p", original_file]
	subprocess.run(command)
	return command

def mergefiles(list_path,save_dir):
	base = os.path.basename(list_path[0])
	file = os.path.splitext(base)
	folder_path = os.path.dirname(list_path[0])
	# print (folder_path)
	if folder_path == '/tmp':
		folder_path = save_dir
	outputfile = folder_path + file[0] +  '_m.pdf'
	# print (outputfile)
	merger = PdfFileMerger()
	for pdf in list_path:
		merger.append(pdf)
	merger.write(outputfile)
	merger.close()
	return outputfile

def splitfiles(file):
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

def gray_this_file(original_file,filetype):
	outputfiles = []
	for item in original_file:
		head, ext = os.path.splitext(item)
		outputfile = head + '_gray' + ext
		if filetype == 'pdf':
			command = ["gs", "-sDEVICE=pdfwrite", "-dProcessColorModel=/DeviceGray", "-dColorConversionStrategy=/Gray", "-dPDFUseOldCMS=false", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-sOutputFile="+outputfile, item]
		else:
			command = ["convert", item, "-colorspace", "Gray", outputfile]
		subprocess.run(command)
		outputfiles.append(outputfile)
	return command, outputfiles

def compres_this_file(original_file):
	outputfiles = []
	for item in original_file:
		head, ext = os.path.splitext(item)
		outputfile = head + '_c' + ext
		command = ["gs", "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.4", "-dPDFSETTINGS=/ebook", "-dNOPAUSE", "-dQUIET", "-dBATCH", "-sOutputFile="+outputfile, item]
		subprocess.run(command)
		outputfiles.append(outputfile)
	return command, outputfiles

def raster_this_file(original_file,resolution):
	outputfiles = []
	for item in original_file:
		head, ext = os.path.splitext(item)
		outputfile = head + '_raster' + ext
		command_gs = ["gs", "-dSAFER", "-dBATCH", "-dNOPAUSE", "-dNOCACHE", "-sDEVICE=pdfwrite", "-sColorConversionStrategy=/LeaveColorUnchanged", "-dAutoFilterColorImages=true", "-dAutoFilterGrayImages=true", "-dDownsampleMonoImages=true", "-dDownsampleGrayImages=true", "-dDownsampleColorImages=true", "-sOutputFile="+outputfile, original_file]
		command = ["convert", "-density", str(resolution), "+antialias", str(item), str(outputfile)]
		subprocess.run(command)
		outputfiles.append(outputfile)
	return command, outputfiles

def convert_this_file(original_file,resolution):
	outputfiles = []
	for item in original_file:
		head, ext = os.path.splitext(item)
		outputfile = head + '.pdf'
		command = ["convert", str(resolution), '-density',  '300', str(item), str(outputfile)]
		print (command)
		subprocess.run(command)
		outputfiles.append(outputfile)
	return command, outputfiles


def get_boxes(input_file):
		pdf_reader = PdfFileReader(input_file)
		page = pdf_reader.getPage(0)
		pageNumbers = pdf_reader.getNumPages()
		return pageNumbers

def file_info_new(inputs, file, *args):
	_info = []
	if file == 'pdf':
		for item in inputs:
			pdf_toread = PdfFileReader(open(item, "rb"))
			pdf_ = pdf_toread.getDocumentInfo()
			pdf_fixed = {key.strip('/'): item.strip() for key, item in pdf_.items()}
			pdf_fixed.update( {'Filesize' : humansize(os.path.getsize(item))} )
			# print (pdf_fixed)
			boxes = get_boxes(item)
			# z = dict(list(x.items()) + list(y.items()))
			# pdf_fixed.update({'a':'B'})
			# pdf_fixed.update(dict(a=1))
			# pdf_fixed.update(a=1)
			html_info = tablemaker(pdf_fixed)
			_info.append(html_info)
	else:
		name_ = []
		val_ = []
		for item in inputs:
			output = (subprocess.check_output(["mdls", item]))
			pdf_info = (output.splitlines())
			for num in pdf_info:
				num = num.decode("utf-8")
				name, *value = num.split('=')
				value = ', '.join(value)
				name = name.rstrip()
				value = value.replace('"','')
				value = value.lstrip()
				name = name.replace('kMD','')
				name_.append(name)
				val_.append(value)
		tolist = dict(zip(name_, val_))
		unwanted = ['', [], '(', '0', '(null)']
		img_ = {k: v for k, v in tolist.items() if v not in unwanted}
		img_.update( {'Filesize' : humansize(os.path.getsize(item))} )
		_info = tablemaker(img_)
	return _info

def tablemaker (inputs):
	html = "<table width=100% table cellspacing=0 style='border-collapse: collapse' border = \"0\" >"
	html += '<style>table, td, th {font-size: 9px;border: none;padding-left: 2px;padding-right: 2px;ppadding-bottom: 4px;}</style>'
	# fix this
	inputs = {k.replace(u'D:', ' ') : v.replace(u'D:', ' ') for k, v in inputs.items()}
	inputs = {k.replace(u"+01'00'", ' ') : v.replace(u"+01'00'", ' ') for k, v in inputs.items()}
	inputs = {k.replace(u" +0000", ' ') : v.replace(u" +0000", ' ') for k, v in inputs.items()}
	inputs = {k.replace(u"Item", ' ') : v.replace(u"Item", ' ') for k, v in inputs.items()}
	inputs = {k.replace(u" 00:00:00", ' ') : v.replace(u" 00:00:00", ' ') for k, v in inputs.items()}
	# print (inputs)
	# for i in inputs:
	# 	print (i)
	# 	i = dt.datetime.strptime(dict[i],'%m/%d/%y').month
	# alert['alert_date'] = datetime.strptime(alert['alert_date'], "%Y-%m-%d %H:%M:%S")
	for dict_item in inputs:
		html += '<tr>'
		key_values = dict_item.split(',')
		# print (key_values) # [1:]
		html += '<th><p style="text-align:right;color: #7e7e7e;">' + str(key_values[0]) + '</p></th>'
		# print (inputs[dict_item])
		html += '<th><p style="text-align:left;font-weight: normal">' + inputs[dict_item] + '</p></th>'
		html += '</tr>'
	html += '</table>'
	return html

def print_this_file(print_file, printer, lp_two_sided, orientation, copies, p_size, fit_to_size, collate, colors):
	# https://www.cups.org/doc/options.html
	# COLATE
	# print ('XXXXX: ' + str(colors))
	if collate == 1:
		print ('collate ON')
		collate =  ('-o collate=true')
	else: 
		print ('collate OFF')
		collate = ('')
	# COLORS 
	if colors == 'Auto':
		colors =  ('')
	if colors == 'Color':
		colors =  ('-OColorMode=Color')
	if colors == 'Gray':
		colors =  ('-OColorMode=GrayScale')
		# _colors =  ('-oColorModel=KGray')
	# PAPER SHRINK
	if fit_to_size == 1:
		fit_to_size =  ('-o fit-to-page')
	else: 
		fit_to_size = ('')
	# PAPER SIZE WIP
	if p_size == 'A4':
		_p_size = ('-o media=A4')
	if p_size == 'A3':
		_p_size = ('-o media=A3')
	if p_size == 'A5':
		_p_size = ('-o media=A5')
	if p_size == '480x320':
		_p_size = ('-o media=480x320')
	if p_size == '450x320':
		_p_size = ('-o media=450x320')
	else:
		_p_size = '-o media=Custom.' + p_size + 'mm'
	# na canonu nefunguje pocet kopii... vyhodit -o sides=one-sided
	if lp_two_sided == 1:
		lp_two_sided_ = ('-o sides=two-sided')
		if orientation == 1:
			lp_two_sided_ = ('-o sides=two-sided-long-edge')
		else:
			lp_two_sided_ = ('-o sides=two-sided-short-edge')
	else:
		lp_two_sided_ = ('-o sides=one-sided')
	for printitems in print_file:
		command = ["lp", "-d", printer, printitems, "-n" + copies, lp_two_sided_, _p_size, fit_to_size, collate, colors]
		# remove blank strings
		command = [x for x in command if x]
		subprocess.run(command)
	try:
		subprocess.run(["open", username + "/Library/Printers/" + str(printer) + ".app"])
	except:
		print ('printer not found')
	return command

def pdf_parse(self, inputs, *args):
	self.rows = []
	if type(inputs) is str:
		inputs = [inputs]
	print (inputs)
	# print ('ROWS:' + str(self.rows))
	for item in inputs:
		# print ('item' + str(item))
		oldfilename = (os.path.basename(item))
		ext_file = os.path.splitext(oldfilename)
		dirname = (os.path.dirname(item) + '/')
		with open(item, mode='rb') as f:
			pdf_input = PdfFileReader(f, strict=False)
			if pdf_input.isEncrypted:
				self.d_writer('File is encrypted...', 0, 'red')
				break
			else:
				qsizedoc = (pdf_input.getPage(0).mediaBox)
				sirka = (float(qsizedoc[2]) * float(mm))
				vyska = (float(qsizedoc[3]) * float(mm))
				page_size = (str(round(sirka)) + 'x' + str(round(vyska)) + ' mm')
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
				extension.append(ext_file[1][1:].lower())
	self.rows = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
	# print (self.rows)
	return self.rows

def getimageinfo (filename):
	output = (subprocess.check_output(["identify", '-format', '%wx%hpx %m', filename]))
	outputlist = (output.splitlines())
	getimageinfo = []
	for num in outputlist:  # prochazeni listem
		first, middle = num.split()
		getimageinfo.append(str(first.decode()))
		getimageinfo.append(str(middle.decode()))
	return getimageinfo
	
def parse_img(self, inputs, *args):
	for item in inputs:
		oldfilename = (os.path.basename(item))
		filesize = humansize(os.path.getsize(item))
		ext_file = os.path.splitext(oldfilename)
		dirname = (os.path.dirname(item) + '/')
		info.append('')
		image_info = getimageinfo(item)
		name.append(ext_file[0])
		size.append(str(image_info[0]))
		extension.append(ext_file[1][1:].lower())
		file_size.append(humansize(os.path.getsize(item)))
		pages.append(1)
		price.append('')
		colors.append(str(image_info[1]))
		filepath.append(item)
	self.rows = list(zip(info, name, size, extension, file_size, pages, price, colors, filepath))
	return self.rows

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
	app.setStyleSheet('QPushButton:enabled {color: #ffffff;background-color:#2c2c2c;}QPushButton:disabled {color: #696969;background-color:#272727;}')
	app.setPalette(palette)

class TableWidgetDragRows(QTableWidget):
	def __init__(self, *args, **kwargs):
		QTableWidget.__init__(self, *args, **kwargs)
		self.setAcceptDrops(True)
		# self.setDragEnabled(True)
		self.viewport().setAcceptDrops(True)
		self.setDragDropOverwriteMode(False)
		# self.setDropIndicatorShown(True)
		self.setEditTriggers(QAbstractItemView.NoEditTriggers)
		self.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.setSelectionBehavior(QAbstractItemView.SelectRows)
		# self.setDragDropMode(QAbstractItemView.InternalMove)
		self.setSortingEnabled(True)
# for icons
class IconDelegate(QStyledItemDelegate):
	def initStyleOption(self, option, index):
		super(IconDelegate, self).initStyleOption(option, index)
		if option.features & QStyleOptionViewItem.HasDecoration:
			s = option.decorationSize
			s.setWidth(option.rect.width())
			option.decorationSize = s

class InputDialog_SmartCut(QDialog):
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

class InputDialog_PDFcut(QDialog):
	def __init__(self, parent=None):
		super().__init__(parent)
		self.multipage = QCheckBox(self)
		self.multipage.setChecked(True)
		self.multipage.toggled.connect(self.hide)
		self.croppage_l = QLabel()
		self.croppage_l.setText("Page used as cropbox for all pages")
		self.croppage = QSpinBox(self)
		self.croppage.setRange(1, 1000)
		self.croppage.setValue(1)
		self.croppage.setVisible(False)
		self.croppage_l.setVisible(False)
		self.margin = QSpinBox(self)
		self.margin.setRange(-200, 200)
		# self.margin.setValue(1)
		buttonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self);
		self.layout = QFormLayout(self)
		self.layout.addRow("Detect all pages cropboxes", self.multipage)
		self.layout.addRow(self.croppage_l, self.croppage)
		self.layout.addRow("Margin", self.margin)
		self.layout.addWidget(buttonBox)
		buttonBox.accepted.connect(self.accept)
		buttonBox.rejected.connect(self.reject)
	def getInputs(self):
		return (self.multipage.isChecked(), self.croppage.value(), self.margin.value())
	def hide(self):
		if self.multipage.isChecked():
			self.croppage.setEnabled(False)
			self.croppage.setVisible(False)
			self.croppage_l.setVisible(False)
		else:
			self.croppage.setEnabled(True)
			self.croppage.setVisible(True)
			self.croppage_l.setVisible(True)


class PrefDialog(QDialog):
	def __init__(self, prefs, parent=None):
		super().__init__(parent)
		self.setObjectName("Preferences")
		print ('default_pref' + str(prefs))
		self.layout = QFormLayout(self)
		self.text_link = QLineEdit(prefs[0], self)
		self.text_link.setMaxLength(3)
		# self.text_link.setObjectName("text_lang")
		# resolution rasterubg
		self.res_box = QSpinBox(self)
		self.res_box.setRange(50, 1200)
		self.res_box.setValue(prefs[1])
		# self.res_box.setObjectName("text_res")
		# file parser
		self.btn_convertor = QComboBox(self)
		self.btn_convertor.addItem('OpenOffice')
		self.btn_convertor.addItem('CloudConvert')
		self.btn_convertor.setCurrentText(prefs[2])
		# self.btn_convertor.setObjectName("btn_conv")
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
		return self.text_link.text(), self.res_box.value(), self.btn_convertor.currentText()		

class Window(QMainWindow):
	def __init__(self, parent=None):
		super(Window, self).__init__(parent)
		self.setWindowTitle("PrintManager " + version)
		self.setWindowFlags(Qt.WindowStaysOnTopHint) 
		self.setAcceptDrops(True)
		menubar = self.menuBar()
		menubar.setNativeMenuBar(True)
		file_menu = QMenu('File', self)
		win_menu = QMenu('Windows', self)
		about_menu = QMenu('About', self)
		open_action = QAction("Open file", self) 
		printing_setting_menu  = QAction("Printers", self)
		printing_setting_menu.setShortcut('Ctrl+P')
		printing_setting_menu.setCheckable(True)
		printing_setting_menu.setChecked(True)
		printing_setting_menu.triggered.connect(self.togglePrintWidget)
		win_menu.addAction(printing_setting_menu)
		# DEBUG PANEL
		debug_setting_menu  = QAction("Debug", self)
		debug_setting_menu.setShortcut('Ctrl+D')
		debug_setting_menu.setCheckable(True)
		debug_setting_menu.setChecked(True)
		debug_setting_menu.triggered.connect(self.toggleDebugWidget)
		win_menu.addAction(debug_setting_menu)
		# PREVIEW PANEL
		printing_setting_menu  = QAction("Preview panel", self)
		printing_setting_menu.setShortcut('Ctrl+T')
		printing_setting_menu.setCheckable(True)
		printing_setting_menu.setChecked(False)
		printing_setting_menu.triggered.connect(self.togglePreviewWidget)
		win_menu.addAction(printing_setting_menu)
		# PREVIEW
		preview_menu  = QAction("Preview", self)
		preview_menu.setShortcut('F1')
		preview_menu.triggered.connect(self.preview_window)
		win_menu.addAction(preview_menu)
		# PREFERENCES
		pref_action = QAction("Preferences", self)
		pref_action.triggered.connect(self.open_dialog)
		pref_action.setShortcut('Ctrl+W')
		file_menu.addAction(pref_action)
		# GITHUB PAGE
		url_action = QAction("PrintManager Github", self)
		url_action.triggered.connect(lambda: webbrowser.open('http://github.com/devrosx/PrintManager/'))
		about_menu.addAction(url_action)
		# OPEN
		open_action.triggered.connect(self.openFileNamesDialog)
		open_action.setShortcut('Ctrl+O')
		file_menu.addAction(open_action)
		close_action = QAction(' &Exit', self)
		close_action.triggered.connect(self.close)
		file_menu.addAction(close_action)
		menubar.addMenu(file_menu)
		menubar.addMenu(win_menu)
		menubar.addMenu(about_menu)

		self.files = []

		"""Core Layouts"""
		self.mainLayout = QGridLayout()

		self.table_reload(self.files)
		self.createPrinter_layout()
		self.createDebug_layout()
		self.createButtons_layout()
		pref_preview_state = self.createPreview_layout()
		# HACK to window size on boot
		if pref_preview_state == 1:
			self.setFixedSize(617, 650)
			self.resize(617, 650)
		else:
			self.setFixedSize(875, 650)
			self.resize(875, 650)

		self.mainLayout.addLayout(self.printer_layout, 0,0,1,2)
		self.mainLayout.addLayout(self.debug_layout, 2,0,1,2)
		# self.mainLayout.setRowStretch(0, 2)
		# self.mainLayout.setColumnStretch(0, 2)
		self.mainLayout.addLayout(self.preview_layout, 0,3,0,3)
		self.mainLayout.addLayout(self.buttons_layout, 3,0,1,2)
		# self.setFixedSize(self.window.sizeHint())
		# self.setFixedWidth(self.sizeHint().width())

		"""Initiating  mainLayout """
		self.window = QWidget()
		self.window.setLayout(self.mainLayout)
		self.setCentralWidget(self.window)

	def open_dialog(self):
		# load setting first
		json_pref,printers,default_pref = load_preferences()
		print ('Default_pref:' + default_pref[0])
		form = PrefDialog(default_pref)
		try:
			if form.exec():
				self.localization, self.resolution, self.convertor = form.getInputs()
				preferences = self.pref_generator()
				save_preferences(preferences)
				json_pref,printers,default_pref = load_preferences()
		except:
			print ('pref canceled')

	def pref_generator(self):
		try:
			print (self.localization)
			print (self.resolution)
		except:
			self.localization = default_pref[0]
			self.resolution = default_pref[1]
			self.convertor = default_pref[2]
		preferences = []
		if self.printer_tb.currentItem() != None:
			preferences.append('printer')
			preferences.append(self.printer_tb.currentRow())
			preferences.append('printer_window')
			preferences.append(self.gb_printers.isHidden())
			preferences.append('debug_window')
			preferences.append(self.gb_debug.isHidden())
			preferences.append('preview_window')
			preferences.append(self.gb_preview.isHidden())
			preferences.append(username)
			preferences.append(printers)
			preferences.append(self.localization)
			preferences.append(self.resolution)
			preferences.append(self.convertor)
		return preferences

	def closeEvent(self, event):
		preferences = self.pref_generator()
		save_preferences(preferences)
		close = QMessageBox()
		close.setText("Are you sure?")
		close.setIcon(QMessageBox.Warning)
		close.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
		close.setDefaultButton(QMessageBox.Yes)
		close = close.exec()
		if close == QMessageBox.Yes:
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		event.accept()

	def dragLeaveEvent(self, event):
		event.accept()
		self.table.setStyleSheet("QTableView {background-image:none}" )
		self.d_writer('',0)
# ;border: 2px solid #001033;
	def dragEnterEvent(self, event):
		event.setDropAction(Qt.MoveAction)
		if event.mimeData().hasUrls():
			self.d_writer(event.mimeData().text(),0)
			self.table.setStyleSheet("QTableView {border: 2px solid #00aeff;background-image: url(icons/drop.png);background-repeat: no-repeat;background-position: center center;background-color: #2c2c2c; }" )
			event.accept()
		else:
			event.ignore()
			print ('Ignore')

	def dropEvent(self, event):
		self.d_writer("Loading files - please wait...", 0,'green')
		# hack to update saved value.... fix later somehow
		try:
			print ('loc je:' + self.localization)
		except:
			self.localization = default_pref[0]
			self.convertor = default_pref[2]
		image_files = []
		office_files = []
		unknown_files = []
		for url in event.mimeData().urls():
			path = url.toLocalFile()
			extension = os.path.splitext(path)[1][1:].strip().lower()
			print (extension)
			# handle file
			if os.path.isfile(path):
				if extension == 'pdf':
					print ('Filetype: ' + str(extension))
					self.files = pdf_parse(self, path)
					self.d_writer(path, 0,'green')
					Window.table_reload(self, self.files)
				# handle images to list
				if extension in image_ext:
					image_files.append(path)
					print ('Image path:' + path)
				# handle offices files to list
				if extension in office_ext:
					office_files.append(path)
					print ('Office path:' + path)
				if extension not in office_ext and extension not in image_ext and extension not in next_ext:
						unknown_files.append(path)
				if extension == 'dat':
					dirname_ = (os.path.dirname(path) + '/')
					dirname = str(QFileDialog.getExistingDirectory(self, "Save file",dirname_))
					if dirname:
						with open(path, "rb") as tneffile:
							t = TNEF(tneffile.read())
							for a in t.attachments:
								with open(os.path.join(dirname,a.name.decode("utf-8")), "wb") as afp:
									afp.write(a.data)
							self.d_writer("Successfully wrote %i files" % len(t.attachments) + ' to: ' + dirname, 0)
		if image_files:
			if len(image_files) > 1:
				items = ["Convert to PDF " + (self.convertor),"Combine to PDF " + (self.convertor), "SmartCut", "Resize", "Parse"]
				text, okPressed = QInputDialog.getItem(self, "Action", "Action", items, 0, False)
				if not okPressed:
					return
			else:
				items = ["Convert to PDF", "SmartCut", "OCR", "Resize", "Parse"]
				text, okPressed = QInputDialog.getItem(self, "Action", "Action", items, 0, False)					
				if not okPressed:
					return
				if text == 'Convert to PDF':
					files = self.external_convert(extension, image_files, 'convert')
				if text == 'Combine to PDF':
					files = self.external_convert(extension, image_files, 'combine')
				if text == 'OCR':
					ocr_output = []
					for items in image_files:
						ocr = ocr_core(items, self.localization)
						ocr_output.append(ocr)
					ocr_output =  ''.join(ocr_output)
					self.d_writer(str(ocr_output), 0)
					if self.gb_debug.isHidden():
						self.toggleDebugWidget()
				if text == 'SmartCut':
					smartcut_files = []
					dialog = InputDialog_SmartCut()
					if dialog.exec():
						n_images, tresh = dialog.getInputs()
						for items in image_files:
							outputfiles = processFile(items, n_images, tresh)
							smartcut_files.append(outputfiles)
						# merge lists inside lists 
						smartcut_files = [j for i in smartcut_files for j in i]
						self.files = parse_img(self, smartcut_files)
						Window.table_reload(self, self.files)
						self.d_writer(str(smartcut_files), 0)
					else:
						dialog.close()
				if text == 'Parse':
					parse_files = []
					self.files = parse_img(self, image_files)
					Window.table_reload(self, self.files)
					# self.d_writer('Imported: ' + ' '.join(image_files), 0)
				if text == 'Resize':
					resize_files = []
					percent,okPressed = QInputDialog.getInt(self,"Resize image","Enter a percent", 50, 1, 100)
					for items in image_files:
						command, outputfiles = resizeimage(items, percent)
						resize_files.append(outputfiles)
					self.files = parse_img(self, resize_files)
					Window.table_reload(self, self.files)
					self.d_writer(str(resize_files), 0)
		# fix long names
		if office_files:
			if len(office_files) > 1:
				items = ["Convert to PDF","Combine to PDF"]
				text, okPressed = QInputDialog.getItem(self, "Action", "Action", items, 0, False)
				if not okPressed:
					return
				if text == 'Convert to PDF':
					self.d_writer("Converting to PDF (" + self.convertor + '): ' + extension, 0)
					files = self.external_convert(extension, office_files, 'convert')
				if text == 'Combine to PDF':
					files = self.external_convert(extension, office_files, 'combine')
			else:
				self.d_writer("Converting to PDF (" + self.convertor + '): ' + extension, 0)
				files = self.external_convert(extension, office_files, 'convert')
		# handle images
		if unknown_files:
			conv = QMessageBox()
			conv.setText("Warning One of files isnt propably supported. Do you still want to try import to PDF? (Clouconvert importer recomended)")
			conv.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
			conv = conv.exec()
			if conv == QMessageBox.Yes:
				self.external_convert(extension, unknown_files, 'convert')
			else:
				event.ignore()
		self.table.setStyleSheet("QTableView {background-image:none}" )

	def d_writer(self, message, append, *args):
	# fix for list input
		if isinstance (message, list):
			message = ('\n'.join(message))
		for ar in args:
			if ar == 'red':
				message = '<font color=red><b>' + message + '</b></font>'
			if ar == 'white':
				message = '<font color=white>' + message + '</font>'
			if ar == 'green':
				message = '<font color=green><b>' + message + '</b></font>'

		if append == 1:
			self.debuglist.append(message)
			# self.debuglist.moveCursor(QTextCursor.End, mode=QTextCursor.MoveAnchor)
			# self.debuglist.moveCursor(QTextCursor.StartOfLine, mode=QTextCursor.MoveAnchor)
			# self.debuglist.moveCursor(QTextCursor.End,mode=QTextCursor.KeepAnchor)
			# self.debuglist.textCursor().removeSelectedText()
			# self.debuglist.setText(self.debuglist.toPlainText() + message)
		if append == 0:
			self.debuglist.setText(message)

	def external_convert(self, ext, inputfile, setting):
		converts = []
		if setting == 'combine':
			outputdir = "/tmp/"
			print ('tmp folder selected')
			savedir = os.path.dirname(inputfile[0]) + '/'
		else:
			outputdir = os.path.dirname(inputfile[0]) + '/'

		if self.convertor == 'OpenOffice':
		# self.process = QProcess(self)
		# self.process.readyRead.connect(self.dataReady)
			for items in inputfile:
				print (items)
				command = ["/Applications/LibreOffice.app/Contents/MacOS/soffice", "--headless", "--convert-to", "pdf", items,"--outdir", outputdir]
				p = subprocess.Popen(command, stderr=subprocess.PIPE)
				output, err = p.communicate()
				if err == b'Error: source file could not be loaded\n':
					QMessageBox.about(self, "Error", "File: " + str(items) + " not supported.")
					break
				base = os.path.basename(items)
				base = os.path.splitext(base)[0]
				new_file = outputdir + base + '.pdf'
				converts.append(new_file)
			if setting == 'combine':
				merged_pdf = mergefiles(converts, savedir)
				# convert to list fix for later
				merged_pdf = (merged_pdf.split())
				self.files = pdf_parse(self,merged_pdf)
				self.d_writer('OpenOffice combining files to:', 0, 'green')
				self.d_writer(merged_pdf[0], 1)
				Window.table_reload(self, self.files)
			else:
				self.d_writer('OpenOffice converted files:', 0, 'green')
				self.d_writer(converts, 1)
				self.files = pdf_parse(self,converts)
				Window.table_reload(self, self.files)				
		elif self.convertor == 'CloudConvert':
			print ('CloudConvert')
			for items in inputfile:
				new_file, warning = cc_convert(items)
				if warning == "'NoneType' object is not subscriptable" or warning == "[Errno 2] No such file or directory: 'cc.json'":
					self.d_writer('missing API_KEY',0,'red')
					API_KEY,okPressed = QInputDialog.getText(self,"Warning ","Cloudconvert API key error, enter API key", QLineEdit.Normal, "")
					with open("cc.json", "w") as text_file:
						text_file.write(API_KEY)
					self.d_writer('API_KEY saved - Try import again', 0, 'red')
				elif new_file == None:
					print (warning)
					QMessageBox.about(self, "Warning", warning)
				elif new_file != None:
					print ('converting...')
					converts.append(new_file)
			if setting == 'combine':
				merged_pdf = mergefiles(converts, savedir)
				# convert to list fix for later
				merged_pdf = (merged_pdf.split())
				self.files = pdf_parse(self,merged_pdf)
				self.d_writer('CloudConvert combining files to:', 0, 'green')
				self.d_writer(merged_pdf[0], 1)
				Window.table_reload(self, self.files)
			else:
				self.files = pdf_parse(self,converts)
				Window.table_reload(self, self.files)

	def table_reload(self, inputfile):
		self.table = TableWidgetDragRows()
		headers = ["", "File", "Size", "Kind", "File size", "Pages", "Price", "Colors", 'File path']
		self.table.setColumnCount(len(headers))
		self.table.setHorizontalHeaderLabels(headers)
		# better is preview (printig etc)
		self.table.itemSelectionChanged.connect(self.get_page_size)
		self.table.doubleClicked.connect(self.open_tb)
		self.table.verticalHeader().setDefaultSectionSize(35)
		self.table.setFixedWidth(598)
		self.table.setColumnWidth(0, 35)
		self.table.setColumnWidth(1, 228)
		self.table.setColumnWidth(3, 34)
		self.table.setColumnWidth(4, 67)
		self.table.setColumnWidth(5, 34)
		self.table.setColumnWidth(6, 50)
		self.table.setColumnWidth(7, 52)
		self.table.verticalHeader().setVisible(False)
		self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		# ICONS
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
			self.on_selection_changed)
		# RIGHT CLICK MENU
		self.setContextMenuPolicy(Qt.CustomContextMenu)
		self.customContextMenuRequested.connect(self.contextMenuEvent)	 	
		self.mainLayout.addWidget(self.table,1,0,1,2)
		self.update()

	@pyqtSlot()
	def on_selection_changed(self):
		self.debuglist.clear()
		if self.selected_file_check() == 'pdf':
			print ('pdf')
			self.print_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.color_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.merge_pdf_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.split_pdf_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.compres_pdf_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.gray_pdf_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.raster_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.extract_b.show()
			self.Convert_b.hide()
			self.extract_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.gb_setting.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.crop_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.OCR_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
		elif self.selected_file_check() == 'image':
			print ('image')
			self.print_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.color_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.merge_pdf_b.setDisabled(bool(self.table.selectionModel().selectedRows()))
			self.split_pdf_b.setDisabled(bool(self.table.selectionModel().selectedRows()))
			self.compres_pdf_b.setDisabled(bool(self.table.selectionModel().selectedRows()))
			self.gray_pdf_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.raster_b.setDisabled(bool(self.table.selectionModel().selectedRows()))
			self.Convert_b.show()
			self.gb_setting.setEnabled(bool(self.table.selectionModel().selectedRows()))
			self.crop_b.setDisabled(bool(self.table.selectionModel().selectedRows()))
			self.OCR_b.setEnabled(bool(self.table.selectionModel().selectedRows()))
		else:
			print ('else')
			self.print_b.setDisabled(True)
			self.color_b.setDisabled(True)
			self.merge_pdf_b.setDisabled(True)
			self.split_pdf_b.setDisabled(True)
			self.compres_pdf_b.setDisabled(True)
			self.gray_pdf_b.setDisabled(True)
			self.raster_b.setDisabled(True)
			self.extract_b.setDisabled(True)
			self.gb_setting.setDisabled(True)
			self.crop_b.setDisabled(True)
			self.OCR_b.setDisabled(True)
		# pass

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
						file_path=index.sibling(row,8).data()
						revealfile(file_path,'')
					if action == revealAction:
						index=(self.table.selectionModel().currentIndex())
						row = self.table.currentRow()
						file_path=index.sibling(row,8).data()
						revealfile(file_path,'-R')
					if action == printAction:
						index=(self.table.selectionModel().currentIndex())
						row = self.table.currentRow()
						file_path=index.sibling(row,8).data()
						self.table_print()
					if action == previewAction:
						self.preview_window()

	def togglePrintWidget(self):
		print (self.gb_printers.isHidden())
		self.gb_printers.setHidden(not self.gb_printers.isHidden())
		self.gb_setting.setHidden(not self.gb_setting.isHidden())
		return True

	def togglePreviewWidget(self):

		PreviewWidget = 1
		# self.move(50, 50)
		self.gb_preview.setHidden(not self.gb_preview.isHidden())
		print (self.gb_preview.isHidden())
		if self.gb_preview.isHidden() == 1:
			self.setFixedSize(617, 650)
			self.resize(617, 650)
		else:
			self.setFixedSize(875, 650)
			self.resize(875, 650)
			try:
				self.get_page_size()
			except:
				pass
	def preview_window(self):
		if not self.table.selectionModel().selectedRows():
			pass
		else:
			for items in sorted(self.table.selectionModel().selectedRows()):
				row = items.row()
				index=(self.table.selectionModel().currentIndex())
				size=index.sibling(items.row(),2).data()
				filename=index.sibling(items.row(),1).data()
				filetype=index.sibling(items.row(),3).data()
				filepath=index.sibling(items.row(),8).data()
			self.widget = QDialog(self)
			self.widget.setWindowTitle(filepath + ' / ' + str(size));
			self.im_p = QLabel('Image_P',self.widget)
			self.im_p.setText('PREVIEW')
			self.im_pixmap = QPixmap('')
			if filetype.upper() in (name.upper() for name in image_ext):
				self.im_pixmap = QPixmap(filepath)
				self.im_p.setPixmap(self.im_pixmap)
			if filetype == 'pdf':
				filebytes = pdf_preview_generator(filepath,generate_marks=1)
				self.im_pixmap.loadFromData(filebytes)
				self.im_p.setPixmap(self.im_pixmap)
			sizeObject = QDesktopWidget().screenGeometry(0)# monitor size
			res = [(sizeObject.width()*92/100),(sizeObject.height()*92/100)]
			w, h = self.im_pixmap.width(), self.im_pixmap.height()
			# print ('photo size:' + str(w) + 'x' + str(h) + '/ monitor size:' + str(res[0]) + 'x' + str(res[1]))
			self.widget.setFixedSize(w, h)
			if w > res[0]:
				# print ('zmensuju sirka je veci')
				wpercent = (res[0] / float(w))
				# print (wpercent)
				self.widget.setFixedSize(w*wpercent, h*wpercent)
			if h > res[1]:
				# print ('zmensuju vyska je veci')
				wpercent = (res[1] / float(h))
				# print (wpercent)
				self.widget.setFixedSize(w*wpercent, h*wpercent)
			# print ('photo size:' + str(w) + 'x' + str(h) + '/ monitor size:' + str(res[0]) + 'x' + str(res[1]))
			self.im_p.setPixmap(self.im_pixmap.scaled(self.widget.size(),Qt.KeepAspectRatio))
			self.im_p.setMinimumSize(1, 1)
			self.labl_name = QLabel('Image_name',self.widget)
			self.labl_name.setStyleSheet("QLabel { background-color: '#2c2c2c'; font-size: 11px; height: 16px; padding: 5,5,5,5;}")
			self.labl_name.setText(filename)
			# self.labl_name.setFixedHeight(30)
			self.widget.exec_()

	class ExtendedQLabel(QLabel):
		def __init(self, parent):
			super().__init__(parent)
	
		clicked = pyqtSignal()
		rightClicked = pyqtSignal()

		def mousePressEvent(self, ev):
			if ev.button() == Qt.RightButton:
				self.rightClicked.emit()
			else:
				self.clicked.emit()

	def toggleDebugWidget(self):
		self.gb_debug.setHidden(not self.gb_debug.isHidden())

	def createPreview_layout(self):
		self.preview_layout = QHBoxLayout()
		try:
			pref_preview_state = (json_pref[0][7])
		except Exception as e:
			pref_preview_state = 1
		# PREVIEW GROUPBOX
		self.gb_preview = QGroupBox("Preview file")
		self.gb_preview.setVisible(not pref_preview_state)
		pbox = QVBoxLayout()
		# image
		self.image_label = self.ExtendedQLabel(self)
		self.image_label_pixmap = QPixmap('')
		self.image_label.setPixmap(self.image_label_pixmap)
		self.image_label.setAlignment(Qt.AlignCenter)
		self.image_label.clicked.connect(self.preview_window)
		self.labl_name = QLabel()
		self.labl_name.setStyleSheet("QLabel { background-color : '#2c2c2c'; border-radius: 5px; font-size: 12px;}")
		self.labl_name.setText('No file selected')
		self.labl_name.setAlignment(Qt.AlignCenter)
		self.labl_name.setFixedHeight(30)
		self.labl_name.setWordWrap(True)
		# infotable
		self.infotable = QTextEdit()
		self.infotable.setStyleSheet("QTextEdit { background-color : '#2c2c2c'; border-radius: 5px; font-size: 12px;}")
		self.infotable.acceptRichText()
		self.infotable.setText('Info')
		self.infotable.setReadOnly(True)
		self.infotable.setAlignment(Qt.AlignCenter)
		self.infotable.setFixedHeight(230)
		self.gb_preview.setLayout(pbox)
		# self.gb_preview.setFixedHeight(350)
		self.gb_preview.setFixedWidth(250)
		# self.printer_layout.addStretch()
		pbox.addWidget(self.image_label)
		pbox.addWidget(self.labl_name)
		pbox.addWidget(self.infotable)
		self.preview_layout.addWidget(self.gb_preview)
		self.setFixedWidth(self.sizeHint().width()+300)
		return pref_preview_state

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
		self.gb_debug.setFixedHeight(90)
		self.gb_debug.setFixedWidth(597)
		self.gb_debug.setContentsMargins(0, 0, 0, 0)
		self.gb_debug.setStyleSheet("border: 0px; border-radius: 0px; padding: 0px 0px 0px 0px;")
		dbox = QVBoxLayout()
		dbox.setContentsMargins(0, 0, 0, 0);
		self.gb_debug.setLayout(dbox)
		# debug
		self.debuglist = QTextEdit(self)
		self.d_writer('DEBUG:', 0, 'green')
		# self.debuglist.setAlignment(Qt.AlignJustify)
		self.debuglist.acceptRichText()
		self.debuglist.setReadOnly(True)
		self.debuglist.setFixedHeight(90)
		self.debuglist.setFixedWidth(597)
		dbox.addWidget(self.debuglist)
		self.gb_debug.toggled.connect(self.toggleDebugWidget)

		self.debug_layout.addWidget(self.gb_debug)

	def createButtons_layout(self):
		self.buttons_layout = QHBoxLayout()

		self.color_b = QPushButton('Colors', self)
		self.color_b.clicked.connect(self.loadcolors)
		self.buttons_layout.addWidget(self.color_b)
		self.color_b.setDisabled(True)
		# SPOJ PDF
		self.merge_pdf_b = QPushButton('Merge', self)
		self.merge_pdf_b.clicked.connect(self.merge_pdf)
		self.buttons_layout.addWidget(self.merge_pdf_b)
		self.merge_pdf_b.setDisabled(True)
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
		# GRAY PDF
		self.gray_pdf_b = QPushButton('To Gray', self)
		self.gray_pdf_b.clicked.connect(self.gray_pdf)
		self.buttons_layout.addWidget(self.gray_pdf_b)
		self.gray_pdf_b.setDisabled(True)
		# RASTROVANI PDF
		self.raster_b = QPushButton('Rasterize', self)
		self.raster_b.clicked.connect(self.rasterize_pdf)
		self.buttons_layout.addWidget(self.raster_b)
		self.raster_b.setDisabled(True)
		# CROP PDF WIP
		self.crop_b = QPushButton('SmartCrop', self)
		self.crop_b.clicked.connect(self.crop_pdf)
		# self.crop_b.clicked.connect(self.InputDialog_PDFcut)
		# InputDialog_PDFcut
		self.buttons_layout.addWidget(self.crop_b)
		self.crop_b.setDisabled(True)
		# EXTRACT IMAGES
		self.extract_b = QPushButton('Extract', self)
		self.extract_b.clicked.connect(self.extract_pdf)
		self.buttons_layout.addWidget(self.extract_b)
		self.extract_b.setDisabled(True)
		# OCR
		self.OCR_b = QPushButton('OCR', self)
		self.OCR_b.clicked.connect(self.ocr_maker)
		self.buttons_layout.addWidget(self.OCR_b)
		self.OCR_b.setDisabled(True)
		# CONVERT (only for image files)
		self.Convert_b = QPushButton('Convert', self)
		self.Convert_b.clicked.connect(self.convert_image)
		self.buttons_layout.addWidget(self.Convert_b)
		# # POCITANI TABULKY PDF
		# self.info_b = QPushButton('Info', self)
		# self.info_b.clicked.connect(self.info_tb)
		# self.buttons_layout.addWidget(self.info_b)
		# self.info_b.setDisabled(True)

	def compres_pdf(self):
		outputfiles = []
		if self.table.currentItem() == None:
			self.d_writer('Error - No files selected', 1, 'red')
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			outputfiles.append(file_path)
		debugstring, outputfiles = compres_this_file(outputfiles)
		self.files = pdf_parse(self,outputfiles)
		Window.table_reload(self, self.files)
		self.d_writer('File(s) compresed:', 1, 'green')
		self.d_writer(', '.join(debugstring),1)

	def gray_pdf(self):
		outputfiles = []
		if self.table.currentItem() == None:
			self.d_writer('Error - No files selected', 1, 'red')
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			outputfiles.append(file_path)
		if self.selected_file_check() == 'pdf':
			debugstring, outputfiles = gray_this_file(outputfiles,'pdf')
			self.files = pdf_parse(self,outputfiles)
		else:
			debugstring, outputfiles = gray_this_file(outputfiles,'jpg')
			self.files = parse_img(self,outputfiles)
		Window.table_reload(self, self.files)
		self.d_writer('Converted '+ str(len(outputfiles)) + ' pdf files to grayscale:', 0, 'green')
		self.d_writer(', '.join(debugstring),1)

	def ocr_maker(self):
		outputfiles = []
		if self.table.currentItem() == None:
			self.d_writer('Error - No files selected', 1, 'red')
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			pages=index.sibling(items.row(),5).data()
			outputfiles.append(file_path)
		if self.selected_file_check() == 'pdf':
			file,outputpdf = raster_this_file_(', '.join(outputfiles), 300,0,True,int(pages))
			for items in file:
				ocr = ocr_core(items, self.localization)
				self.d_writer(str(ocr), 1)
			debugstring, outputfiles = gray_this_file(outputfiles,'pdf')
			self.files = pdf_parse(self,outputfiles)
		else:
			# only singe item for now
			for items in outputfiles:
				ocr = ocr_core(items, self.localization)
				self.d_writer(str(ocr), 1)

	def rasterize_pdf(self):
		outputfiles = []
		if self.table.currentItem() == None:
			self.d_writer('Error - No files selected', 1, 'red')
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			outputfiles.append(file_path)
			desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DialogResetButton))
		debugstring, outputfiles = raster_this_file(outputfiles, default_pref[1])
		self.files = pdf_parse(self,outputfiles)
		Window.table_reload(self, self.files)
		self.d_writer('File(s) rasterized:', 1, 'green')
		self.d_writer(', '.join(debugstring),1)

	def convert_image(self):
		outputfiles = []
		if self.table.currentItem() == None:
			self.d_writer('Error - No files selected', 1, 'red')
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			outputfiles.append(file_path)
		debugstring, outputfiles = convert_this_file(outputfiles, default_pref[1])
		self.files = pdf_parse(self,outputfiles)
		Window.table_reload(self, self.files)
		self.d_writer('File(s) converted:', 1, 'green')
		self.d_writer(', '.join(debugstring),1)

	def crop_pdf(self):
		outputfiles = []
		if self.table.currentItem() == None:
			self.d_writer('Error - No files selected', 1, 'red')
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			outputfiles.append(file_path)
			desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DialogResetButton))
		pdf_dialog = InputDialog_PDFcut()
		if pdf_dialog.exec():
			multipage, croppage, margin = pdf_dialog.getInputs()
			debugstring, outputfile = convertor(file_path,72,croppage=croppage-1,multipage=multipage,margin=margin)
			outputfiles.append(outputfile)
			print (outputfiles)
			self.files = pdf_parse(self,outputfiles)
			Window.table_reload(self, self.files)
			self.d_writer(debugstring, 1, 'green')
		else:
			pdf_dialog.close()

	def extract_pdf(self):
		outputfiles = []
		if self.table.currentItem() == None:
			self.d_writer('Error - No files selected', 1, 'red')
			return
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			outputfiles.append(file_path)
			desktop_icon = QIcon(QApplication.style().standardIcon(QStyle.SP_DialogResetButton))
		try:
			outputfiles = extractfiles(file_path)
		except Exception as e:
			self.d_writer('Error - Importing error' + str(e), 1, 'red')
			return
		self.files = parse_img(self,outputfiles)
		Window.table_reload(self, self.files)
		self.d_writer('Extracted images:', 1, 'green')
		self.d_writer(str(outputfiles),1)

	def selected_file_check(self):
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			ftype=index.sibling(items.row(),3).data()
			if ftype == 'pdf':
				return 'pdf'
			if ftype == '':
				pass
			else:
				return 'image'

	def info_tb(self):
		soucet = []
		stranky = []
		_files = []
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			soucet.append(row)
			index=(self.table.selectionModel().currentIndex())
			info=index.sibling(items.row(),5).data()
			f_path=index.sibling(items.row(),8).data()
			ftype=index.sibling(items.row(),3).data()
			stranky.append(int(info))
			_files.append(f_path)
		if ftype == 'pdf':
			pdf_info = file_info(_files, 'pdf')
			celkem = (str(len(soucet)) + '  PDF files, ' + str(sum(stranky)) + ' pages')
			self.d_writer(str(celkem),0,'green')
			self.d_writer(pdf_info,1)
		else:
			jpg_info = file_info(_files, 'image')
			self.d_writer(' '.join(_files),0,'green')
			self.d_writer(jpg_info,1)


	def split_pdf(self):
		green_ = (QColor(10, 200, 50))
		for items in sorted(self.table.selectionModel().selectedRows()):
			index=(self.table.selectionModel().currentIndex())
			row = items.row()
			if int(index.sibling(items.row(),5).data()) < 2:
				self.d_writer('Error - Not enough files to split', 1, 'red')
			else:
				index=(self.table.selectionModel().currentIndex())
				file_path=index.sibling(items.row(),8).data()
				split_pdf = splitfiles(file_path)
				self.files = pdf_parse(self,split_pdf)
				self.d_writer('Created '+ str(len(split_pdf)) + ' pdf files:', 0, 'green')
				self.d_writer(split_pdf, 1)
				Window.table_reload(self, self.files)
				# self.table.item((len(rows)-1), 1).setForeground(green_)

	def merge_pdf(self):
		green_ = (QColor(10, 200, 50))
		combinefiles = []
		table = sorted(self.table.selectionModel().selectedRows())
		if len(table) <= 1:
			self.d_writer("Error - Choose two or more files to combine PDFs. At least two files...", 1, 'red')
			# QMessageBox.information(self, 'Error', 'Choose two or more files to combine PDFs. At least two files....', QMessageBox.Ok)
		else:
			for items in table:
				row = items.row()
				# print (row)
				index=(self.table.selectionModel().currentIndex())
				file_path=index.sibling(items.row(),8).data()
				combinefiles.append(file_path)
			merged_pdf = mergefiles(combinefiles, 0)
			self.d_writer('New combined PDF created:', 1,'green')
			self.d_writer(merged_pdf, 1)
			merged_pdf = (merged_pdf.split())
			self.files = pdf_parse(self,merged_pdf)
			Window.table_reload(self, self.files)
			# self.table.item((len(rows)-1), 1).setForeground(green_)

	def loadcolors(self):
		green_ = (QColor(10, 200, 50))
		black_ = (QBrush(QColor(200, 200, 200)))
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
		if druh == 'pdf':
			for items in sorted(self.table.selectionModel().selectedRows()):
				row = items.row()
				index=(self.table.selectionModel().currentIndex())
				file_path=index.sibling(items.row(),8).data()
				outputfiles.append(file_path)
				for items in outputfiles:
					nc = count_page_types(items)
					if not nc:
						self.table.item(row, 7).setText('BLACK')
						self.table.item(row, 7).setForeground(black_)
						self.d_writer("Document is all grayscale", 1, 'red')
						self.table.item(row, 7).setFont(font)
						self.table.clearSelection()
					else:
						self.table.item(row, 7).setText('CMYK')
						self.table.item(row, 7).setForeground(green_)
						self.table.item(row, 7).setFont(font)
						self.d_writer("Color pages:", 0, 'green')
						self.d_writer(' ' +  ', '.join(map(str, nc)), 1)
						self.table.clearSelection()
		else:
			for items in sorted(self.table.selectionModel().selectedRows()):
				row = items.row()
				index=(self.table.selectionModel().currentIndex())
				file_path=index.sibling(items.row(),8).data()
				outputfiles.append(file_path)
				for items in outputfiles:
					image_info = getimageinfo(items)
					print (image_info)
					print (items)
					self.d_writer(str(image_info[1]), 0, 'green')
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
		self.gb_printers.setFixedWidth(202)
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
		self.vbox2 = QGridLayout()
		self.gb_setting.setFixedHeight(150)
		self.gb_setting.setFixedWidth(391)
		self.gb_setting.setVisible(not pref_printers_state)
		self.gb_setting.setDisabled(True)

		# # POČET KOPII
		copies_Label = QLabel("Copies:")
		self.copies = QSpinBox()
		self.copies.setValue(1)
		self.copies.setMinimum(1)
		self.copies.setMaximum(999)
		self.copies.setFixedSize(60, 25)
		self.gb_setting.setLayout(self.vbox2)
		# PAPERFORMAT
		paper_Label = QLabel("Paper size:")
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
		fit_to_size_Label = QLabel("Paper size:")
		self.fit_to_size = QCheckBox('Fit to page', self)
		# ORIENTATION L/T
		self.btn_orientation = QPushButton()
		self._icon = QIcon()
		self._icon.addPixmap(QPixmap('icons/long.png'))
		self.btn_orientation.setCheckable(True)
		self.btn_orientation.setIcon(self._icon)
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

		# # COLORS
		btn_colors_Label = QLabel("Color:")
		self.btn_colors = QComboBox(self)
		self.btn_colors.addItem('Auto')
		self.btn_colors.addItem('Color')
		self.btn_colors.addItem('Gray')
		self.btn_colors.activated[str].connect(self.color_box_change)

		self.print_b = QPushButton('Print', self)
		self.print_b.clicked.connect(self.table_print)
		self.print_b.setDisabled(True)
		# self.buttons_layout.addWidget(self.print_b)
		# self.btn_colors= QPushButton()
		# self._icon_colors = QIcon()
		# self._icon_colors.addPixmap(QPixmap('icons/colors_auto.png'))
		# self.btn_colors.setIcon(self._icon_colors)
		# self.btn_colors.setCheckable(True)
		# self.btn_colors.setIconSize(QSize(23,38))
		# self.btn_colors.setChecked(True)
		# self.btn_colors.toggled.connect(lambda: self.icon_change('icons/colors_on.png','icons/colors_off.png',self.btn_colors))

		self.vbox2.addWidget(copies_Label, 0,0)
		self.vbox2.addWidget(self.copies, 0,1)
		self.vbox2.addWidget(paper_Label, 0,2)
		self.vbox2.addWidget(self.papersize, 0,3)
		self.vbox2.addWidget(self.lp_two_sided, 1,0)
		self.vbox2.addWidget(self.btn_orientation, 1,1)
		self.vbox2.addWidget(self.btn_collate, 1,2)
		self.vbox2.addWidget(btn_colors_Label, 2,0)
		self.vbox2.addWidget(self.btn_colors, 2,1)
		self.vbox2.addWidget(self.print_b, 2,3)
		self.vbox2.addWidget(self.fit_to_size, 1,3)


		self.printer_layout.addWidget(self.gb_setting)
		self.printer_layout.addStretch()

	def papersize_box_change(self, text):
			self.d_writer(text,0)
			print (text)
			return text

	def color_box_change(self, text):
			self.d_writer(text,0)
			return text

	def togle_btn(self):
		if self.lp_two_sided.isChecked():
			self.btn_orientation.setVisible(True)
		else:
			self.btn_orientation.setVisible(False)

	def icon_change(self, _on, _off, name):
		# print (name.isChecked())
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
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			outputfiles.append(file_path)
			tiskarna_okPressed = self.printer_tb.currentItem()
			tiskarna_okPressed = (tiskarna_ok.text())
		debugstring = print_this_file(outputfiles, tiskarna_ok, self.lp_two_sided.isChecked(), self.btn_orientation.isChecked(), str(self.copies.value()), self.papersize.currentText(), self.fit_to_size.isChecked(), self.btn_collate.isChecked(), self.btn_colors.currentText())
		self.d_writer('Printing setting:',0,'green')
		self.d_writer(debugstring,1,'white')

	def open_tb(self):
		green_ = (QColor(80, 80, 80))
		black_ = (QBrush(QColor(0, 0, 0)))
		outputfiles = []
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			file_path=index.sibling(items.row(),8).data()
			outputfiles.append(file_path)
		revealfile(outputfiles,'')
		self.d_writer('Opened: ' + str(outputfiles),0, 'green')

	def open_printer_tb(self):
		for items in sorted(self.printer_tb.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			tiskarna = (printers[row])
		open_printer(tiskarna)
		self.d_writer('Printing setting: ' + tiskarna,0, 'green')

	def get_page_size(self):
		for items in sorted(self.table.selectionModel().selectedRows()):
			row = items.row()
			index=(self.table.selectionModel().currentIndex())
			size=index.sibling(items.row(),2).data()
			filename=index.sibling(items.row(),1).data()
			filetype=index.sibling(items.row(),3).data()
			filepath=index.sibling(items.row(),8).data()
		try:
			if not self.gb_preview.isHidden():
				self.image_label.show()
				self.labl_name.setText(filename+'.'+filetype)
				# self.infotable.setFixedHeight(230)
				if filetype.upper() in (name.upper() for name in image_ext):
					image_info = file_info_new(filepath.split(','), 'image')
					self.infotable.setText(image_info)
					self.image_label_pixmap = QPixmap(filepath)
					self.image_label.setPixmap(self.image_label_pixmap)
				if filetype == 'pdf':
					pdf_info = file_info_new(filepath.split(','), 'pdf')
					self.infotable.setText(' '.join(pdf_info))
					filebytes = pdf_preview_generator(filepath,generate_marks=1)
					self.image_label_pixmap.loadFromData(filebytes)
					self.image_label.setPixmap(self.image_label_pixmap)
			w, h = self.image_label_pixmap.width(), self.image_label_pixmap.height()
			w_l, h_l = self.image_label.width(), self.image_label.height()
			# Change box according to aspect ratio...
			self.image_label.setFixedHeight(325)
			self.image_label.setPixmap(self.image_label_pixmap.scaled(self.image_label.size(),Qt.KeepAspectRatio))
			# print (self.image_label_pixmap.scaled(self.image_label.size(),Qt.KeepAspectRatio).width())
			# print (self.image_label_pixmap.scaled(self.image_label.size(),Qt.KeepAspectRatio).height())
			height_ = self.image_label_pixmap.scaled(self.image_label.size(),Qt.KeepAspectRatio).height() - 325
			self.infotable.setFixedHeight(230 - height_)
			self.image_label.setMinimumSize(1, 1)
			# change with of info
			self.labl_name.setText(filename+'.'+filetype)
			if size[-2:] == 'px':
				papers[5] = 'not supported'
			else: 
				papers[5] = size[:-3]
				self.papersize.clear()
			for items in papers:
				self.papersize.addItem(items)
			self.papersize.update()
			# self.d_writer('Page size: ' + size,0, 'green')
		except Exception as e:
				# print (e)
				# print ('error')
				self.infotable.clear()
				self.image_label.clear()
				self.labl_name.setText('No file selected')

	def keyPressEvent(self,e):
		if e.key() == Qt.Key_Delete:
			for items in sorted(self.table.selectionModel().selectedRows()):
				row = items.row()
				del(self.files[row]) 
			Window.table_reload(self, self.files)

		if e.key() == Qt.Key_F1:
			self.preview_window()

	def deleteClicked(self):
		row = self.table.currentRow()
		self.table.removeRow(row)

	def openFileNamesDialog(self):
		options = QFileDialog.Options()
		soubor, _ = QFileDialog.getOpenFileNames(self,"QFileDialog.getOpenFileNames()", "",";Pdf Files (*.pdf)", options=options)
		if soubor:
			self.files = pdf_parse(self,soubor)
			self.table_reload(self.files)
			self.d_writer('Loaded: ' + str(soubor),0,'green')

if __name__ == '__main__':
	json_pref,printers,default_pref = load_preferences()
	app = QApplication(sys.argv)
	path = os.path.join(os.path.dirname(sys.modules[__name__].__file__), 'icons/printer.png')
	app.setWindowIcon(QIcon(path))
	w = Window()
	darkmode()
	log = ('OS: '  + system + ': ' + sys_support + ' / boot time: ' + str((time.time() - start_time))[:5] + ' seconds')
	w.d_writer(log,1)
	w.showNormal()
	sys.exit(app.exec_())