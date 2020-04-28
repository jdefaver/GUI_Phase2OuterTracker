from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

class PipeReader(QThread):
    message = pyqtSignal(str)

    def __init__(self, pipe, handler):
        super().__init__()
        self.pipe = pipe
        self.message.connect(handler)
        self.start()

    def run(self):
        while True:
            line = self.pipe.readline()
            if len(line) == 0:
                break
            self.message.emit(line[:-1])

