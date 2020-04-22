from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

class StartAssembly(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        ui = loadUi('widgets_ui/start_assembly.ui', self)
        self.step = "screw"
        self.detid = None 
        self.db_session = parent.db_session
        self.geometry = parent.geometry
        self.parent = parent