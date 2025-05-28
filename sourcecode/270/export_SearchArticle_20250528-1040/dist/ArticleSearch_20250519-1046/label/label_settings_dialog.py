#label_settings_dialog
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QMessageBox, QGroupBox, QScrollArea, QWidget
)
from settings import load_label_settings, save_label_settings

from PySide6.QtGui import QShortcut, QKeySequence


class LabelSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Labelinstellingen")
        self.resize(500, 700)
        self.fields = {}
        self._build_ui()

    def _build_ui(self):
        current = load_label_settings()

        # Centrale layout voor de dialog
        outer_layout = QVBoxLayout(self)

        # Scrollable gebied
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        main_layout = QVBoxLayout(scroll_content)

        # Alle groepen toevoegen
        main_layout.addWidget(self._build_group("Afmetingen", {
            "LABEL_WIDTH": "Labelbreedte (mm)",
            "LABEL_HEIGHT": "Labelhoogte (mm)"
        }, current))

        main_layout.addWidget(self._build_group("Barcode", {
            "BARCODE_TOP": "Barcode bovenafstand (mm)",
            "BARCODE_LEFT": "Barcode linksafstand (mm)",
            "BARCODE_WIDTH_SCALE": "Barcode breedte schaal",
            "BARCODE_HEIGHT_SCALE": "Barcode hoogte schaal"
        }, current))

        main_layout.addWidget(self._build_group("Artikel positie", {
            "ART_TOP": "Artikel bovenafstand (mm)",
            "ART_LEFT": "Artikel linksafstand (mm)"
        }, current))

        main_layout.addWidget(self._build_group("Beschrijving", {
            "DESCRIPTION_TOP": "Beschrijving bovenafstand (mm)",
            "DESCRIPTION_LEFT": "Beschrijving linksafstand (mm)",
            "DESCRIPTION_WIDTH": "Beschrijving breedte (mm)"
        }, current))

        main_layout.addWidget(self._build_group("Datum", {
            "DATE_TOP": "Datum bovenafstand (mm)",
            "DATE_LEFT": "Datum linksafstand (mm)"
        }, current))

        main_layout.addWidget(self._build_group("Inbound", {
            "INBOUND_TOP": "Inbound bovenafstand (mm)",
            "INBOUND_LEFT": "Inbound linksafstand (mm)"
        }, current))

        main_layout.addWidget(self._build_group("Leverancier", {
            "SUPPLIER_TOP": "Leverancier bovenafstand (mm)",
            "SUPPLIER_LEFT": "Leverancier linksafstand (mm)"
        }, current))

        main_layout.addWidget(self._build_group("Lettergroottes", {
            "FONT_SIZE_ART": "Grootte Artikel",
            "FONT_SIZE_DESCRIPTION": "Grootte Beschrijving",
            "FONT_SIZE_SUPPLIER": "Grootte Leverancier",
            "FONT_SIZE_INBOUND": "Grootte Inbound",
            "FONT_SIZE_DATE": "Grootte Datum"
        }, current))

        scroll_area.setWidget(scroll_content)
        outer_layout.addWidget(scroll_area)

        save_btn = QPushButton("Opslaan")
        save_btn.clicked.connect(self._save)
        outer_layout.addWidget(save_btn)
        
        save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        save_shortcut.activated.connect(self._save)

    def _build_group(self, title, keys_labels, current):
        group_box = QGroupBox(title)
        form_layout = QFormLayout()

        for key, label in keys_labels.items():
            field = QLineEdit()
            field.setText(str(current.get(key, "")))
            self.fields[key] = field
            form_layout.addRow(label, field)

        group_box.setLayout(form_layout)
        return group_box

    def _save(self):
        try:
            new_settings = {}
            for key, field in self.fields.items():
                new_settings[key] = float(field.text())

            save_label_settings(new_settings)
            QMessageBox.information(self, "Opgeslagen", "Labelinstellingen zijn opgeslagen.")
            self.accept()
        except ValueError as e:
            QMessageBox.warning(self, "Fout", f"Alle velden moeten numeriek zijn.\n\n{e}")
