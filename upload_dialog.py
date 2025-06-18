# upload_dialog.py
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QFileDialog, QHBoxLayout, QMessageBox
)
from pathlib import Path
from oitmi_upload import convert_file_to_base64, upload_image_data


class UploadDialog(QDialog):
    def __init__(self, item_code: str, parent=None, on_success=None):
        super().__init__(parent)
        self.setWindowTitle("Upload afbeelding/PDF")
        self.resize(500, 300)

        self.item_code = item_code
        self.on_success = on_success
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.file_input = QLineEdit()
        browse_btn = QPushButton("Bladeren")
        browse_btn.clicked.connect(self._choose_file)

        file_row = QHBoxLayout()
        file_row.addWidget(self.file_input)
        file_row.addWidget(browse_btn)

        self.descr_input = QLineEdit()
        self.vendor_id_input = QLineEdit()
        self.vendor_name_input = QLineEdit()
        self.link_input = QLineEdit()

        form.addRow("Bestand:", file_row)
        form.addRow("Beschrijving:", self.descr_input)
        form.addRow("Vendor ID:", self.vendor_id_input)
        form.addRow("Vendor Naam:", self.vendor_name_input)
        form.addRow("Weblink:", self.link_input)

        upload_btn = QPushButton("Uploaden")
        upload_btn.clicked.connect(self._upload)

        layout.addLayout(form)
        layout.addWidget(upload_btn)
        self.setLayout(layout)

    def _choose_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Kies bestand", "", "Afbeelding/PDF (*.png *.jpg *.jpeg *.pdf)"
        )
        if file_path:
            self.file_input.setText(file_path)

    def _upload(self):
        try:
            path = Path(self.file_input.text())
            if not path.exists():
                raise FileNotFoundError("Bestand niet gevonden.")

            blob = convert_file_to_base64(path)
            payload = {
                "DESCR": self.descr_input.text(),
                "ID": self.item_code,
                "TYPE": "IMG",
                "VENDORID": self.vendor_id_input.text(),
                "WEBLINK": self.link_input.text(),
                "BLOB": blob,
                "OITMI_ID": "",
                "VENDORNAME": self.vendor_name_input.text()
            }

            response = upload_image_data(payload)

            QMessageBox.information(self, "Gelukt", f"✅ Upload voltooid.\nAntwoord: {response}")

            if self.on_success:
                self.on_success()
            self.accept()


        except Exception as e:
            QMessageBox.critical(self, "Fout", f"❌ Upload mislukt:\n{e}")
