from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from sqlalchemy.sql import func

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule

from widgets import GuideAssembly, PickModule

class ScrewDialog (QDialog):
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
        self.good_modules = self.db_session.query(ExternalModule).filter(ExternalModule.status == None)
        self.good_modules = self.good_modules.filter(ExternalModule.module_type == self.geo_data["type"])
        self.good_modules = self.good_modules.filter(ExternalModule.module_thickness == self.geo_data["sensor_spacing_mm"])
        self.good_modules = self.good_modules.all()

        # first tab : offer a list of modules and ask to scan one of them
        self.pick = PickModule.PickModule(self, self.good_modules, self.go_to_guide)
        self.layout.addWidget(self.pick)

    def go_to_guide(self, barcode):
        guide = [
            {"text": barcode, "image": None},
            {"text": "test",  "image": 'assembly_images/test_1.png'},
            {"text": "troll", "image": 'assembly_images/test_2.png'},
            {"text": "broll", "image": 'assembly_images/test_3.png'}
        ]
        title = f"Installing module with barcode {barcode} at detid {self.detid}"
        self.guide = GuideAssembly.GuideAssembly(self, guide, proceed_callback = partial(self.proceed, barcode), title = title)
        self.layout.addWidget(self.guide)
        self.layout.setCurrentIndex(1)

    def proceed(self, barcode):
        self.save_new_installation(barcode)
        self.close()

    def save_new_installation(self, barcode):
        status = {"barcode": barcode, "detid": self.detid, "screwed":func.now()}
        self.db_session.add(ModuleStatus(**status))
        self.db_session.commit()