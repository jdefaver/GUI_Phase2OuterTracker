from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from sqlalchemy.sql import func
from markdown import markdown
import yaml
import os

from local_database_definitions import LogEvent
from widgets.TakePicture import TakePicture
import logging

class GuideAssembly(QWidget):
    def __init__(self, parent, barcode, yaml_file, proceed_callback = None):
        """
        create an assembly guide widget
        arguments:
           barcode  = id of the current module being worked on. Needed for DB operations
           yaml_file = path to the yaml file with building instructions and the window title. See load_from_yaml for details.
           proceed_callback = function to be called when the proceed button is clicked
        """
        super().__init__(parent)
        ui = loadUi('widgets_ui/guide_assembly.ui', self)
        self.db_session = parent.db_session
        self.parent = parent
        self.barcode = barcode
        self.title, self.guide = self.load_from_yaml(yaml_file)

        if len(self.guide) > 1:
            self.next_button.clicked.connect(self.next_step)
            self.previous_button.clicked.connect(self.previous_step)
            self.previous_button.setEnabled(False)
        else:
            self.next_button.setEnabled(False)
            self.previous_button.setEnabled(False)
        
        self.add_elog_entry.clicked.connect(self.save_elog)
        self.add_picture.clicked.connect(self.picture_dialog)
        self.cancel.clicked.connect(parent.close)

        if self.title:
            self.assembly_title.setText(self.title)

        try: 
            self.proceed_button.clicked.connect(proceed_callback)
        except TypeError:
            logging.warning("No callback given for next step in assembly")

        self.show_elog_history()

        for step in self.guide:
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
            log_event = LogEvent(barcode = self.barcode, text = self.elog_text.toPlainText().strip(), time =  func.now())
            self.db_session.add(log_event)
            self.db_session.commit()
            self.elog_text.setPlainText("")
            QMessageBox.information(self, "OK", "Your elog entry was saved")
        else:
            QMessageBox.warning(self, "Failure", "Cannot save an empty elog entry")
        
        self.show_elog_history()

    def show_elog_history(self):
        events = self.db_session.query(LogEvent).filter(LogEvent.barcode == self.barcode).order_by(LogEvent.time).all()
        text = "### Previous log entries\n\n"
        text += "\n".join(f" * {e.time}: {e.text}" for e in events)
        self.previous_elogs.setHtml(markdown(text))

    def picture_dialog(self):
        pic_dialog = TakePicture(self, save_callback = self.register_picture)
        pic_dialog.exec()

    def register_picture(self, qpix):
        filename = f"test_{self.barcode}.png"
        print(f"picture saved as {filename}")
        qpix.save(filename,"PNG")

    def load_from_yaml(self, yaml_file):
        """
        get assembly guide and title from yaml. format:
          title : "window title"
          image_path : "/absolute/path/of/image/folder"
          steps:
            - text: "step 1 instructions text"
              image: "image file name"
            - text: "etc."
            - image: "another file name"
        all texts are templates that can use variables defined in this object's parent window (for instance OpticalDialog)
        """
        guide = []
        with open(yaml_file, 'r') as yfile:
            data = yaml.load(yfile, Loader=yaml.FullLoader)
            path = data.get('image_path', '')
            title = data.get('title', '').format(**vars(self.parent), barcode=self.barcode)
            for step in data["steps"]:
                if 'image' in step:
                    step['image'] = os.path.join(path, step['image'])
                if 'text' in step:
                    step['text'] = step['text'].format(**vars(self.parent), barcode=self.barcode)
                guide.append(step)
        return title, guide

