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

    def modules_from_bundle(self, bundle, geometry = None):
        if geometry is None:
            geometry = self.geometry
        detids = geometry[geometry["mfb"] == bundle].index.tolist()
        return self.modules_from_detids(detids)

    def modules_in_my_bundle(self, detid, geometry = None):
        if geometry is None:
            geometry = self.geometry
        bundle = geometry.loc[detid]["mfb"]
        return self.modules_from_bundle(bundle, geometry)

    def detids_in_my_bundle(self, detid, geometry = None):
        if geometry is None:
            geometry = self.geometry
        bundle = geometry.loc[detid]["mfb"]
        return geometry[geometry["mfb"] == bundle].index.tolist()
