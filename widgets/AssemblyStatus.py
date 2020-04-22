import logging
from collections import defaultdict
from operator import attrgetter
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule
from Module import Module

from assembly_dialogs import *

class AssemblyStatus(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        ui = loadUi('widgets_ui/assembly_status.ui', self) 

        self.parent = parent
        self.geometry = parent.geometry
        self.db_session = parent.db_session

        self.select_dee.clicked.connect(self.show_dee_status)

        self.detids = None

        self.next_layout = QGridLayout()
        self.next_layout.setColumnStretch(0,5)
        self.next_layout.setColumnStretch(1,1)
        next_widget = QWidget(self)
        next_widget.setLayout(self.next_layout)
        self.next_steps_area.setWidget(next_widget)

        self.next_steps_table_rows = 0

    def show_dee_status(self):
        """
        show modules and status
        """
        self.clear_display()
        side = self.dee_side.currentText()
        layer = self.dee_layer.currentText()
        surface = self.dee_surface.currentText()
        vertical = self.dee_vertical.currentText()
        self.detids = self.geometry.full_selector(side, int(layer), int(surface), vertical)
        detids_by_ring = {ring: self.detids[self.detids["module_ring"] == ring] for ring in np.sort(self.detids['module_ring'].unique())[::-1]}
        for ring, detids in detids_by_ring.items():
            r_layout = QHBoxLayout()
            for detid, data in detids.iterrows():
                r_layout.addStretch(1)
                text = f"{data['type']}\n{data['sensor_spacing_mm']}"
                r_layout.addWidget(ModuleButton(self, detid))
                r_layout.addStretch(1)
            self.dee_status_display.addLayout(r_layout)

        self.compute_next_steps()

    def compute_next_steps(self):
        detids_ids = tuple(self.detids.index.tolist())
        self.modules = self.db_session.query(ExternalModule).filter(ExternalModule.status.has(ModuleStatus.detid.in_(detids_ids))).all()
        self.modules = {Module(module, self.detids.loc[module.status.detid]) for module in self.modules}
        
        complete, incomplete, empty = self.process_bundles()
        next_detid, next_bundle = self.next_bundle(empty)
        to_replace = self.to_replace()
        to_continue = self.to_continue()

        if incomplete:
            self.add_row(QLabel("Incomplete bundles"))
            for bundle, detids in incomplete.items():
                for detid in detids:
                    self.add_row(QLabel(str(detid)), AssemblyButton("Install", self, detid, "screw"))

        if next_detid:
            self.add_row(QLabel("Next bundle to start"))
            self.add_row(QLabel(str(next_detid)), AssemblyButton("Start new", self, next_detid, "screw"))

        if to_replace:
            self.add_row(QLabel("Modules to replace"))
            for mod in to_replace:
                self.add_row(QLabel(str(mod.detid)), AssemblyButton("Replace", self, mod.detid, "replace"))

        if to_continue:
            self.add_row(QLabel("Needing more work"))
            for mod in to_continue:
                    self.add_row(QLabel(str(mod.detid)), AssemblyButton("Proceed", self, mod.detid, "continue"))

    def to_replace(self):
        modules_to_replace = [Module(m, geometry_df = self.detids) for m in self.modules if m.status.test_status == 'faulty']
        return sorted(modules_to_replace, key=attrgetter('ring', 'module_phi_deg'))

    def to_continue(self):
        modules_to_continue = [Module(m, geometry_df = self.detids) for m in self.modules if m.status.tested is None]
        return sorted(modules_to_continue, key=attrgetter('next_step_order', 'ring', 'module_phi_deg'))

    def next_bundle(self, empty_bundles):
        """
        determine the next bundle to start screwing
        it should be the one containing the most central module of the most external ring
        """
        # TODO: this requires that PHI angles are brought back up and flipped if needed: check it works
        max_ring = 0
        central_phi = 180
        best_detid = None
        best_bundle = None
        for bundle, detids in empty_bundles.items():
            for detid in detids:
                if self.detids.loc[detid]['ring'] > max_ring:
                    max_ring = self.detids.loc[detid]['ring']
                if self.detids.loc[detid]['ring'] == max_ring and abs(self.detids.loc[detid]['module_phi_deg'] - 90) < central_phi:
                    central_phi =  abs(self.detids.loc[detid]['module_phi_deg'] - 90)
                    best_detid = detid
                    best_bundle = bundle

        return best_detid, best_bundle

    def process_bundles(self):
        """
        determine bundles with some modules not yet screwed
        """
        to_fill = {}
        full = []
        dee_bundles = self.detids.reset_index().groupby('mfb')['Module_DetId/i'].apply(list).to_dict()
        bundles_installed = defaultdict(list)
        for module in self.modules:
            bundle = self.geometry.loc[module.status.detid]['mfb']
            bundles_installed[bundle].append(module.status.detid)

        for bundle, detids in bundles_installed.items():
            if len(detids) != len(dee_bundles[bundle]):
                to_fill[bundle] = [detid for detid in dee_bundles[bundle] if detid not in detids]
            else:
                full.append(bundle)
            dee_bundles.pop(bundle)
            
        return full, to_fill, dee_bundles

    def clear_display(self):
        """
        remove current shown modules
        """
        while self.dee_status_display.count() > 0:
            line = self.dee_status_display.takeAt(0)
            while line.count() > 0:
                item = line.takeAt(0)
                if not item:
                    continue

                w = item.widget()
                if w:
                    w.deleteLater()
            line.deleteLater()

    def add_row(self, w1, w2 = None):
        if w2 is None:
            self.next_layout.addWidget(w1, self.next_steps_table_rows, 0, 1, 2, Qt.AlignCenter)
        else:
            self.next_layout.addWidget(w1, self.next_steps_table_rows, 0)
            self.next_layout.addWidget(w2, self.next_steps_table_rows, 1)
        self.next_steps_table_rows += 1

    def go_to_assembly(self):
        sender = self.sender()
        dialog = None
        if sender.next_step == "screw":
            dialog = ScrewDialog(self, sender.detid)

        if dialog:
            dialog.exec()


class AssemblyButton(QPushButton):
    """
    display a button to get to the assembly guide with the right step
    """
    def __init__(self, text, parent = None, detid = None, next_step = None):
        super().__init__(text, parent)
        self.detid = detid
        self.next_step = next_step
        try:
            self.clicked.connect(parent.go_to_assembly)
        except AttributeError:
            logging.warning("Parent class misses the requested method 'go_to_assembly'")


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
            text = f"{detid}\n{self.module.barcode}\n{self.geo_data['mfb']}"
            self.setText(text)
        else:
            text = f"{detid}\n\n{self.geo_data['mfb']}"
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
