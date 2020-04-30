from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from sqlalchemy.sql import func

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule

from widgets import GuideAssembly, PickModule
from assembly_dialogs import AbstractAssemblyDialog, PowerDialog

class ScrewDialog (AbstractAssemblyDialog):
    def __init__(self, parent, **assembly_data):
        super().__init__(parent, **assembly_data)

        self.good_modules = self.db_session.query(ExternalModule).filter(ExternalModule.status == None).filter(ExternalModule.location == 'Louvain')
        self.good_modules = self.good_modules.filter(ExternalModule.module_type == self.geo_data["type"])
        self.good_modules = self.good_modules.filter(ExternalModule.module_thickness == self.geo_data["sensor_spacing_mm"])
        self.good_modules = self.good_modules.all()

        self.pick = PickModule.PickModule(self, self.good_modules, self.go_to_guide)
        self.layout.addWidget(self.pick)

    def go_to_guide(self, barcode):
        guide = [
            {"text": barcode, "image": None},
            {"text": "do task 1",  "image": 'assembly_images/test_1.png'},
            {"text": "do task 2", "image": 'assembly_images/test_2.png'},
            {"text": "do task 3", "image": 'assembly_images/test_3.png'}
        ]
        title = f"Installing module with barcode {barcode} at detid {self.detid}"
        self.guide = GuideAssembly.GuideAssembly(self, barcode, guide, proceed_callback = partial(self.proceed, barcode), title = title)
        self.layout.addWidget(self.guide)
        self.layout.setCurrentIndex(1)

    def proceed(self, barcode):
        self.save_new_installation(barcode)
        dialog = PowerDialog.PowerDialog(self.parent, detid = self.detid)
        dialog.exec()
        self.close()

    def save_new_installation(self, barcode):
        status = {"barcode": barcode, "detid": self.detid, "screwed":func.now()}
        self.db_session.add(ModuleStatus(**status))
        self.db_session.commit()