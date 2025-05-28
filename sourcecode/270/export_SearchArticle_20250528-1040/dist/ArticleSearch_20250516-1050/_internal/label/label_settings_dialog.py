# label_settings_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton, QMessageBox, QGroupBox
)
from settings import load_label_settings, save_label_settings


class LabelSettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Labelinstellingen")
        self.resize(400, 500)
        self.fields = {}
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout()
        current = load_label_settings()

        # Groepen per categorie
        main_layout.addWidget(self._build_group("Afmetingen", {
            "LABEL_WIDTH": "Labelbreedte (mm)",
            "LABEL_HEIGHT": "Labelhoogte (mm)"
        }, current))

        main_layout.addWidget(self._build_group("Barcode positie", {
            "BARCODE_TOP": "Barcode bovenafstand",
            "BARCODE_LEFT": "Barcode linksafstand"
        }, current))

        main_layout.addWidget(self._build_group("Beschrijving positie", {
            "DESCRIPTION_TOP": "Beschrijving bovenafstand",
            "DESCRIPTION_WIDTH": "Beschrijving breedte"
        }, current))

        main_layout.addWidget(self._build_group("Datumpositie", {
            "DATE_TOP": "Datum bovenafstand",
            "DATE_LEFT": "Datum linksafstand"
        }, current))

        main_layout.addWidget(self._build_group("Inbound positie", {
            "INBOUND_TOP": "Inbound bovenafstand",
            "INBOUND_LEFT": "Inbound linksafstand"
        }, current))

        main_layout.addWidget(self._build_group("Leverancier positie", {
            "SUPPLIER_TOP": "Leverancier bovenafstand",
            "SUPPLIER_LEFT": "Leverancier linksafstand"
        }, current))

        save_btn = QPushButton("Opslaan")
        save_btn.clicked.connect(self._save)
        main_layout.addWidget(save_btn)

        self.setLayout(main_layout)

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
