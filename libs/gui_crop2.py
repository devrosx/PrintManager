# #!/usr/bin/python3
import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
# import numpy

# clean code
class livecropwindow(QDialog):
	def __init__(self, input_file):
		super(livecropwindow, self).__init__()
		# crop button
		self.move(5, 5)
		self.defined_crop = False
		self.crop = QPushButton('Crop', self)
		self.crop.clicked.connect(self.cropimage)
		self.begin = QPoint()
		self.end = QPoint()
		self.handle_offsets = (QPoint(8, 8), QPoint(-1, 8), QPoint(8, -1), QPoint(-1, -1))
		# check str or list
		if isinstance (input_file, str):
			res, self.w, self.h, self.wpercent, self.hpercent, self.percent = self.get_sizes(input_file)
		else:
			im_pixmap = QPixmap('')
			im_pixmap.loadFromData(input_file)
			res, self.w, self.h, self.wpercent, self.hpercent, self.percent = self.get_sizes(im_pixmap)
		self.setFixedSize(self.wpercent*self.w, self.hpercent*self.h)
		print ('new size:' + str(self.wpercent*self.w) + 'x' + str(self.hpercent*self.h))
		print ('show window')
		self.show()

	def get_sizes(self,input_file):
		self.pixmap = QPixmap(input_file)
		self.w, self.h = self.pixmap.width(), self.pixmap.height()
		sizeObject = QDesktopWidget().screenGeometry(0)# monitor size
		res = [(int(sizeObject.width()*92/100)),(int(sizeObject.height()*92/100))]
		print ('original size:'+ str(self.w) + ' x ' +  str(self.h))
		if self.w > res[0]:
			print ('shrink width')
			self.wpercent = (res[0] / float(self.w))
			self.hpercent = self.wpercent
			self.percent = self.w/ res[0]
			print ('xxxx' + str(self.percent))
		if self.h > res[1]:
			print ('shrink height')
			self.hpercent = (res[1] / float(self.h))
			self.wpercent = self.hpercent

			self.percent = self.w/ res[1]
			print ('xxxx' + str(self.percent))
		else:
			print ('no neeed to shrink image')
			self.wpercent,self.hpercent = 1,1
			self.percent = 0
		print ('res'  +str(res) + ' hpercent: ' + str(100 * self.hpercent) + ' wpercent:' + str(100 * self.wpercent))
		return res, self.w, self.h, self.wpercent, self.hpercent, self.percent

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
		self.clip_rect = qp.drawRect(QRect(self.begin, self.end))
		centerCoord = (self.begin.x()+((self.end.x()-self.begin.x())/2), (self.begin.y()+((self.end.y()-self.begin.y())/2)))
		# qp.drawRect(self.clip_rect)
		# for i in range(4):
		# 	qp.drawRect(self.corner(i))
		# path = QPainterPath()
		# path.addRect(QRectF(self.clip_rect))
		# https://stackoverflow.com/questions/41982006/compute-the-centroid-of-a-rectangle-in-python
		# print (centerCoord)
		# font
		qp.setPen(QPen(Qt.white,  2))
		qp.drawEllipse(centerCoord[0], centerCoord[1], 2, 2)
		qp.setPen(QColor(Qt.black))
		font = qp.font()
		path1 = QPainterPath()
		font.setBold(True)
		qp.setFont(font)
		qp.setPen(QColor(Qt.white))
		qp.drawText(80, 20, 'image size: ' + str(self.w) + ' x ' +  str(self.h) + ' px')
		# qp.drawText(centerCoord[0], centerCoord[1], 'Crop size: ' + str(self.begin.x()-self.end.x()) + ' x ' +  str(self.begin.y()-self.end.y()) + ' px')
		qp.drawText(self.begin.x(),self.begin.y()-5, 'Crop size: ' + str(self.begin.x()-self.end.x()) + ' x ' +  str(self.begin.y()-self.end.y()) + ' px')

		qp.end()

	def mousePressEvent(self, event):
		if self.defined_crop == False:
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

	def corner(self, number):
	
		if number == 0:
			return QRect(self.clip_rect.topLeft() - self.handle_offsets[0], QSize(8, 8))
		elif number == 1:
			return QRect(self.clip_rect.topRight() - self.handle_offsets[1], QSize(8, 8))
		elif number == 2:
			return QRect(self.clip_rect.bottomLeft() - self.handle_offsets[2], QSize(8, 8))
		elif number == 3:
			return QRect(self.clip_rect.bottomRight() - self.handle_offsets[3], QSize(8, 8))



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
		fixed_input = p_input * self.percent
		return fixed_input

	def GetValue(self):
		return self.crop_text

if __name__ == '__main__':
	app = QApplication(sys.argv)
	ex = livecropwindow("/Users/jandevera/Desktop/Screenshot 2020-06-08 at 00.23.06.png")
	ex.show()
	sys.exit(app.exec_())
