# #!/usr/bin/python3
# # -*- coding: utf-8 -*-
# import sys
# from PyQt5.QtWidgets import QWidget, QApplication, QComboBox, QLabel, QPushButton
# from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush, QPainter, QPixmap
# from PyQt5.QtCore import Qt
# from PyQt5 import QtCore, QtGui, QtWidgets

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import numpy


class livecropwindow(QDialog):
	def __init__(self, input_file):
		super(livecropwindow, self).__init__()
		self.defined_crop = False

		self.crop = QPushButton('Crop', self)
		self.crop.clicked.connect(self.cropimage)
		self.begin = QPoint()
		self.end = QPoint()
		if isinstance (input_file, str):
			res, self.w, self.h = self.get_sizes(input_file)
		else:
			im_pixmap = QPixmap('')
			# print ('PDF')
			im_pixmap.loadFromData(input_file)
			res, self.w, self.h = self.get_sizes(im_pixmap)
		self.setFixedSize(self.w, self.h)
		print ('show window')
		self.show()

	def get_sizes(self,input_file):
		self.pixmap = QPixmap(input_file)
		self.w, self.h = self.pixmap.width(), self.pixmap.height()
		sizeObject = QDesktopWidget().screenGeometry(0)# monitor size
		res = [(int(sizeObject.width()*92/100)),(int(sizeObject.height()*92/100))]
		if self.w > res[0]:
			# print ('zmensuju sirka je veci')
			wpercent = (res[0] / float(self.w))
			# print (wpercent)
			self.setFixedSize(self.w*wpercent, self.h*wpercent)
		if self.h > res[1]:
			# print ('zmensuju vyska je veci')
			wpercent = (res[1] / float(self.h))
			# print (wpercent)
			self.setFixedSize(self.w*wpercent, self.h*wpercent)
		else:
			print ('neni potreba zmensovat')

		print (res)
		return res, self.w, self.h

	def paintEvent(self, event):
		qp = QPainter(self)
		qp.drawPixmap(self.rect(), self.pixmap)
		pen = QPen(Qt.black, 2, Qt.DashDotLine)
		qp.setPen(pen)
		pen.setStyle(Qt.DashLine)
		qp.setPen(pen)
		brush = QBrush()
		brush.setColor(QColor(Qt.white))
		brush.setStyle(Qt.Dense6Pattern)
		qp.setBrush(brush)
		# qp.setBrush(QColor(Qt.red))
		# qp.setColor(QtGui.QColor(42, 42, 42, 255))
		self.selection = qp.drawRect(QRect(self.begin, self.end))
		# page_width_center = self.w/2
		# page_height_center = self.h/2
		# self.coordinates = str(self.w) + ' x ' +  str(self.h) + ' px'
		# # sizeinfo
		# painter.setPen(QColor(Qt.gray))
		# painter.setFont(QFont("Arial", 18))
		# painter.setBrush(Qt.blue);
		# painter.setRenderHint(QPainter.Antialiasing);
		# painter.drawText(250, 23, 'bingo')

		# # livenum 
		# livesize = QPainter(self)
		qp.setPen(QColor(Qt.red))
		qp.setFont(QFont("Arial", 14))
		qp.drawText(80, 20, 'image size: ' + str(self.w) + ' x ' +  str(self.h) + ' px')
		qp.end()

	def mousePressEvent(self, event):
		if self.defined_crop == False:
			# print ('xxxxx')
			self.begin = event.pos()
			self.end = event.pos()
			self.update()
		elif event.buttons () == Qt.RightButton and self.defined_crop == True :
			self.defined_crop = False
			print ('Right click')
			self.begin = event.pos()
			self.end = event.pos()	
			self.update()
		else:
			print ('todooo')
			# print (str(QCursor.pos().x()) + ' x ' + str(QCursor.pos().y()))
			# print (self.begin.x(),self.begin.y(),self.end.x(),self.end.y())
			# if QCursor.pos().x() > self.begin.x():
			# 	# if QCursor.pos().x() < self.end.x():
			# 	# 	QApplication.setOverrideCursor(QCursor(Qt.OpenHandCursor))
			# 	print ('uvnitr')
			# else: 
			# 	print ('venku')



	def mouseMoveEvent(self, event):
		self.end = event.pos()
		self.update()

	def mouseReleaseEvent(self, event):
		self.defined_crop = True
		self.update()

	def cropimage(self):
		self.crop_text = [self.begin.x(),self.begin.y(),self.end.x(),self.end.y()]
		self.accept()
		return self.crop_text

	def GetValue(self):
		return self.crop_text

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = livecropwindow("/Users/jandevera/Desktop/1.png")
	ex.show()
	sys.exit(app.exec_())
