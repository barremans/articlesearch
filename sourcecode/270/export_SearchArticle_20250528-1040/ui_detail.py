
#ui_detail.py
import os
import base64
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMessageBox, QScrollArea, QHBoxLayout
)
from PySide6.QtGui import QPixmap, QGuiApplication, QShortcut, QKeySequence
from PySide6.QtCore import Qt
from settings import load_detail_modal


def safe_base64_decode(data: bytes) -> bytes:
    try:
        decoded = base64.b64decode(data)
        if decoded.startswith(b'\x89PNG\r\n\x1a\n'):
            return decoded
    except Exception:
        pass
    return data


class DetailWindow(QDialog):
    def __init__(self, item_code, detail_data: dict):
        super().__init__()
        self.setWindowTitle(f"Detail: {item_code}")
        if load_detail_modal():
            self.setWindowModality(Qt.ApplicationModal)
        else:
            self.setWindowFlag(Qt.WindowStaysOnTopHint)

        self.resize(1000, 700)
        self._center_window()

        self.item_code = item_code
        self.detail_data = detail_data
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self._add_lisa_tab()               # 0
        self._add_sap_tab()                # 1
        self._add_financial_purchase_tab() # 2
        self._add_financial_sales_tab()    # 3
        self._add_logistics_tab()          # 4
        self._add_last_purch_tab()         # 5
        self._add_image_tab()              # 6

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Artikelcode: {item_code}"))
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        # ALT-sneltoetsen voor tabnavigatie
        QShortcut(QKeySequence("Alt+L"), self).activated.connect(lambda: self.tabs.setCurrentIndex(0))  # LISA
        QShortcut(QKeySequence("Alt+S"), self).activated.connect(lambda: self.tabs.setCurrentIndex(1))  # SAP
        QShortcut(QKeySequence("Alt+A"), self).activated.connect(lambda: self.tabs.setCurrentIndex(2))  # Aankoop
        QShortcut(QKeySequence("Alt+V"), self).activated.connect(lambda: self.tabs.setCurrentIndex(3))  # Verkoop
        QShortcut(QKeySequence("Alt+G"), self).activated.connect(lambda: self.tabs.setCurrentIndex(4))  # Logistiek
        QShortcut(QKeySequence("Alt+R"), self).activated.connect(lambda: self.tabs.setCurrentIndex(5))  # Recent
        QShortcut(QKeySequence("Alt+F"), self).activated.connect(lambda: self.tabs.setCurrentIndex(6))  # Foto

    def _add_tab(self, title, data, headers):
        tab = QWidget()
        layout = QVBoxLayout()
        table = QTableWidget()

        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels(headers)
            for row, record in enumerate(data):
                for col, key in enumerate(headers):
                    val = str(record.get(key, ""))
                    item = QTableWidgetItem(val)
                    item.setToolTip(val)
                    table.setItem(row, col, item)
        else:
            table.setRowCount(1)
            table.setColumnCount(1)
            table.setHorizontalHeaderLabels(["Informatie"])
            item = QTableWidgetItem(f"❌ Geen {title} data beschikbaar.")
            item.setToolTip(item.text())
            table.setItem(0, 0, item)

        table.doubleClicked.connect(lambda index: self._copy_table_row_to_clipboard(table, index))
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, title)

    def _add_lisa_tab(self):
        data = self.detail_data.get("STOCK", {}).get("LISA", [])
        headers = ["LOCNAME", "WHSNAME", "QUANTITY", "QTYRESERVED", "QTYMININV", "QTYMAXINV"]
        self._add_tab("📦 LISA", data, headers)

    def _add_sap_tab(self):
        raw_data = self.detail_data.get("STOCK", {}).get("SAP", [])
        data = []
        for entry in raw_data:
            vrije_stock = entry.get("OnHand", 0) - entry.get("IsCommited", 0)
            data.append({
                "WhsName": entry.get("WhsName", ""),
                "OnHand": entry.get("OnHand", 0),
                "IsCommited": entry.get("IsCommited", 0),
                "OnOrder": entry.get("OnOrder", 0),
                "MinStock": entry.get("MinStock", 0),
                "MaxStock": entry.get("MaxStock", 0),
                "VrijeStock": vrije_stock
            })
        headers = ["WhsName", "OnHand", "IsCommited", "OnOrder", "MinStock", "MaxStock", "VrijeStock"]
        self._add_tab("🏢 SAP", data, headers)

    def _add_financial_purchase_tab(self):
        data = self.detail_data.get("FIN", {}).get("PURCH", [])
        headers = ["Price", "Currency", "BuyUnitMsr", "NumInBuy", "PurPackMsr", "PurPackUn", "LastPurPrc"]
        self._add_tab("💰 Aankoop", data, headers)

    def _add_financial_sales_tab(self):
        data = self.detail_data.get("FIN", {}).get("SALES", [])
        headers = ["Price", "Currency", "SalUnitMsr", "NumInSale", "SalPackMsr", "SalPackUn"]
        self._add_tab("💸 Verkoop", data, headers)

    def _add_logistics_tab(self):
        data = self.detail_data.get("LOG", {})
        excluded = {
            "validFor", "validFrom", "validTo",
            "frozenFor", "frozenFrom", "frozenTo",
            "BlockOut", "ItemClass", "CLASSITEM"
        }
        filtered = [{"Veld": k, "Waarde": v} for k, v in data.items() if k not in excluded]
        self._add_tab("🚚 Logistiek", filtered, ["Veld", "Waarde"])

    def _add_last_purch_tab(self):
        data = self.detail_data.get("RET", [])
        headers = ["DocNum", "DocDate", "ItemCode", "Dscription", "Quantity", "ShipDate", "VendorNum", "BaseCard", "CardName", "WhsName"]
        self._add_tab("📄 Laatste aankoop", data, headers)

    def _add_image_tab(self):
        images = self.detail_data.get("IMG", [])
        tab = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        upload_button = QPushButton("📤 Upload nieuwe aanpassingen")
        upload_button.clicked.connect(self._open_image_uploader)
        main_layout.addWidget(upload_button)

        if images:
            first_img = images[0]
            weblink = first_img.get("OITMI_WEBLINK", "")
            if weblink:
                link_label = QLabel(f"<a href='{weblink}'>{weblink}</a>")
                link_label.setOpenExternalLinks(True)
                link_label.setAlignment(Qt.AlignLeft)
                main_layout.addWidget(link_label)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        image_container = QWidget()
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        image_layout.setSpacing(10)
        image_layout.setAlignment(Qt.AlignTop)

        if images:
            for img in images:
                image_data = img.get("OITMI_IMAGE", "")
                label = QLabel()
                label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)

                if image_data:
                    try:
                        raw_base64 = image_data.split(",", 1)[-1].strip().replace("\n", "").replace(" ", "")
                        decoded_once = base64.b64decode(raw_base64)
                        image_bytes = safe_base64_decode(decoded_once)

                        pixmap = QPixmap()
                        if pixmap.loadFromData(image_bytes):
                            label.setPixmap(pixmap.scaledToWidth(300))
                        else:
                            label.setText("❌ Ongeldige afbeelding")
                    except Exception as e:
                        label.setText(f"❌ Decode fout: {e}")
                else:
                    label.setText("❌ Geen afbeelding aanwezig")

                image_wrapper = QWidget()
                wrapper_layout = QHBoxLayout(image_wrapper)
                wrapper_layout.setContentsMargins(0, 0, 0, 0)
                wrapper_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
                wrapper_layout.addWidget(label)

                image_layout.addWidget(image_wrapper)
        else:
            image_layout.addWidget(QLabel("❌ Geen afbeeldingen beschikbaar."))

        scroll_area.setWidget(image_container)
        main_layout.addWidget(scroll_area)

        tab.setLayout(main_layout)
        self.tabs.addTab(tab, "🖼️ Afbeelding")

    def _open_image_uploader(self):
        from test_oitmi_upload import ImageUploader

        img_data = self.detail_data["IMG"][0] if self.detail_data.get("IMG") else {}
        image_blob = img_data.get("OITMI_IMAGE", "")

        self.uploader_window = ImageUploader(
            item_code=img_data.get("ID", self.item_code),
            description=img_data.get("OITMI_DESCRIPTION", ""),
            vendor_id=img_data.get("OITMI_VENDORID", ""),
            vendor_name=img_data.get("OITMI_VENDORNAME", ""),
            weblink=img_data.get("OITMI_WEBLINK", ""),
            original_blob=image_blob,
            oitmi_id=str(img_data.get("OITMI_ID", "")),
            oitmi_type=img_data.get("OITMI_TYPE", "IMG")
        )
        self.uploader_window.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.uploader_window.show()

    def _copy_table_row_to_clipboard(self, table, index):
        row = index.row()
        values = [table.item(row, col).text() if table.item(row, col) else "" for col in range(table.columnCount())]
        QGuiApplication.clipboard().setText("\t".join(values))
        QMessageBox.information(self, "Gekopieerd", "Rijinhoud is naar het klembord gekopieerd.")

    def _center_window(self):
        frame_geometry = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())