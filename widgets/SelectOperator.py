from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
import re

class SelectOperator (QDialog):
    """
    select an operator using their unique ID
    """
    def __init__(self, parent, check_function, can_cancel = False):
        super().__init__(parent)

        self.label = QLabel("Please scan your personal barcode\nor enter it on the keyboard.")
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        if can_cancel:
            cancel = QPushButton("Cancel", self)
            layout.addWidget(cancel)
            cancel.clicked.connect(self.reject)

        self.id_chars = []
        self.check_function = check_function
        self.id = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            id = "".join([QKeySequence(i).toString() for i in self.id_chars])
            id = re.sub('[\W_]+', '', id)
            operator = self.check_function(id)
            if operator:
                self.id = operator
                self.accept()
            else:
                self.label.setText(f"Unknown ID : {id}, please try again.")
                self.id_chars = []
        else:
            self.id_chars.append(event.key())
        event.accept()