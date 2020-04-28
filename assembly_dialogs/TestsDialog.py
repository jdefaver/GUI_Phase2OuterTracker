from functools import partial
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *
from sqlalchemy.sql import func

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule
from widgets import GuideAssembly, PickModule, RunTests
from assembly_dialogs import AbstractAssemblyDialog

class TestsDialog (AbstractAssemblyDialog):
    def __init__(self, parent, detid):
        super().__init__(parent, detid)

        self.bundle = self.geometry.loc[detid]["mfb"]
        self.detids = self.geometry[self.geometry["mfb"] == self.bundle]
        self.modules = self.db_session.query(ExternalModule).filter(ExternalModule.status.has(ModuleStatus.detid.in_(self.detids))).all()

        self.add_instructions_before()
        self.add_instructions_after()
        self.layout.setCurrentIndex(0)

        if not all(m.opt_status is not None for m in self.modules) or len(self.detids) != len(self.modules):
            QMessageBox.warning(self, "Warning", "Not all modules in this bundle are connected to optics, tests cannot be done")
            #FIXME : close does not work here !
            self.close()

        self.add_instructions_before()
        self.add_tests()
        self.add_instructions_after()
        self.layout.setCurrentIndex(0)

    def add_tests(self):
        self.tests = RunTests.RunTests(self, modules = self.modules, proceed_callback = self.go_to_cleanup)
        self.layout.insertWidget(1, self.tests)

    def add_instructions_before(self):
        guide = [
            {"text": f"Connect all optics for bundle {self.bundle}", "image": 'assembly_images/test_1.png'},
        ]
        title = f"Preparing to test modules in bundle {self.bundle}"
        self.guide_before = GuideAssembly.GuideAssembly(self, "", guide, proceed_callback = self.go_to_tests, title = title)
        self.layout.insertWidget(0, self.guide_before)

    def add_instructions_after(self):
        guide = [
            {"text": f"Disconnect all optics for bundle {self.bundle}", "image": 'assembly_images/test_2.png'},
        ]
        title = f"Cleaning after tests of modules in bundle {self.bundle}"
        self.guide_before = GuideAssembly.GuideAssembly(self, "", guide, proceed_callback = self.finish, title = title)
        self.layout.insertWidget(2, self.guide_before)

    def go_to_tests(self):
        self.layout.setCurrentIndex(1)

    def go_to_cleanup(self):
        self.layout.setCurrentIndex(2)

    def finish(self):
        # FIXME : this will need to reflect the true test status
        for module in self.modules:
            module.status.tested = func.now()
            module.status.test_status = "ok"
        self.db_session.commit()
        self.close()