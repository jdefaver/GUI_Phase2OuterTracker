import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule

class AssemblyStatus(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        ui = loadUi('widgets_ui/assembly_status.ui', self) 

        self.geometry = parent.geometry
        self.db_session = parent.db_session

        self.select_dee.clicked.connect(self.show_dee_status)

    def show_dee_status(self):
        self.clear_display()
        side = self.dee_side.currentText()
        layer = self.dee_layer.currentText()
        surface = self.dee_surface.currentText()
        vertical = self.dee_vertical.currentText()
        detids = self.geometry.full_selector(side, int(layer), int(surface), vertical)
        detids_by_ring = {ring: detids[detids["module_ring"] == ring] for ring in np.sort(detids['module_ring'].unique())[::-1]}
        for ring, detids in detids_by_ring.items():
            r_layout = QHBoxLayout()
            for detid, data in detids.iterrows():
                r_layout.addStretch(1)
                text = f"{data['type']}\n{data['sensor_spacing_mm']}"
                r_layout.addWidget(ModuleButton(self, detid))
                r_layout.addStretch(1)
            self.dee_status_display.addLayout(r_layout)

    def clear_display(self):
        while self.dee_status_display.count() > 0:
            line = item = self.dee_status_display.takeAt(0)
            while line.count() > 0:
                item = line.takeAt(0)
                if not item:
                    continue

                w = item.widget()
                if w:
                    w.deleteLater()
            line.deleteLater()



class ModuleButton(QPushButton):
    """
    Display one module in the Dee Selector Window
    """

    def __init__(self, parent, detid):
        super().__init__(parent)

        self.geometry = parent.geometry
        self.db_session = parent.db_session

        self.module = self.db_session.query(ExternalModule).filter(ExternalModule.status.has(ModuleStatus.detid == detid)).first()
        self.geo_data = self.geometry.loc[detid]

        self.setAutoFillBackground(True)
        if self.module:
            self.setText(self.module.barcode)
        else:
            text = f"Absent\n{self.geo_data['type']}\n{self.geo_data['sensor_spacing_mm']}mm"
            self.setText(text)

        self.process_status()

    def process_status(self):
        if self.module:
            status = self.module.status
            p = self.palette()
            if status.test_status:
                if status.test_status == "ok":
                    p.setColor(self.backgroundRole(), Qt.green)
                else:
                    p.setColor(self.backgroundRole(), Qt.red)
            else:
                p.setColor(self.backgroundRole(), Qt.yellow)
            self.setPalette(p)
