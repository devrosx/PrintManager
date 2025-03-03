#!/usr/bin/python3
import sys
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtCore import *

# Clean code
class LiveCropWindow(QDialog):
    def __init__(self, input_file):
        super().__init__()
        self.setWindowTitle(input_file)
        # Inicializace proměnných
        self.defined_crop = False
        self.crop = QPushButton('Crop', self)
        self.crop.clicked.connect(self.crop_image)
        self.begin = QPoint()
        self.end = QPoint()
        self.handle_offsets = (QPoint(8, 8), QPoint(-1, 8), QPoint(8, -1), QPoint(-1, -1))

        # Kontrola typu input_file
        if isinstance(input_file, str):
            res, self.w, self.h, self.wpercent, self.hpercent, self.percent = self.get_sizes(input_file)
        else:
            im_pixmap = QPixmap()
            im_pixmap.loadFromData(input_file)
            res, self.w, self.h, self.wpercent, self.hpercent, self.percent = self.get_sizes(im_pixmap)
        # Nastavení velikosti okna
        self.setFixedSize(int(self.wpercent * self.w), int(self.hpercent * self.h))
        print(f'New size: {int(self.wpercent * self.w)}x{int(self.hpercent * self.h)}')
        print('Show window')

        # Umístění tlačítka "Crop" do pravého dolního rohu s odsazením 5,5
        button_width = self.crop.sizeHint().width()  # Získání šířky tlačítka
        button_height = self.crop.sizeHint().height()  # Získání výšky tlačítka
        self.crop.move(self.width() - button_width - 5, self.height() - button_height - 5)

        self.show()


    def get_sizes(self, input_file):
        self.pixmap = QPixmap(input_file)
        self.w, self.h = self.pixmap.width(), self.pixmap.height()
        screen = QApplication.primaryScreen().geometry()  # Monitor size
        res = [int(screen.width() * 0.92), int(screen.height() * 0.92)]
        print(f'Original size: {self.w}x{self.h}')
        if self.w > res[0]:
            print('Shrink width')
            self.wpercent = res[0] / float(self.w)
            self.hpercent = self.wpercent
            self.percent = self.w / res[0]
            print(f'Percent: {self.percent}')
        if self.h > res[1]:
            print('Shrink height')
            self.hpercent = res[1] / float(self.h)
            self.wpercent = self.hpercent
            self.percent = self.w / res[1]
            print(f'Percent: {self.percent}')
        else:
            print('No need to shrink image')
            self.wpercent, self.hpercent = 1, 1
            self.percent = 0
        print(f'Res: {res}, HPercent: {100 * self.hpercent}, WPercent: {100 * self.wpercent}')
        return res, self.w, self.h, self.wpercent, self.hpercent, self.percent

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.drawPixmap(self.rect(), self.pixmap)
        pen = QPen(Qt.GlobalColor.black, 2, Qt.PenStyle.DashDotLine)
        qp.setPen(pen)
        pen.setStyle(Qt.PenStyle.DashLine)
        qp.setPen(pen)
        brush = QBrush(QColor(Qt.GlobalColor.white), Qt.BrushStyle.Dense6Pattern)
        qp.setBrush(brush)
        self.clip_rect = qp.drawRect(QRect(self.begin, self.end))
        centerCoord = (self.begin.x() + ((self.end.x() - self.begin.x()) / 2), (self.begin.y() + ((self.end.y() - self.begin.y()) / 2)))
        
        # Font
        qp.setPen(QPen(Qt.GlobalColor.white, 2))
        qp.drawEllipse(int(centerCoord[0]), int(centerCoord[1]), 2, 2)
        qp.setPen(QColor(Qt.GlobalColor.black))
        font = qp.font()
        font.setBold(True)
        qp.setFont(font)
        qp.setPen(QColor(Qt.GlobalColor.white))
        qp.drawText(80, 20, f'Image size: {self.w}x{self.h} px')
        qp.drawText(self.begin.x(), self.begin.y() - 5, f'Crop size: {abs(self.begin.x() - self.end.x())}x{abs(self.begin.y() - self.end.y())} px')

        qp.end()

    def mousePressEvent(self, event):
        if not self.defined_crop:
            if self.hpercent != 1:
                print('Image too big')
            self.begin = event.position().toPoint()
            self.end = event.position().toPoint()
            self.update()
        elif event.buttons() == Qt.MouseButton.LeftButton and self.defined_crop:
            self.defined_crop = False
            print('Right click')
            self.begin = event.position().toPoint()
            self.end = event.position().toPoint()    
            self.update()
        # else:
        #     print('Todo')
        #     self.defined_crop = False
        #     self.update()

    def mouseMoveEvent(self, event):
        self.end = event.position().toPoint()
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

    def crop_image(self):
        if self.hpercent != 1:
            self.crop_text = [self.begin.x(), self.begin.y(), self.end.x(), self.end.y()]
            print(self.crop_text)
            print('Image too big')
            self.crop_text = [self.ucalc(self.begin.x()), self.ucalc(self.begin.y()), self.ucalc(self.end.x()), self.ucalc(self.end.y())]
            print(self.crop_text)
        else:
            self.crop_text = [self.begin.x(), self.begin.y(), self.end.x(), self.end.y()]
        self.accept()
        return self.crop_text

    def ucalc(self, p_input):
        fixed_input = p_input * self.percent
        return fixed_input

    def get_value(self):
        return self.crop_text

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = LiveCropWindow("/Users/jandevera/Desktop/Screenshot 2020-06-08 at 00.23.06.png")
    ex.show()
    sys.exit(app.exec())