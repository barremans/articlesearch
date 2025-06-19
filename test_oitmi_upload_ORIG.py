#test_oitmi_upload.py
import sys
import json
import base64
import requests
from io import BytesIO
from PIL import Image, UnidentifiedImageError
from oitmi_token import get_auth_header
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QTextEdit, QSpinBox, QMessageBox,
    QFileDialog, QComboBox
)
from PySide6.QtGui import QKeySequence, QShortcut



class ImageUploader(QWidget):
    def __init__(self, item_code="", description="", vendor_id="", vendor_name="", weblink="", original_blob="", oitmi_id="", oitmi_type="IMG"):
        super().__init__()
        self.setWindowTitle("OITMI Upload Tester")
        self.setMinimumWidth(600)
        
        esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        esc_shortcut.activated.connect(self.close)


        self.original_blob = original_blob.strip()
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

        for label, widget in [
            ("Beschrijving (DESCR):", self.descr_input),
            ("Artikelnummer (ID):", self.id_input),
            ("TYPE:", self.type_input),
            ("VENDORID:", self.vendorid_input),
            ("WEBLINK:", self.weblink_input),
            ("VENDORNAME:", self.vendorname_input),
            ("Technische ID (OITMI_ID):", self.oitmi_id_input)
        ]:
            layout.addWidget(QLabel(label))
            layout.addWidget(widget)

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

        self.api_button = QPushButton("Stuur naar API")
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
            encoded = base64.b64encode(output.getvalue()).decode("utf-8")
            self.output_text.setPlainText(encoded)
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
            encoded = base64.b64encode(output.getvalue()).decode("utf-8")
            self.output_text.setPlainText(encoded)
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Fout bij verwerken bestand:\n{e}")

    def _reencode_original_blob(self) -> str:
        try:
            blob_data = self.original_blob
            if blob_data.startswith("data:image"):
                blob_data = blob_data.split(",", 1)[1]

            # Decode 2 keer
            decoded_once = base64.b64decode(blob_data)
            decoded_twice = base64.b64decode(decoded_once)

            image = Image.open(BytesIO(decoded_twice))
            output = BytesIO()
            image.save(output, format="PNG")
            return base64.b64encode(output.getvalue()).decode("utf-8")
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Afbeelding decoderen mislukt:\n{e}")
            return ""

    def send_to_api(self):
        blob = self.output_text.toPlainText().strip()
        if not blob:
            blob = self._reencode_original_blob()
            if not blob:
                return

        try:
            header = base64.b64decode(blob)[:8]
            if header.startswith(b'\x89PNG\r\n\x1a\n'):
                print("✅ PNG-header OK vóór verzending.")
            else:
                print(f"⚠️ PNG-header afwijken: {header}")
        except Exception as e:
            print("❌ Base64 decode error vóór verzending:", e)

        payload = {
            "DESCR": self.descr_input.text().strip(),
            "ID": self.id_input.text().strip(),
            "TYPE": self.type_input.currentText(),
            "VENDORID": self.vendorid_input.text().strip(),
            "WEBLINK": self.weblink_input.text().strip(),
            "VENDORNAME": self.vendorname_input.text().strip(),
            "BLOB": blob,
            "OITMI_ID": self.oitmi_id_input.text().strip()
        }

        required_keys = ["DESCR", "ID", "TYPE", "VENDORID", "WEBLINK", "VENDORNAME", "BLOB"]
        missing = [k for k in required_keys if not payload.get(k)]
        if missing:
            QMessageBox.warning(self, "Ontbrekende velden", f"Volgende velden zijn verplicht:\n{', '.join(missing)}")
            return

        try:
            actie = "UPDATE" if payload["OITMI_ID"] else "CREATE"
            endpoint = "U" if payload["OITMI_ID"] else "A"
            url = f"https://api.cgk-group.com/api/import/OITMI/{endpoint}/dbname/SBOCGKLIVE"
            headers = get_auth_header()
            headers["Content-Type"] = "application/json"

            print("\n📋 COPY PASTE DIT IN POSTMAN:")
            print(json.dumps(payload, indent=2))

            response = requests.post(url, headers=headers, json=payload, timeout=20, verify=False)
            response.raise_for_status()
            result = response.json() if response.content else {"message": "Upload succesvol, geen body."}
            print("✅ API response:")
            print(json.dumps(result, indent=2))
            QMessageBox.information(self, "Upload geslaagd", "✅ Upload succesvol.\nZie console voor details.")
        except Exception as e:
            print("❌ API-fout:", e)
            QMessageBox.critical(self, "Fout", f"Upload mislukt:\n{e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageUploader()
    window.show()
    sys.exit(app.exec())