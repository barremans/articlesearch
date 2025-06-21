
#ui_detail.py
import os
import base64
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMessageBox, QScrollArea, QHBoxLayout, QStyle,    QTextEdit, 
    QFileDialog   
)
from PySide6.QtGui import QPixmap, QGuiApplication, QShortcut, QKeySequence, QIcon
from PySide6.QtCore import Qt
from settings import load_detail_modal, load_detail_qss_path

# from oitmi_upload import ImageUploader

def safe_base64_decode(data: bytes) -> bytes:
    try:
        decoded = base64.b64decode(data)
        if decoded.startswith(b'\x89PNG\r\n\x1a\n'):
            return decoded
    except Exception:
        pass
    return data


class DetailWindow(QDialog):
    def __init__(self, parent=None, item_code=None, detail_data: dict = None):
        super().__init__(parent)
                # — Zet dit dialoog bovenop én verwijder drag‐handles en resize‐knoppen —
        self.setWindowFlags(
            Qt.Dialog
            | Qt.WindowStaysOnTopHint
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )
        # Optioneel: geef een vaste grootte (hier 800×600) zodat user niet kan resizen
        #self.setFixedSize(1400, 800)
        self.resize(1400, 800)

        
        self.item_code = item_code
        self.detail_data = detail_data or {}

        self.setWindowTitle(f"Detail: {item_code}")
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "mark.png")
        self.setWindowIcon(QIcon(icon_path))
       # self.setWindowIcon(QGuiApplication.style().standardIcon(QStyle.SP_MessageBoxInformation))

        if load_detail_modal():
            self.setWindowModality(Qt.ApplicationModal)
        #else:
        #    self.setWindowFlag(Qt.WindowStaysOnTopHint)

        #self.resize(1000, 700)
        self._center_window()
        
        # Lijst om alle sub‐vensters (zoals ImageUploader) in op te slaan
        self.child_windows = []

        #self.item_code = item_code
        #self.detail_data = detail_data
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
        
        # —————— Laad opgeslagen detail.qss bij openen ——————
        detail_qss = load_detail_qss_path()
        if detail_qss and os.path.exists(detail_qss):
            try:
                with open(detail_qss, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception:
                pass
        # ————————————————————————————————————————————

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
        images = self.detail_data.get("DIG", [])
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
        from oitmi_upload import ImageUploader, safe_base64_cleanup  # ← extra functie

        images = self.detail_data.get("DIG", [])
        img_data = images[0] if images and isinstance(images[0], dict) else {}

        raw_blob = img_data.get("OITMI_IMAGE", "")
        cleaned_blob = safe_base64_cleanup(raw_blob) if raw_blob else ""

        uploader = ImageUploader(
            parent=self,
            item_code=img_data.get("OITMI_ITRMID", self.item_code),
            description=img_data.get("OITMI_DESCRIPTION", ""),
            vendor_id=img_data.get("OITMI_VENDORID", ""),
            vendor_name=img_data.get("OITMI_VENDORNAME", ""),
            weblink=img_data.get("OITMI_WEBLINK", ""),
            original_blob=cleaned_blob,
            oitmi_id=str(img_data.get("OITMI_ID", "")),
            oitmi_type=img_data.get("OITMI_TYPE", "IMG")
        )

        uploader.uploadSuccess.connect(self._on_uploader_closed)
        uploader.show()
        uploader.raise_()
        uploader.activateWindow()
        self.child_windows.append(uploader)



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
        
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    # — OVERRIDING MOVEEvent en RESIZEEvent zodat ImageUploader meebeweegt —
    def moveEvent(self, event):
        super().moveEvent(event)
        for child in self.child_windows:
            if child.isVisible():
                self._reposition_child(child)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for child in self.child_windows:
            if child.isVisible():
                self._reposition_child(child)

    def _reposition_child(self, child_widget):
        # Kies de vaste offset t.o.v. de linkerbovenhoek van DetailWindow.
        # In dit voorbeeld: altijd 20px naar rechts en 20px naar beneden
        parent_pos = self.pos()          # QPoint(x, y) van DetailWindow
        offset_x = 2
        offset_y = 2
        new_x = parent_pos.x() + offset_x
        new_y = parent_pos.y() + offset_y
        child_widget.move(new_x, new_y)
    # — EINDE OVERRIDES —

    # — NIEUWE METHODES VOOR “UPDATE IMAGE NA SUCCESVOLLE API‐CALL” —
    def _on_uploader_closed(self):
        """
        Wordt aangeroepen zodra ImageUploader.uploadSuccess wordt uitgezonden.
        We halen de nieuwste detail_data op en verversen het Afbeelding‐tabblad.
        """
        try:
            from stock_info import get_item_detail_stockinfo
            new_data = get_item_detail_stockinfo(self.item_code) or {}
            self.detail_data = new_data
            self._refresh_image_tab()
        except Exception as e:
            QMessageBox.warning(self, "Refresh Fout", f"Kon afbeeldinggegevens niet verversen:\n{e}")

    def _refresh_image_tab(self):
        """
        Verwijdert het oude ‘🖼️ Afbeelding’ tabblad en voegt het opnieuw toe
        met de geüpdatete self.detail_data["IMG"].
        """
        for idx in range(self.tabs.count()):
            if self.tabs.tabText(idx) == "🖼️ Afbeelding":
                self.tabs.removeTab(idx)
                break

        self._add_image_tab()
    # — EINDE NIEUWE METHODES —