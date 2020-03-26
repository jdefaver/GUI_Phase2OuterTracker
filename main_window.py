import sys
import logging
import glob
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

from widgets import *

logging.basicConfig(level=logging.WARNING)

class DeeBuilder(QMainWindow):

    tabs_files = {
            "browse modules": ModuleBrowser,
            "assembly": Assembly,
            "start assembly": StartAssembly,
            "guide": GuideAssembly,
            "setup FC7": SetupFC7,
            "new issue": NewIssue
            }

    def __init__(self):
        super().__init__()
        self.title = 'Dee building GUI'

        tabs = QTabWidget()
        for title, source in self.tabs_files.items():
            widget = source(self)
            tabs.addTab(widget, title)
        self.setCentralWidget(tabs)

        self.setWindowTitle(self.title)
        self.setGeometry(0, 0, 1600, 1080)


if __name__ == "__main__":
    app = QApplication([])
    window = DeeBuilder()
    window.show()
    sys.exit(app.exec())

