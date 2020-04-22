from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

import re
import logging

class PickModule(QWidget):
    def __init__(self, parent, modules):
        super().__init__(parent)
        self.parent = parent
        ui = loadUi('widgets_ui/pick_module.ui', self)
        self.modules = modules
        text = "\n".join(sorted(m.barcode for m in modules))
        self.modules_list.setText(text)

        self.cancel_button.clicked.connect(parent.close)

        self.barcode_chars = []

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            barcode = "".join([QKeySequence(i).toString() for i in self.barcode_chars])
            barcode = re.sub('[\W_]+', '', barcode)
            self.check_barcode(barcode)
        else:
            self.barcode_chars.append(event.key())
        event.accept()

    def check_barcode(self, barcode):
        if barcode in (m.barcode for m in self.modules):
            self.parent.set_barcode(barcode)
        else:
            self.barcode_chars = []
            # FIXME : pop a dialog for this
