#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QWidget, QApplication, QComboBox, QLabel
from PyQt5.QtGui import QPainter, QColor, QFont, QPen, QBrush
from PyQt5.QtCore import Qt

print_pages = [[74,105,'A7'],[105,148,'A6'],[148,210,'A5'],[210,297,'A4'],[297,420,'A3'],[420,594,'A2'],[594,841,'A1'],[841,1189,'A0']]
window_size = [405,405]

class MyFirstGUI(QWidget):
	
	def __init__(self):
		super(MyFirstGUI, self).__init__()
		self.setFixedSize(window_size[0], window_size[1])
		self.flag = False
		self.orientace = 'P'
		# sizes
		self.combo = QComboBox(self)
		for items in print_pages:
			self.combo.addItem(str(items[2]),items)
		self.combo.move(348, 373)
		self.combo.activated.connect(self.onChangedSize)
		# orientace
		self.combo_or = QComboBox(self)
		self.combo_or.addItem('Portrait','P')
		self.combo_or.addItem('Landscape','L')
		self.combo_or.move(318, 343)
		self.combo_or.activated.connect(self.onChangedOr)       
		
	def initUI(self):      
		self.setWindowTitle('print preview')
		self.show()

	def onChangedOr(self, index):
		self.orientace = self.combo_or.itemData(index)
		print(self.combo_or.itemText(index))
		self.update()

	def onChangedSize(self, index):
		self.flag = True
		self.page_info = self.combo.itemData(index)
		print(self.page_info)
		self.update()

	def paintEvent(self, e):
		if self.flag:
			qp = QPainter()
			qp.begin(self)
			self.showprintpage(qp, self.page_info, self.orientace)
			qp.end()
	
	def showprintpage(self, qp, pagesize, orient):
		print (orient)
		# fit to page trick
		padding = 10
		no_print = 5
		if orient == 'L':
			pagesize[0], pagesize[1] = pagesize[1], pagesize[0]
			orient = 'Landscape'
			if pagesize[0] > window_size[0]:
				page_width = (((100 * (pagesize[0] - window_size[0]+padding) / pagesize[0])-100)/-100) * pagesize[0]
				page_height = (((100 * (pagesize[0] - window_size[0]+padding) / pagesize[0])-100)/-100) * pagesize[1]
				print ('musim zmensit landscape: ' + str(page_width) + ' x '  + str(page_height))
			else:
				page_width = pagesize[0]
				page_height = pagesize[1]
		else:
			orient = 'Portrait'
			if pagesize[1] > window_size[1]:
				page_width = (((100 * (pagesize[1] - window_size[1]+padding) / pagesize[1])-100)/-100) * pagesize[0]
				page_height = (((100 * (pagesize[1] - window_size[1]+padding) / pagesize[1])-100)/-100) * pagesize[1]
				print ('musim zmensit portrait: ' + str(page_width) + ' x '  + str(page_height))
			else:
				page_width = pagesize[0]
				page_height = pagesize[1]

		page_width_center = page_width/2
		page_height_center = page_height/2
		d_height = qp.device().height()/2
		d_width = qp.device().width()/2
		# draw page frame
		qp.setPen(QPen(Qt.black,  2, Qt.SolidLine))
		qp.setBrush(QBrush(Qt.white))
		qp.drawRect(d_width - page_width_center, d_height - page_height_center, page_width, page_height)
		# draw non printing area 
		qp.setPen(QPen(Qt.cyan,  1, Qt.SolidLine))
		qp.drawRect(d_width - page_width_center + no_print, d_height - page_height_center + no_print, page_width - no_print*2, page_height - no_print*2)
		# draw page size
		qp.setPen(QColor(Qt.black))
		qp.setFont(QFont("Arial", 14, QFont.Bold))
		qp.drawText(d_width - page_width_center+15, d_height - page_height_center+20, pagesize[2])
		qp.setFont(QFont("Arial", 13))
		qp.setPen(QColor(Qt.gray))
		qp.drawText(d_width - page_width_center+40, d_height - page_height_center+20, (str(pagesize[0]) + ' x ' + str(pagesize[1]) + ' mm ' + orient))
		# draw letter on it
		qp.setPen(QColor(Qt.black))
		qp.setFont(QFont("Arial", 80, QFont.Bold))
		qp.drawText(d_width-27, d_height+30, 'R')# hack how to calculate center

if __name__ == '__main__':
	app = QApplication(sys.argv)
	gui = MyFirstGUI()
	gui.show()
	sys.exit(app.exec_())