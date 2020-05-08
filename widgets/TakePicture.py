from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from PyQt5.QtMultimedia import QSound
import cv2
from functools import partial


class TakePicture (QDialog):

    def __init__(self, parent, *, max_captures = 5, save_callback = None):
        super().__init__(parent)

        self.save_callback = save_callback

        # basic layout
        self.img = QLabel()
        self.captured = QLabel()
        self.capture = QPushButton("Take pictures")
        self.quit = QPushButton("Cancel")
        layout = QVBoxLayout(self)
        layout.addWidget(self.img)
        layout.addWidget(QLabel("Select a picture below or capture again."))
        self.thumbs_layout = QHBoxLayout()
        layout.addLayout(self.thumbs_layout)
        layout.addWidget(self.capture)
        layout.addWidget(self.quit)

        # active parts
        self.max_captures = max_captures
        self.shutter = QSound("camera-shutter.wav")
        self.saved = []
        self.cap = cv2.VideoCapture(0)
        _, frame = self.cap.read()
        if frame is None:
            raise Exception("Camera absent or busy")
        self.timer = QTimer()
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.draw_camera)
        self.timer.start()
        self.quit.clicked.connect(self.close)
        self.capture.clicked.connect(self.capture_images)

        self.capture_timer = QTimer()
        self.capture_timer.setInterval(1000)
        self.capture_timer.timeout.connect(self.save_one)

    def capture_images(self):
        """
        start capturing pictures
        """
        self.saved = []
        self.clean_thumbnails()
        self.capture_timer.start()

    def save_one(self):
        """"
        add one picture to the queue of candidates
        """
        self.shutter.play()
        ret, frame = self.cap.read()
        self.saved.append(frame_to_qpix(frame))
        self.add_to_thumbnails(frame)
        if len(self.saved) == self.max_captures:
            self.capture_timer.stop()

    def clean_thumbnails(self):
        """
        cleanup the capture list
        """
        while self.thumbs_layout.count() > 0:
            item = self.thumbs_layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.thumbs_layout.addStretch()

    def add_to_thumbnails(self, frame):
        """
        add one thumbnail to the preview list
        """
        thumb = frame_to_qpix(frame, 0.95/self.max_captures)
        qpix = frame_to_qpix(frame)
        container = QLabel()
        container.mousePressEvent = partial(self.save_picture, picture = qpix)
        container.setCursor(Qt.PointingHandCursor)
        container.setPixmap(thumb)
        self.thumbs_layout.addWidget(container)
        self.thumbs_layout.addStretch()

    def draw_camera(self):
        """
        show the current camera feed
        """
        ret, frame = self.cap.read()
        self.img.setPixmap(frame_to_qpix(frame))

    def save_picture(self, event, picture):
        if self.save_callback is not None:
            self.save_callback(picture)
        else:
            filename = "test.png"
            print("No picture saing method provided, saving as {filename}")
            picture.save(filename,"PNG")
        self.close()


def frame_to_qpix(frame, scaling = None):
    """
    Turn an opencv frame into a pyqt QPixmap for direct use
    """
    height, width, channel = frame.shape
    if scaling is not None:
        height = int(scaling*height)
        width = int(scaling*width)
        frame = cv2.resize(frame, (width, height))
    qImg = QImage(frame.data, width, height, width*3, QImage.Format_RGB888).rgbSwapped()
    return QPixmap(qImg)
