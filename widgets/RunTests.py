from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from PipeReader import PipeReader
import subprocess
import os
import json

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from widgets.DeeBaseWidget import DeeBaseWidget

def make_fifo(fifo_path):
    try:
        os.remove(fifo_path)
    except:
        pass

    try:
        os.mkfifo(fifo_path)
    except:
        raise

class DynamicMplCanvas(FigureCanvas):
    """A canvas that updates itself every second with a new plot."""

    def __init__(self, parent, x, y):
        self.xs = x
        self.ys = y

        fig = Figure(figsize=(100, 100), dpi=100)
        self.axes = fig.add_subplot(111)

        self.compute_initial_figure()

        super().__init__(fig)
        self.setParent(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.updateGeometry()

    def compute_initial_figure(self):
        self.axes.plot(self.xs, self.ys, 'r')
        self.cleanup()

    def cleanup(self):
        self.xs = []
        self.ys = []

    def update_figure(self, new_x, new_y):
        self.xs.append(new_x)
        self.ys.append(new_y)
        self.axes.cla()
        self.axes.plot(self.xs, self.ys, 'r')
        self.draw()

class RunTests (DeeBaseWidget):
    def __init__(self, parent, modules, proceed_callback = None):
        super().__init__(parent)
        ui = loadUi('widgets_ui/run_tests.ui', self) 

        self.proceed_button.clicked.connect(proceed_callback)

        self.start_test_1.clicked.connect(self.run_test_1)
        self.start_test_2.clicked.connect(self.run_test_2)

        self.fifo_path = '/tmp/my_fifo'
        make_fifo(self.fifo_path)

        self.plot = DynamicMplCanvas(self, [0], [0])
        self.mpl_layout.addWidget(self.plot)

    def start_and_attach_pipes(self, executable):
        path = os.path.realpath(executable)
        process =  subprocess.Popen([path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, encoding='UTF-8')

        self.stdout_reader = PipeReader(process.stdout, self.append_to_output)
        self.stderr_reader = PipeReader(process.stderr, self.append_to_errors)

        # fifo needs to be open after process starts as it blocks until it gets data
        self.pipe = open(self.fifo_path)
        self.pipe_reader = PipeReader(self.pipe, self.on_pipe_message)
        self.pipe_reader.finished.connect(self.on_complete)

    def run_test_1(self):
        self.plot.cleanup()
        self.start_and_attach_pipes('test1.py')
        self.start_test_1.setEnabled(False)
        self.start_test_2.setEnabled(False)

    def run_test_2(self):
        self.plot.cleanup()
        self.start_and_attach_pipes('test2.py')
        self.start_test_1.setEnabled(False)
        self.start_test_2.setEnabled(False)

    def append_to_output(self, message):
        self.output_logs.append(message)

    def append_to_errors(self, message):
        self.error_logs.append(message)

    def on_pipe_message(self, message):
        try:
            data = json.loads(message)
            if data['type'] == "message":
                self.append_to_output(f"Got from pipe : {data['data']}")
            elif data['type'] == "data":
                self.plot.update_figure(data["data"][0], data["data"][1])
        except:
            print(message)
            raise

    def on_complete(self):
        self.pipe.close()
        self.start_test_1.setEnabled(True)
        self.start_test_2.setEnabled(True)