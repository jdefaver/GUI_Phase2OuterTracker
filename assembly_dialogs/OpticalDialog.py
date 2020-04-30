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

        self.remaining_modules = deepcopy(self.modules)

        pick = PickModule.PickModule(self, self.remaining_modules, self.go_to_guide)
        self.layout.addWidget(pick)
        self.mfb = self.geo_data.iloc[0]["mfb"]
        self.opt_channel = self.geo_data.iloc[0]["opt_services_channel"]

    def go_to_guide(self, barcode):
        module = self.db_session.query(ExternalModule).filter(ExternalModule.barcode == barcode).first()
        self.remaining_modules = [m for m in self.remaining_modules if m.barcode != barcode]
        guide = [
            {"text": f"connect optics using mfb {self.mfb} in channel {self.opt_channel}", "image": 'assembly_images/test_1.png'},
            {"text": "test 1", "image": None},
            {"text": "test 2", "image": 'assembly_images/test_2.png'},
            {"text": "test 3", "image": 'assembly_images/test_3.png'}
        ]
        title = f"Connecting module with barcode {barcode} to optics at {self.opt_channel}"
        guide = GuideAssembly.GuideAssembly(self, barcode, guide, proceed_callback = partial(self.proceed_next, module), title = title)
        if not self.remaining_modules:
            guide.proceed_button.setText("Save and finish")
        self.layout.addWidget(guide)
        self.go_to_widget(guide)

    def go_to_widget(self, widget):
        index = self.layout.indexOf(widget)
        self.layout.setCurrentIndex(index)

    def proceed_next(self, module):
        self.save_current(module)
        if self.remaining_modules:
            pick = PickModule.PickModule(self, self.remaining_modules, self.go_to_guide)
            self.layout.addWidget(pick)
            self.go_to_widget(pick)
        else:
            self.close()

    def save_current(self, module):
        module.status.opt_status = func.now()
        self.db_session.commit()
        self.close()