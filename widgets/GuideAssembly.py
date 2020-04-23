from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from sqlalchemy.sql import func

from local_database_definitions import LogEvent
import logging

class GuideAssembly(QWidget):
    def __init__(self, parent, barcode, guide = (), proceed_callback = None, title = None):
        super().__init__(parent)
        ui = loadUi('widgets_ui/guide_assembly.ui', self)
        self.guide = guide
        self.db_session = parent.db_session
        self.barcode = barcode

        self.next_button.clicked.connect(self.next_step)
        self.previous_button.clicked.connect(self.previous_step)
        self.previous_button.setEnabled(False)
        self.add_elog_entry.clicked.connect(self.save_elog)

        if title is not None:
            self.assembly_title.setText(title)

        try: 
            self.proceed_button.clicked.connect(proceed_callback)
        except TypeError:
            logging.warning("No callback given for next step in assembly")

        for step in guide:
            tw = QTextBrowser(self)
            if "text" in step:
                tw.setText(step["text"])

            iw = QLabel(self)
            if "image" in step:
                iw.setPixmap(QPixmap(step["image"]))

            self.text_widget.addWidget(tw)
            self.image_widget.addWidget(iw)

        self.text_widget.setCurrentIndex(1)
        self.image_widget.setCurrentIndex(1)

    def next_step(self):
        current = self.text_widget.currentIndex()
        if current + 1 < self.text_widget.count():
            self.text_widget.setCurrentIndex(current + 1)
            self.image_widget.setCurrentIndex(current + 1)
        if current + 2 == self.text_widget.count():
            self.next_button.setEnabled(False)
        if current == 1:
            self.previous_button.setEnabled(True)


    def previous_step(self):
        current = self.text_widget.currentIndex()
        if current > 1:
            self.text_widget.setCurrentIndex(current - 1)
            self.image_widget.setCurrentIndex(current - 1)
        if current - 2 == 0:
            self.previous_button.setEnabled(False)
        if current + 1 == self.text_widget.count():
            self.next_button.setEnabled(True)

    def save_elog(self):
        if self.elog_text.toPlainText().strip():
            log_event = LogEvent(barcode = self.barcode, text = self.elog_text.toPlainText(), time =  func.now())
            self.db_session.add(log_event)
            self.db_session.commit()
            self.elog_text.setPlainText("")
            QMessageBox.information(self, "OK", "Your elog entry was saved")
        else:
            QMessageBox.warning(self, "Failure", "Cannot save an empty elog entry")



