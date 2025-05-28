# oitmi_upload.py
# test_oitmi_upload.py

import sys
import json
import base64
import requests
from io import BytesIO
from PIL import Image
from oitmi_upload import upload_image_data  # ← wordt nu NIET gebruikt
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QSpinBox, QMessageBox,
    QFileDialog, QComboBox
)
import time


class ImageUploader(QWidget):
    def __init__(
        self,
        item_code="",
        description="",
        vendor_id="",
        vendor_name="",
        weblink="",
        original_blob="",
        oitmi_id="",
        oitmi_type="IMG"
    ):
        super().__init__()
        self.setWindowTitle("OITMI Upload Tester")
        self.setMinimumWidth(600)

        self.original_blob = original_blob
        self.oitmi_id = str(oitmi_id)
        self.oitmi_type = oitmi_type

        layout = QVBoxLayout()

        self.descr_input = QLineEdit(description)
        self.id_input = QLineEdit(item_code)
        self.id_input.setReadOnly(True)
        self.type_input = QComboBox()
        self.type_input.addItems(["IMG", "PDF"])
        self.type_input.setCurrentText(oitmi_type)
        self.vendorid_input = QLineEdit(vendor_id)
        self.vendorname_input = QLineEdit(vendor_name)
        self.weblink_input = QLineEdit(weblink)
        self.oitmi_id_input = QLineEdit(self.oitmi_id)
        self.oitmi_id_input.setReadOnly(True)

        layout.addWidget(QLabel("Beschrijving (OITMI_DESCRIPTION):"))
        layout.addWidget(self.descr_input)
        layout.addWidget(QLabel("ID (OITMI_ITRMID):"))
        layout.addWidget(self.id_input)
        layout.addWidget(QLabel("TYPE (OITMI_TYPE):"))
        layout.addWidget(self.type_input)
        layout.addWidget(QLabel("VENDORID (OITMI_VENDORID):"))
        layout.addWidget(self.vendorid_input)
        layout.addWidget(QLabel("WEBLINK (OITMI_WEBLINK):"))
        layout.addWidget(self.weblink_input)
        layout.addWidget(QLabel("VENDORNAME (OITMI_VENDORNAME):"))
        layout.addWidget(self.vendorname_input)
        layout.addWidget(QLabel("OITMI_ID (readonly):"))
        layout.addWidget(self.oitmi_id_input)

        layout.addWidget(QLabel("Afbeelding URL:"))
        self.url_input = QLineEdit()
        layout.addWidget(self.url_input)

        layout.addWidget(QLabel("Breedte (pixels):"))
        self.width_input = QSpinBox()
        self.width_input.setRange(1, 2000)
        self.width_input.setValue(300)
        layout.addWidget(self.width_input)

        self.convert_button = QPushButton("Zet om naar PNG Base64 (via URL)")
        self.convert_button.clicked.connect(self.convert_image)
        layout.addWidget(self.convert_button)

        self.upload_button = QPushButton("Selecteer lokaal bestand en converteer")
        self.upload_button.clicked.connect(self.upload_from_file)
        layout.addWidget(self.upload_button)

        layout.addWidget(QLabel("Base64 PNG output:"))
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        layout.addWidget(self.output_text)

        self.api_button = QPushButton("Stuur naar API (TESTMODE)")
        self.api_button.clicked.connect(self.send_to_api)
        layout.addWidget(self.api_button)

        self.setLayout(layout)

    def convert_image(self):
        try:
            url = self.url_input.text().strip()
            width = self.width_input.value()
            response = requests.get(url)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content))

            new_height = int(width * (image.height / image.width))
            resized_image = image.resize((width, new_height))

            output = BytesIO()
            resized_image.save(output, format="PNG")
            self.output_text.setPlainText(base64.b64encode(output.getvalue()).decode("utf-8"))
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Afbeelding kon niet worden verwerkt:\n{e}")

    def upload_from_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Selecteer afbeelding", "", "Images (*.png *.jpg *.jpeg *.bmp *.webp)")
        if not file_path:
            return
        try:
            image = Image.open(file_path)
            width = self.width_input.value()
            new_height = int(width * (image.height / image.width))
            resized_image = image.resize((width, new_height))

            output = BytesIO()
            resized_image.save(output, format="PNG")
            self.output_text.setPlainText(base64.b64encode(output.getvalue()).decode("utf-8"))
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Fout bij verwerken bestand:\n{e}")

    def send_to_api(self):
        base64_data = self.output_text.toPlainText().strip()
        blob = base64_data if base64_data else self.original_blob.strip()

        payload = {
            "OITMI_DESCRIPTION": self.descr_input.text().strip(),
            "OITMI_ITRMID": self.id_input.text().strip(),
            "OITMI_TYPE": self.type_input.currentText(),
            "OITMI_VENDORID": self.vendorid_input.text().strip(),
            "OITMI_WEBLINK": self.weblink_input.text().strip(),
            "OITMI_VENDORNAME": self.vendorname_input.text().strip(),
            "OITMI_IMAGE": blob,
            "OITMI_ID": self.oitmi_id_input.text().strip()
        }

        required_keys = [
            "OITMI_DESCRIPTION", "OITMI_ITRMID", "OITMI_TYPE",
            "OITMI_VENDORID", "OITMI_WEBLINK", "OITMI_VENDORNAME", "OITMI_IMAGE"
        ]
        missing = [k for k in required_keys if not payload.get(k)]
        if missing:
            QMessageBox.warning(self, "Ontbrekende velden", f"Volgende velden zijn verplicht:\n{', '.join(missing)}")
            return

        # Debug output
        print("\n📦 --- DEBUG: API REQUEST ---")
        actie = "UPDATE" if payload["OITMI_ID"] else "CREATE"
        endpoint = "U" if payload["OITMI_ID"] else "A"
        url = f"https://api.cgk-group.com/api/import/OITMI/{endpoint}/dbname/SBOCGKLIVE"
        headers = {"Authorization": "Bearer <token>", "Content-Type": "application/json"}

        print(f"🔁 Actie: {actie}")
        print(f"➡️  URL: {url}")
        print("🧾 Headers:")
        print(json.dumps(headers, indent=2))
        print("📤 Payload:")
        print(json.dumps(payload, indent=2))
        print("🚫 [TESTMODE] Geen API-call uitgevoerd.")
        QMessageBox.information(self, "DEBUG", "API-call is gesimuleerd.\nCheck console voor details.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageUploader()
    window.show()
    sys.exit(app.exec())
