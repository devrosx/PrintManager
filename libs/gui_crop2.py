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
		self.move(5, 5)
		self.crop = QPushButton('Crop', self)
		self.crop.clicked.connect(self.cropimage)
		self.begin = QPoint()
		self.end = QPoint()
		if isinstance (input_file, str):
			res, self.w, self.h, self.wpercent, self.hpercent, self.number = self.get_sizes(input_file)
		else:
			im_pixmap = QPixmap('')
			im_pixmap.loadFromData(input_file)
			res, self.w, self.h, self.wpercent, self.hpercent, self.number = self.get_sizes(im_pixmap)
		self.setFixedSize(self.wpercent*self.w, self.hpercent*self.h)
		print ('nova velikost:' + str(self.wpercent*self.w) + 'x' + str(self.hpercent*self.h))
		print ('show window')
		self.show()

	def get_sizes(self,input_file):
		self.pixmap = QPixmap(input_file)
		self.w, self.h = self.pixmap.width(), self.pixmap.height()
		sizeObject = QDesktopWidget().screenGeometry(0)# monitor size
		res = [(int(sizeObject.width()*92/100)),(int(sizeObject.height()*92/100))]
		print ('puvodni obraz:'+ str(self.w) + ' x ' +  str(self.h))
		if self.w > res[0]:
			print ('zmensuju Sirka je veci')
			self.wpercent = (res[0] / float(self.w))
			self.hpercent = self.wpercent
			self.number = self.w/ res[0]
			print ('xxxx' + str(self.number))
			# print ('procenta:' + str(self.wpercent))
			# self.setFixedSize(self.w*wpercent, self.h*wpercent)
		if self.h > res[1]:
			print ('zmensuju Vyska je veci')
			self.hpercent = (res[1] / float(self.h))
			self.wpercent = self.hpercent

			self.number = self.w/ res[1]
			print ('xxxx' + str(self.number))
			# print ('procenta:' + str(self.hpercent))
			# self.setFixedSize(self.w*wpercent, self.h*wpercent)
		else:
			print ('neni potreba zmensovat')
			self.wpercent = 1
			self.hpercent = 1
			self.number = 0
		# self.im_pixmap.setPixmap(self.im_pixmap.scaled(self.widget.size(),Qt.KeepAspectRatio))
		# self.im_pixmap.setMinimumSize(1, 1)
		print ('res'  +str(res))
		print ('wpercent:' + str(100 * self.wpercent))
		print ('hpercent: ' + str(100 * self.hpercent))
		return res, self.w, self.h, self.wpercent, self.hpercent, self.number

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
		self.selection = qp.drawRect(QRect(self.begin, self.end))
		centerCoord = (self.begin.x()+((self.end.x()-self.begin.x())/2), (self.begin.y()+((self.end.y()-self.begin.y())/2)))
		# https://stackoverflow.com/questions/41982006/compute-the-centroid-of-a-rectangle-in-python
		# print (centerCoord)
		qp.setPen(QPen(Qt.black,  2, Qt.SolidLine))
		qp.drawEllipse(centerCoord[0], centerCoord[1], 2, 2)
		qp.setPen(QColor(Qt.black))
		font = qp.font()
		font.setBold(True)
		qp.setFont(font)
		qp.drawText(80, 20, 'image size: ' + str(self.w) + ' x ' +  str(self.h) + ' px')
		# qp.drawText(centerCoord[0], centerCoord[1], 'Crop size: ' + str(self.begin.x()-self.end.x()) + ' x ' +  str(self.begin.y()-self.end.y()) + ' px')
		qp.drawText(self.begin.x(),self.begin.y()-5, 'Crop size: ' + str(self.begin.x()-self.end.x()) + ' x ' +  str(self.begin.y()-self.end.y()) + ' px')

		qp.end()

	def mousePressEvent(self, event):
		if self.defined_crop == False:
			print ('xxxxx')
			if self.hpercent != 1:
				print ('image to big')
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
			self.defined_crop = False
			self.update()
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
		if self.hpercent != 1:
			self.crop_text = [self.begin.x(),self.begin.y(),self.end.x(),self.end.y()]
			print (self.crop_text)
			print ('image to big')
			self.crop_text = [self.ucalc(self.begin.x()),self.ucalc(self.begin.y()),self.ucalc(self.end.x()),self.ucalc(self.end.y())]
			print (self.crop_text)
		else:
			self.crop_text = [self.begin.x(),self.begin.y(),self.end.x(),self.end.y()]
		self.accept()
		return self.crop_text

	def ucalc(self, p_input):
		fixed_input = p_input * self.number
		return fixed_input

	def GetValue(self):
		return self.crop_text

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = livecropwindow("/Users/jandevera/Desktop/15.jpg")
	ex.show()
	sys.exit(app.exec_())
