import sys
import glob
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

    tabs_files = {
            "browse modules": ModuleBrowser,
            "assembly status": AssemblyStatus,
            "assembly": Assembly,
            "start assembly": StartAssembly,
            # "guide": GuideAssembly,
            "setup FC7": SetupFC7,
            "new issue": NewIssue
            }

    def __init__(self):
        super().__init__()
        self.title = 'Dee building GUI'

        self.db_session = DBSession()

        modules_to_dtc_files = ["ModulesToDTCsPosOuter.csv", "ModulesToDTCsNegOuter.csv"]
        aggregation_files = ["AggregationPatternsPosOuter.csv", "AggregationPatternsNegOuter.csv"]
        detids_file = "DetId_modules_list.csv"
        self.geometry = Geometry.from_csv(modules_to_dtc_files, aggregation_files, detids_file)

        self.tabs = QTabWidget()
        for title, source in self.tabs_files.items():
            widget = source(self)
            setattr(self, title.lower().replace(" ","_"),widget)
            self.tabs.addTab(widget, title)
        self.setCentralWidget(self.tabs)

        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, 1600, 1080)


if __name__ == "__main__":
    app = QApplication([])
    window = DeeBuilder()
    window.show()
    sys.exit(app.exec())

