from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule

class AbstractAssemblyDialog(QDialog):
    def __init__(self, parent, **assembly_data):
        super().__init__(parent)
        self.parent = parent
        self.db_session = parent.db_session
        self.geometry = parent.geometry
        self.operator = parent.operator
        self.assembly_data = assembly_data

        self.layout = QStackedLayout()
        self.setLayout(self.layout)
        self.setGeometry(0, 0, 1600, 1080)
        
        if "detid" in assembly_data:
            detid = assembly_data["detid"]
            self.detid = detid
            self.geo_data = self.geometry.loc[detid]
            self.module = self.db_session.query(ExternalModule).filter(ExternalModule.status.has(ModuleStatus.detid == self.detid)).first()
        elif "detids" in assembly_data:
            detids = assembly_data["detids"]
            self.detids = detids
            self.geo_data = self.geometry.loc[detids]
            self.modules = self.db_session.query(ExternalModule).filter(ExternalModule.status.has(ModuleStatus.detid.in_(self.detids))).all()