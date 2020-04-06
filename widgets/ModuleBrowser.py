import re, string
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

class ModuleBrowser(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        ui = loadUi('widgets_ui/browse_modules.ui', self) 
        self.ScanMOD.clicked.connect(self.start_scan)
        self.Enter_MODID.setEnabled(False)
        self.scanning = False
        self.barcode_chars = []

    def start_scan(self):
        self.scanning = True
        self.Enter_MODID.setText("Scannning...")

    def keyPressEvent(self, event):
        if self.scanning:
            if event.key() == Qt.Key_Return:
                barcode = "".join([QKeySequence(i).toString() for i in self.barcode_chars])
                self.Enter_MODID.setText(re.sub('[\W_]+', '', barcode))
                self.barcode_chars = []
                self.scanning = False
            else:
                self.barcode_chars.append(event.key())
            event.accept()

