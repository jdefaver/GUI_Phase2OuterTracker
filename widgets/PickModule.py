from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

import re
import logging

class PickModule(QWidget):
    def __init__(self, parent, modules, success_callback):
        """
        Widget asking to scan a module from agiven list
          parent should be a QWidget
          modules is a list of ExternalModules
          success_callback will be called with the scanned barcode as an argument
        """
        super().__init__(parent)
        self.parent = parent
        self.success_callback = success_callback
        ui = loadUi('widgets_ui/pick_module.ui', self)
        self.modules = modules
        if len(self.modules) == 1:
            self.label.setText("Please scan module. It should match the barcode below.")
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
            self.success_callback(barcode)
        else:
            self.barcode_chars = []
            if len(self.modules) == 1:
                error = WrongBarcode(self, barcode, self.modules[0].barcode)
            else:
                error = WrongBarcode(self, barcode)
            error.exec()

class WrongBarcode(QDialog):
    def __init__(self, parent, barcode, expected = None):
        super().__init__(parent)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        msg_text =  f"Wrong barcode\n\nYou scanned {barcode}"
        if expected is not None:
            msg_text += f"\nbut we expected {expected}"
        message = QLabel(msg_text)
        message.setAlignment(Qt.AlignCenter | Qt.AlignVCenter)
        retry = QPushButton("Try again", self)
        self.layout.addWidget(message)
        self.layout.addWidget(retry)
        retry.clicked.connect(self.close)
        QTimer.singleShot(10000, self.close)
