from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

class AbstractAssemblyDialog(QDialog):
    def __init__(self, parent, detid):
        super().__init__(parent)
        self.detid = detid
        self.parent = parent
        self.db_session = parent.db_session
        self.geometry = parent.geometry

        self.layout = QStackedLayout()
        self.setLayout(self.layout)
        self.setGeometry(0, 0, 1600, 1080)
        
        self.geo_data = self.geometry.loc[detid]