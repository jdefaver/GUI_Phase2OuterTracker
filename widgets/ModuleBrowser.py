import re, string
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.uic import *

from local_database_definitions import LogEvent, ModuleStatus, ExternalModule

class ModuleBrowser(QWidget):

    actions_nice = {
        "screwed": "screwed",
        "pwr_status": "power connected",
        "opt_status": "optical connected",
        "tested": "tested"
    }

    def __init__(self, parent):
        super().__init__(parent)
        ui = loadUi('widgets_ui/browse_modules.ui', self) 
        self.ScanMOD.clicked.connect(self.start_scan)
        self.Enter_MODID.setEnabled(False)
        self.browseMODTab.setSortingEnabled(True)
        self.browseMODTab.cellClicked.connect(self.update_from_table)
        self.ComboBox_MODLocation.activated.connect(self.filter_modules)
        self.ComboBox_LastAction.activated.connect(self.filter_modules)
        self.ComboBox_Status.activated.connect(self.filter_modules)
        self.scanning = False
        self.barcode_chars = []

        self.db_session = parent.db_session
        self.geometry = parent.geometry

        self.fill_table()

    def start_scan(self):
        self.scanning = True
        self.Enter_MODID.setText("Scannning...")

    def keyPressEvent(self, event):
        if self.scanning:
            if event.key() == Qt.Key_Return:
                barcode = "".join([QKeySequence(i).toString() for i in self.barcode_chars])
                barcode = re.sub('[\W_]+', '', barcode)
                self.Enter_MODID.setText(barcode)
                self.barcode_chars = []
                self.scanning = False
                self.show_module_details(barcode)
            else:
                self.barcode_chars.append(event.key())
            event.accept()

    def show_module_details(self, barcode):
        text = f"Data for module {barcode}\n"
        text += len(text)*"="+"\n"
        module = self.db_session.query(ExternalModule).filter(ExternalModule.barcode == barcode).first()
        if module:
            text += "\n"+module.__str__()
            if(module.status):
                text += "\n\nInstallation status\n============\n"
                text += module.status.__str__()
                text += "\n\nGeometry data\n============\n"
                mgeo = self.geometry.loc[module.status.detid]
                text += f"opical bundle: {mgeo.mfb} on service {mgeo.opt_services_channel}"
        else:
            text += "\nModule not found"
        self.module_data.setText(text)

    def filter_modules(self):
        modules = self.db_session.query(ExternalModule)

        location = self.ComboBox_MODLocation.currentText()
        if location != '-':
            modules = modules.filter(ExternalModule.location == location)

        test_status = self.ComboBox_Status.currentText().lower()
        if test_status != '-':
            modules = modules.filter(ExternalModule.status.has(ModuleStatus.test_status == test_status))

        self.fill_table(modules)


    def update_from_table(self, row, col):
        self.browseMODTab.selectRow(row)
        barcode = self.browseMODTab.item(row, 0).text()
        self.show_module_details(barcode)


    def fill_table(self, modules=None):
        if modules == None:
            modules = self.db_session.query(ExternalModule).all()

        self.browseMODTab.setRowCount(0)
        for line, module in enumerate(modules):
            self.browseMODTab.insertRow(line)
            self.browseMODTab.setItem(line,0,QTableWidgetItem(module.barcode))
            self.browseMODTab.setItem(line,1,QTableWidgetItem(module.module_type))
            self.browseMODTab.setItem(line,2,QTableWidgetItem(module.module_thickness))
            self.browseMODTab.setItem(line,3,QTableWidgetItem(module.location))
            if module.status:
                status = self.actions_nice[[attr for attr in self.actions_nice.keys() if getattr(module.status,attr)][-1]]
                self.browseMODTab.setItem(line,4,QTableWidgetItem(status))
                self.browseMODTab.setItem(line,5,QTableWidgetItem(module.status.test_status))


