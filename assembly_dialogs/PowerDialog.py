from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from sqlalchemy.sql import func

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule
from widgets import GuideAssembly, PickModule
from assembly_dialogs import AbstractAssemblyDialog

class PowerDialog(AbstractAssemblyDialog):
    def __init__(self, parent, **assembly_data):
        super().__init__(parent, **assembly_data)

        self.pick = PickModule.PickModule(self, [self.module], self.go_to_guide)
        self.layout.addWidget(self.pick)

    def go_to_guide(self, barcode):
        guide = [
            {"text": f"connect power in channel {self.geo_data['pwr_services_channel']}", "image": 'assembly_images/test_1.png'},
            {"text": "test 1", "image": None},
            {"text": "test 2", "image": 'assembly_images/test_2.png'},
            {"text": "test 3", "image": 'assembly_images/test_3.png'}
        ]
        title = f"Connecting module with barcode {self.module.barcode} to power at {self.geo_data['pwr_services_channel']}"
        self.guide = GuideAssembly.GuideAssembly(self, barcode, guide, proceed_callback = self.proceed, title = title)
        self.layout.addWidget(self.guide)
        self.layout.setCurrentIndex(1)

    def proceed(self):
        self.module.status.pwr_status = func.now()
        self.db_session.commit()
        self.close()