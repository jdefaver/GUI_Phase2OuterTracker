from collections import defaultdict
from operator import attrgetter
import numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule
from Module import Module

class AssemblyStatus(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        ui = loadUi('widgets_ui/assembly_status.ui', self) 

        self.geometry = parent.geometry
        self.db_session = parent.db_session

        self.select_dee.clicked.connect(self.show_dee_status)

        self.detids = None

    def show_dee_status(self):
        """
        show modules and status
        """
        self.clear_display()
        side = self.dee_side.currentText()
        layer = self.dee_layer.currentText()
        surface = self.dee_surface.currentText()
        vertical = self.dee_vertical.currentText()
        self.detids = self.geometry.full_selector(side, int(layer), int(surface), vertical, fix_phi = True)
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

        text = ""

        if incomplete:
            text += "\n### Incomplete bundles\n"
            for bundle, detids in incomplete.items():
                text += f" * {bundle}: {', '.join(str(detid) for detid in detids)}\n"

        if next_detid:
            text += "\n### Next Bundle to start\n"
            text += f" * Please start installing on detid {next_detid} in bundle {next_bundle}\n"
            text += f" * Location : ring {self.detids.loc[next_detid]['ring']}, phi = {self.detids.loc[next_detid]['module_phi_deg']:.2f}\n"

        if to_replace:
            text += "\n### Modules to replace\n"
            text += "\n".join(mod.markdown for mod in to_replace)+"\n"

        if to_continue:
            text += "\n### Modules needing more work\n"
            text += "\n".join(mod.markdown+f", next: {mod.next_step}" for mod in to_continue)+"\n"

        print(text)

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
            text = f"{detid}\n{self.module.barcode}\n{self.geo_data['mfb']}"
            self.setText(text)
            # self.setText(self.module.barcode+"\n\n")
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
