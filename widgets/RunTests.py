from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

class RunTests(QWidget):
    def __init__(self, parent, proceed_callback = None):
        super().__init__(parent)
        ui = loadUi('widgets_ui/run_tests.ui', self) 

        self.proceed_button.clicked.connect(proceed_callback)