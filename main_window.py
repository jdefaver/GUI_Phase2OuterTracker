import sys
import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

from widgets import *
from geometry import Geometry
from local_database_definitions import LogEvent, ModuleStatus, ExternalModule, DBSession


import logging
logging.basicConfig(level=logging.WARNING)

class DeeBuilder(QMainWindow):

    ids = {
        "1111": "Jerome de Favereau",
        "2222": "Maksym Teklishyn" 
    }

    tabs_files = {
            "browse modules": ModuleBrowser,
            "assembly status": AssemblyStatus,
            # "assembly": Assembly,
            # "start assembly": StartAssembly,
            # "guide": GuideAssembly,
            # "setup FC7": SetupFC7,
            # "new issue": NewIssue
            # "take picture": TakePicture
            }

    def __init__(self):
        super().__init__()
        self.title = 'Dee building GUI'

        self.db_session = DBSession()

        modules_to_dtc_files = ["ModulesToDTCsPosOuter.csv", "ModulesToDTCsNegOuter.csv"]
        aggregation_files = ["AggregationPatternsPosOuter.csv", "AggregationPatternsNegOuter.csv"]
        detids_file = "DetId_modules_list.csv"
        self.geometry = Geometry.from_csv(modules_to_dtc_files, aggregation_files, detids_file)
        self.operator = None

        self.tabs = QTabWidget()
        for title, source in self.tabs_files.items():
            widget = source(self)
            setattr(self, title.lower().replace(" ","_"),widget)
            self.tabs.addTab(widget, title)
        self.setCentralWidget(self.tabs)

        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, 1600, 1080)

        self.status = QLabel("")
        self.statusBar = QStatusBar()
        self.statusBar.addWidget(self.status)
        self.setStatusBar(self.statusBar)

        operator_select = SelectOperator(self, self.check_id)
        while self.operator is None:
            if operator_select.exec():
                self.set_operator(operator_select.id)

        quit_gui = QAction('&Exit', self)
        quit_gui.triggered.connect(self.close)
        change_operator = QAction('&Change operator', self)
        change_operator.triggered.connect(self.switch_operator)
        menubar = self.menuBar()
        file_menu = menubar.addMenu('&File')
        file_menu.addAction(quit_gui)
        file_menu.addAction(change_operator)

    def switch_operator(self):
        operator_select = SelectOperator(self, self.check_id, can_cancel = True)
        if operator_select.exec():
            self.set_operator(operator_select.id)

    def set_operator(self, id):
        self.operator = id
        self.status.setText(f"Operator: {self.ids.get(self.operator, 'Undefined')}")


    def check_id(self, id):
        if id in self.ids:
            return id
        else:
            return None


if __name__ == "__main__":
    app = QApplication([])
    window = DeeBuilder()
    window.show()
    sys.exit(app.exec())

