from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule
from Module import Module
from geometry import MGeometry

class DeeBaseWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.geometry = parent.geometry
        self.db_session = parent.db_session

    def modules_from_detids(self, detids):
        return self.db_session.query(ExternalModule).filter(ExternalModule.status.has(ModuleStatus.detid.in_(detids))).all()
    
    def module_from_detid(self, detid):
        return self.db_session.query(ExternalModule).filter(ExternalModule.status.has(ModuleStatus.detid == detid)).first()