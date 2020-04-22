from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

class GuideAssembly(QWidget):
    def __init__(self, parent, guide = ()):
        super().__init__(parent)
        ui = loadUi('widgets_ui/guide_assembly.ui', self)
        self.guide = guide

        self.next_button.clicked.connect(self.next_step)
        self.previous_button.clicked.connect(self.previous_step)
        self.previous_button.setEnabled(False)

        for step in guide:
            tw = QTextBrowser(self)
            if "text" in step:
                tw.setText(step["text"])

            iw = QLabel(self)
            if "image" in step:
                iw.setPixmap(QPixmap(step["image"]))

            self.text_layout.addWidget(tw)
            self.image_layout.addWidget(iw)

        self.text_layout.setCurrentIndex(0)
        self.image_layout.setCurrentIndex(0)

    def next_step(self):
        current = self.text_layout.currentIndex()
        if current < self.text_layout.count():
            self.text_layout.setCurrentIndex(current + 1)
            self.image_layout.setCurrentIndex(current + 1)
        if current + 2 == self.text_layout.count():
            self.next_button.setEnabled(False)
        if current == 0:
            self.previous_button.setEnabled(True)


    def previous_step(self):
        current = self.text_layout.currentIndex()
        if current > 0:
            self.text_layout.setCurrentIndex(current - 1)
            self.image_layout.setCurrentIndex(current - 1)
        if current - 1 == 0:
            self.previous_button.setEnabled(False)
        if current + 1 == self.text_layout.count():
            self.next_button.setEnabled(True)