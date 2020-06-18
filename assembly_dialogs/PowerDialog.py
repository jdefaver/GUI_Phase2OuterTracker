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
        self.pwr_services_channel = self.geo_data["pwr_services_channel"]
        self.layout.addWidget(self.pick)

    def go_to_guide(self, barcode):
        self.guide = GuideAssembly.GuideAssembly(self, barcode, "assembly_guides/connect_power.yml", proceed_callback = self.proceed)
        self.layout.addWidget(self.guide)
        self.layout.setCurrentIndex(1)

    def proceed(self):
        self.module.status.pwr_status = func.now()
        self.db_session.commit()
        self.close()