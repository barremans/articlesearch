# =============================================================================
# ArticleSearch
# File:    ui_detail.py
# Role:    Detail-popup venster voor een artikel (QDialog) — tabbladen LISA,
#          SAP, Dimensions, Aankoop, Verkoop, Logistiek, Laatste aankoop,
#          Afbeelding, ATP. Ontvangt de volledige ZStockInfoP-payload
#          (detail_data) van ui_main.py en verdeelt de sub-secties over de
#          tab-widgets.
# Version: 1.3.0
# Author:  Bart Bossuyt
# Changes: 1.3.0 — BUGFIX vervolg (screenshot Bart Bossuyt, artikel
#                   152.PPECO200515): Beschrijving werd al correct
#                   vooringevuld (v1.2.0), maar VENDORID/VENDORNAME bleven
#                   leeg zodra er nog geen aankoophistorie (RET) was — een
#                   nieuw artikel heeft immers nog geen "Laatste aankoop".
#                   Nieuwe constructor-parameters vendor_hint_id/
#                   vendor_hint_name (meegegeven vanuit ui_main.py's
#                   zoekresultaat-rij: "Vendor Nr"/"Leverancier"-kolommen,
#                   SuppCatNum/SUPPLIERIDPRODUCT/SUPPLIERNAME — velden die
#                   niet in de ZStockInfoP-detailpayload zelf zitten).
#                   _open_image_uploader() gebruikt deze nu als 2e fallback-
#                   laag, vóór de RET-fallback: OITMI-waarde > vendor_hint
#                   (zoekresultaat-rij) > RET (laatste aankoop). Zie
#                   ui_main.py v1.5.0 voor de aanroepende kant.
# Changes: 1.2.0 — BUGFIX (bugmelding Bart Bossuyt, 2026-08-25): OITMI
#                   Upload-dialoog opende met lege velden Beschrijving/
#                   VENDORID/VENDORNAME zodra een artikel nog geen bestaande
#                   afbeelding-record had (img_data leeg) — _open_image_
#                   uploader() gaf in dat geval altijd lege strings door.
#                   Nu: fallback naar reeds gekende artikelgegevens, ENKEL
#                   wanneer het overeenkomstige OITMI-veld zelf leeg is
#                   (bestaande OITMI-waarden hebben nog steeds voorrang):
#                     - Beschrijving  <- self.detail_data["ItemName"]
#                       (eigen omschrijving, al aanwezig in de payload)
#                     - VENDORID      <- meest recente "RET"-record
#                       (Laatste aankoop, zelfde payload)["VendorNum"]
#                       (leveranciersartikelnummer)
#                     - VENDORNAME    <- idem ["CardName"] (leveranciersnaam)
#                   Geen nieuwe API-call nodig — RET/ItemName zitten al in
#                   detail_data. "Meest recente" RET-record bepaald via
#                   max(DocDate), met fallback op eerste rij indien DocDate
#                   ontbreekt/onvergelijkbaar.
# Changes: 1.1.0 — Nieuwe tab "📐 Dimensions" toegevoegd, net na "SAP". Toont
#                   MEASUREMENT_INFO (afmetingen/gewicht) uit de bestaande
#                   ZStockInfoP-payload (config WEZ7CY) via de nieuwe
#                   DimensionsTab-widget (ui_dimensions.py) — geen nieuwe
#                   API-call/client nodig. Alt-sneltoetsen herverdeeld:
#                   Alt+D nieuw voor Dimensions (tabindex 2); Alt+A/V/G/R/F/T
#                   elk 1 index opgeschoven (was 2-7, wordt 3-8).
# Changes: 1.0.0 — Baseline: bestaande functionaliteit vóór introductie van
#                   versiebeheer in commentaar. Voorgeschiedenis (LISA/SAP/
#                   Aankoop/Verkoop/Logistiek/Laatste aankoop/Afbeelding/ATP-
#                   tabs, image-upload, ATP-tab) niet gedocumenteerd per
#                   deelversie — vanaf nu wel.
# =============================================================================
import os
import base64
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTabWidget, QWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QPushButton,
    QMessageBox, QScrollArea, QHBoxLayout, QStyle, QTextEdit,
    QFileDialog
)
from PySide6.QtGui import QPixmap, QGuiApplication, QShortcut, QKeySequence, QIcon
from PySide6.QtCore import Qt
from settings import load_detail_modal, load_detail_qss_path

from ui_lisa import LisaTab
from ui_sap import SapTab
from ui_dimensions import DimensionsTab
from ui_purchase import PurchaseTab
from ui_sales import SalesTab
from ui_lastpurch import LastPurchTab
from ui_logistics import LogisticsTab
from ui_atp import AtpWidget

def safe_base64_decode(data: bytes) -> bytes:
    try:
        decoded = base64.b64decode(data)
        if decoded.startswith(b'\x89PNG\r\n\x1a\n'):
            return decoded
    except Exception:
        pass
    return data


class DetailWindow(QDialog):
    def __init__(self, parent=None, item_code=None, detail_data: dict = None,
                 vendor_hint_id: str = "", vendor_hint_name: str = ""):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.Dialog |
            Qt.WindowStaysOnTopHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )
        self.resize(1400, 800)

        self.item_code = item_code
        self.detail_data = detail_data or {}
        # Vendor-hints uit de zoekresultaat-rij (ui_main.py) — "Vendor Nr"/
        # "Leverancier"-kolommen, niet aanwezig in detail_data zelf. Enkel
        # gebruikt als fallback bij het vooraf invullen van OITMI Upload.
        self.vendor_hint_id = (vendor_hint_id or "").strip()
        self.vendor_hint_name = (vendor_hint_name or "").strip()
        self.setWindowTitle(f"Detail: {item_code}")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "assets", "mark.png")))

        if load_detail_modal():
            self.setWindowModality(Qt.ApplicationModal)

        self._center_window()
        self.child_windows = []

        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)

        self._add_lisa_tab()
        self._add_sap_tab()
        self._add_dimensions_tab()
        self._add_financial_purchase_tab()
        self._add_financial_sales_tab()
        self._add_logistics_tab()
        self._add_last_purch_tab()
        self._add_image_tab()
        self._add_atp_tab()

        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Artikelcode: {item_code}"))
        layout.addWidget(self.tabs)
        self.setLayout(layout)

        detail_qss = load_detail_qss_path()
        if detail_qss and os.path.exists(detail_qss):
            try:
                with open(detail_qss, "r", encoding="utf-8") as f:
                    self.setStyleSheet(f.read())
            except Exception:
                pass

        # ALT-sneltoetsen voor tabnavigatie
        # Volgorde tabs: LISA(0), SAP(1), Dimensions(2), Aankoop(3), Verkoop(4),
        #                Logistiek(5), Laatste aankoop(6), Afbeelding(7), ATP(8)
        QShortcut(QKeySequence("Alt+L"), self).activated.connect(lambda: self.tabs.setCurrentIndex(0))
        QShortcut(QKeySequence("Alt+S"), self).activated.connect(lambda: self.tabs.setCurrentIndex(1))
        QShortcut(QKeySequence("Alt+D"), self).activated.connect(lambda: self.tabs.setCurrentIndex(2))
        QShortcut(QKeySequence("Alt+A"), self).activated.connect(lambda: self.tabs.setCurrentIndex(3))
        QShortcut(QKeySequence("Alt+V"), self).activated.connect(lambda: self.tabs.setCurrentIndex(4))
        QShortcut(QKeySequence("Alt+G"), self).activated.connect(lambda: self.tabs.setCurrentIndex(5))
        QShortcut(QKeySequence("Alt+R"), self).activated.connect(lambda: self.tabs.setCurrentIndex(6))
        QShortcut(QKeySequence("Alt+F"), self).activated.connect(lambda: self.tabs.setCurrentIndex(7))
        QShortcut(QKeySequence("Alt+T"), self).activated.connect(lambda: self.tabs.setCurrentIndex(8))


    def _add_tab(self, title, data, headers, headers_map):
        tab = QWidget()
        layout = QVBoxLayout()
        table = QTableWidget()

        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(headers))
            mapped_headers = [headers_map.get(h, h) for h in headers]
            table.setHorizontalHeaderLabels(mapped_headers)

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
            table.setItem(0, 0, QTableWidgetItem(f"❌ Geen {title} data beschikbaar."))

        table.doubleClicked.connect(lambda index: self._copy_table_row_to_clipboard(table, index))
        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
        tab.setLayout(layout)
        self.tabs.addTab(tab, title)

    def _add_lisa_tab(self):
        data = self.detail_data.get("STOCK", {}).get("LISA", [])
        tab = LisaTab(data)
        self.tabs.addTab(tab, "📦 LISA")


    def _add_sap_tab(self):
        raw_data = self.detail_data.get("STOCK", {}).get("SAP", [])
        tab = SapTab(raw_data)
        self.tabs.addTab(tab, "🏢 SAP")


    def _add_dimensions_tab(self):
        # MEASUREMENT_INFO zit als top-level dict in de ZStockInfoP-payload
        # (zelfde niveau als STOCK, GROUP_INFO, EXTRA_INFO) — geen aparte API-call nodig.
        data = self.detail_data.get("MEASUREMENT_INFO", {})
        tab = DimensionsTab(data)
        self.tabs.addTab(tab, "📐 Dimensions")

    def _add_financial_purchase_tab(self):
        data = self.detail_data.get("FIN", {}).get("PURCH", [])
        tab = PurchaseTab(data)
        self.tabs.addTab(tab, "💰 Aankoop")


    def _add_financial_sales_tab(self):
        data = self.detail_data.get("FIN", {}).get("SALES", [])
        tab = SalesTab(data)
        self.tabs.addTab(tab, "💸 Verkoop")


    def _add_last_purch_tab(self):
        data = self.detail_data.get("RET", [])
        tab = LastPurchTab(data)
        self.tabs.addTab(tab, "📄 Laatste aankoop")


    def _add_logistics_tab(self):
        data = self.detail_data.get("LOG", {})
        tab = LogisticsTab(data)
        self.tabs.addTab(tab, "🚚 Logistiek")


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
        from oitmi_upload import ImageUploader, safe_base64_cleanup

        images = self.detail_data.get("DIG", [])
        img_data = images[0] if images and isinstance(images[0], dict) else {}

        raw_blob = img_data.get("OITMI_IMAGE", "")
        cleaned_blob = safe_base64_cleanup(raw_blob) if raw_blob else ""

        # --- Fallback-gegevens vanuit het eigen artikel (al aanwezig in
        #     detail_data — geen extra API-call nodig), enkel gebruikt
        #     wanneer het overeenkomstige OITMI-veld zelf nog leeg is. ---
        own_description = self.detail_data.get("ItemName", "")

        last_purch = self.detail_data.get("RET", []) or []
        last_purch_record = {}
        if last_purch:
            try:
                # Meest recente aankoop op basis van DocDate
                last_purch_record = max(last_purch, key=lambda r: r.get("DocDate") or "")
            except Exception:
                last_purch_record = last_purch[0]

        fallback_vendor_id = last_purch_record.get("VendorNum", "")   # leveranciersartikelnummer (RET)
        fallback_vendor_name = last_purch_record.get("CardName", "")  # leveranciersnaam (RET)

        description = img_data.get("OITMI_DESCRIPTION", "") or own_description
        # Volgorde: bestaande OITMI-waarde > "Vendor Nr"/"Leverancier" uit de
        # zoekresultaat-rij (meest specifiek per artikel) > laatste aankoop (RET).
        vendor_id = img_data.get("OITMI_VENDORID", "") or self.vendor_hint_id or fallback_vendor_id
        vendor_name = img_data.get("OITMI_VENDORNAME", "") or self.vendor_hint_name or fallback_vendor_name

        uploader = ImageUploader(
            parent=self,
            item_code=img_data.get("OITMI_ITRMID", self.item_code),
            description=description,
            vendor_id=vendor_id,
            vendor_name=vendor_name,
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
        parent_pos = self.pos()
        offset_x = 2
        offset_y = 2
        new_x = parent_pos.x() + offset_x
        new_y = parent_pos.y() + offset_y
        child_widget.move(new_x, new_y)

    def _on_uploader_closed(self):
        try:
            from stock_info import get_item_detail_stockinfo
            new_data = get_item_detail_stockinfo(self.item_code) or {}
            self.detail_data = new_data
            self._refresh_image_tab()
        except Exception as e:
            QMessageBox.warning(self, "Refresh Fout", f"Kon afbeeldinggegevens niet verversen:\n{e}")

    def _refresh_image_tab(self):
        for idx in range(self.tabs.count()):
            if self.tabs.tabText(idx) == "🖼️ Afbeelding":
                self.tabs.removeTab(idx)
                break
        self._add_image_tab()

    def _add_atp_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        atp_widget = AtpWidget(self.item_code, parent=self)
        layout.addWidget(atp_widget)
        self.tabs.addTab(tab, "⚡ ATP")