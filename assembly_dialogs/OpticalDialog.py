from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from sqlalchemy.sql import func

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule
from widgets import GuideAssembly, PickModule
from assembly_dialogs import AbstractAssemblyDialog

from copy import deepcopy
from functools import partial

class OpticalDialog (AbstractAssemblyDialog):
    def __init__(self, parent, **assembly_data):
        super().__init__(parent, **assembly_data)

        self.initial_modules = self.modules[:]

        pick = PickModule.PickModule(self, self.modules, self.go_to_guide)
        self.layout.addWidget(pick)
        self.mfb = self.geo_data.iloc[0]["mfb"]
        self.opt_channel = self.geo_data.iloc[0]["opt_services_channel"]

    def go_to_guide(self, barcode):
        """
        create guide window and switch there
        """
        module = self.db_session.query(ExternalModule).filter(ExternalModule.barcode == barcode).first()
        self.barcode = barcode
        guide = GuideAssembly.GuideAssembly(self, barcode, "assembly_guides/connect_optics.yml", proceed_callback = partial(self.proceed_next, module))

        self.modules = [m for m in self.modules if m.barcode != barcode]
        if not self.modules:
            guide.proceed_button.setText("Save and finish")
        self.layout.addWidget(guide)
        self.go_to_widget(guide)

    def go_to_widget(self, widget):
        index = self.layout.indexOf(widget)
        self.layout.setCurrentIndex(index)

    def proceed_next(self, module):
        self.save_current(module)
        if self.modules:
            pick = PickModule.PickModule(self, self.modules, self.go_to_guide)
            self.layout.addWidget(pick)
            self.go_to_widget(pick)
        else:
            self.close()

    def save_current(self, module):
        module.status.opt_status = func.now()
        self.db_session.commit()