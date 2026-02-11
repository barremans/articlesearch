# project_ui.py (versie 26/11/2025 - aankooporders groen gemarkeerd)
import os
from collections import defaultdict
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QPushButton,
    QHBoxLayout, QAbstractItemView, QMessageBox, QScrollArea
)
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QColor
from ui_po import PoWidget
from settings import load_tab_order

from ui_detail import DetailWindow
from stock_info import get_item_detail_stockinfo


class ProjectWindow(QDialog):
    def __init__(self, json_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📁 Project Info")
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint |
            Qt.WindowMinimizeButtonHint |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowStaysOnTopHint
        )

        self.resize(1200, 800)
        self.setMinimumSize(1000, 600)
        self._center_window()
        self.child_windows = []

        css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "detail.qss")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        layout = QVBoxLayout(self)
        tabs = QTabWidget(self)
        root = json_data[0]
        pr_data = root.get("PR", [{}])[0]
        art_data = pr_data.get("ART", [])
        vta_data = root.get("VTA", [])

        # ------------------------
        # INFO TAB
        # ------------------------
        info_tab = QWidget()
        form_layout = QFormLayout(info_tab)

        def add_label(name, value):
            form_layout.addRow(QLabel(f"{name}:"), QLabel(str(value) if value else "-"))

        add_label("Projectnummer", root.get("project_number"))
        add_label("Is Closed", root.get("is_closed"))
        add_label("Beschrijving", root.get("description"))
        add_label("Start (actual)", pr_data.get("actual_start"))
        add_label("Einde (actual)", pr_data.get("actual_finish"))
        add_label("Klantreferentie", pr_data.get("customer_reference"))
        self._add_truncated_text(form_layout, "Omschrijving", pr_data.get("long_description"))
        self._add_truncated_text(form_layout, "Intern memo", pr_data.get("internal_memo"))
        add_label("Prijs", pr_data.get("sales_price"))
        add_label("CardCode", pr_data.get("CardCode"))
        add_label("CardName", pr_data.get("CardName"))
        add_label("Offertenummer", pr_data.get("quotation_document_number"))
        layout.addWidget(info_tab)

        # ------------------------
        # ART TAB
        # ------------------------
        art_tab = QWidget()
        art_layout = QVBoxLayout(art_tab)
        self.art_table = QTableWidget()
        self.art_table.setColumnCount(8)
        self.art_table.setHorizontalHeaderLabels([
            "", "Relatie", "CardName", "PU_SuppNbr", "Artikel", "Omschrijving", "Aantal", "Prijs"
        ])
        self.art_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.art_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.art_table.cellDoubleClicked.connect(self._open_item_detail)

        grouped = defaultdict(list)
        for item in art_data:
            grouped[item.get("relation_key")].append(item)
        flat_items = [i for group in grouped.values() for i in group]
        self.art_table.setRowCount(len(flat_items))

        def make_cell(val):
            txt = str(val or "")
            item = QTableWidgetItem(txt)
            item.setToolTip(txt)
            return item

        for row, item in enumerate(flat_items):
            cb = QCheckBox()
            cb.setFocusPolicy(Qt.NoFocus)
            self.art_table.setCellWidget(row, 0, cb)
            self.art_table.setItem(row, 1, make_cell(item.get("relation_key")))
            self.art_table.setItem(row, 2, make_cell(item.get("CardName")))
            self.art_table.setItem(row, 3, make_cell(item.get("SuppCatNum")))
            self.art_table.setItem(row, 4, make_cell(item.get("article_key")))
            self.art_table.setItem(row, 5, make_cell(item.get("description")))
            self.art_table.setItem(row, 6, make_cell(item.get("amount")))
            self.art_table.setItem(row, 7, make_cell(item.get("price")))

        art_layout.addWidget(self.art_table)
        art_layout.addWidget(QLabel(f"Aantal rijen: {self.art_table.rowCount()}"))

        # ------------------------
        # VTA TAB
        # ------------------------
        vta_tab = QWidget()
        vta_layout = QVBoxLayout(vta_tab)
        self.vta_table = QTableWidget()
        self.vta_table.cellDoubleClicked.connect(self._open_po_from_vta)
        self.vta_table.cellDoubleClicked.connect(self._open_item_detail_from_vta)


        #vta_sorted = sorted(vta_data, key=lambda x: x.get("U_U_Certified", "N"), reverse=True)
        # ---- Nieuwe sorteervolgorde: Aankoop (type 12) > In Progress > rest ----
        def sort_key(item):
            por = item.get("POR", {})
            docnum = str(por.get("DocNum", "")).strip()
            is_purchase = (len(docnum) >= 4 and docnum[2:4] == "12")

            # 🔍 Zoek "Status" diep in de structuur
            def find_status(data):
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, (dict, list)):
                            s = find_status(v)
                            if s:
                                return s
                        elif isinstance(v, str) and k.lower() == "status":
                            return v
                elif isinstance(data, list):
                    for v in data:
                        s = find_status(v)
                        if s:
                            return s
                return None

            status = (find_status(item) or "").strip().upper()
            is_in_progress = (status == "IN PROGRESS")

            # Sorteervolgorde: aankoop eerst, dan in progress, dan rest
            return (
                0 if is_purchase else (1 if is_in_progress else 2),
                item.get("Artikelnummer", "")
            )

        vta_sorted = sorted(vta_data, key=sort_key)

        self.vta_table.setRowCount(len(vta_sorted))
        self.vta_table.setColumnCount(9)
        self.vta_table.setHorizontalHeaderLabels([
            "", "Artikelnummer", "VendorNbr", "Gecert.", "Omschrijving", "Leverancier", "PurchNbr", "SupplNbr", "PrefSuppl"
        ])

        for r, item in enumerate(vta_sorted):
            cb = QCheckBox()
            self.vta_table.setCellWidget(r, 0, cb)
            self.vta_table.setItem(r, 1, make_cell(item.get("Artikelnummer")))
            por = item.get("POR", {})
            por1_list = por.get("POR1") or [{}]
            suppl_nbr = por1_list[0].get("VendorNum", "")
            self.vta_table.setItem(r, 2, make_cell(suppl_nbr))
            self.vta_table.setItem(r, 3, make_cell(item.get("U_U_Certified", "N")))
            self.vta_table.setItem(r, 4, make_cell(item.get("Artikel-/serviceomschrijving")))
            self.vta_table.setItem(r, 5, make_cell(item.get("Leverancier")))
            docnum = por.get("DocNum", "")
            cell_item = make_cell(docnum)
            cell_item.setData(Qt.UserRole, por)

            # ✅ Aankooporders (type 12) groen markeren
            if isinstance(docnum, str) and len(docnum) >= 4 and docnum[2:4] == "12":
                cell_item.setBackground(QColor(170, 255, 170))  # zachtgroen

            self.vta_table.setItem(r, 6, cell_item)

            lart = (item.get("LART") or [{}])[0]
            self.vta_table.setItem(r, 7, make_cell(lart.get("SuppCatNum")))
            self.vta_table.setItem(r, 8, make_cell(lart.get("CardName")))

        vta_layout.addWidget(self.vta_table)
        vta_layout.addWidget(QLabel(f"Aantal rijen: {self.vta_table.rowCount()}"))

        # ------------------------
        # VTA (CERT.) TAB
        # ------------------------
        vta_cert_tab = QWidget()
        vta_cert_layout = QVBoxLayout(vta_cert_tab)
        vta_cert_table = QTableWidget()
        certified_data = [item for item in vta_data if item.get("U_U_Certified", "N") == "Y"]
        vta_cert_table.setRowCount(len(certified_data))
        vta_cert_table.setColumnCount(6)
        vta_cert_table.setHorizontalHeaderLabels([
            "Art.nr", "Omschrijving", "Benodigd", "Bevestigd", "Status", "Locatie"
        ])
        for r, item in enumerate(certified_data):
            vta_cert_table.setItem(r, 0, make_cell(item.get("Artikelnummer")))
            vta_cert_table.setItem(r, 1, make_cell(item.get("Artikel-/serviceomschrijving")))
            vta_cert_table.setItem(r, 2, make_cell(item.get("Benodigd")))
            vta_cert_table.setItem(r, 3, make_cell(item.get("Bevestigd")))
            vta_cert_table.setItem(r, 4, make_cell(item.get("Status")))
            vta_cert_table.setItem(r, 5, make_cell(item.get("RealLocation")))
        vta_cert_layout.addWidget(vta_cert_table)
        vta_cert_layout.addWidget(QLabel(f"Aantal rijen: {vta_cert_table.rowCount()}"))

        # ------------------------
        # INSTALLATIES TAB
        # ------------------------
        installations_tab = QWidget()
        installations_layout = QVBoxLayout(installations_tab)
        self.installations_table = QTableWidget()
        self.installations_table.cellDoubleClicked.connect(self._handle_install_cell_click)
        self.installations_table.cellDoubleClicked.connect(self._open_item_detail_from_install)
        installations_layout.addWidget(self.installations_table)

        #vta_sorted2 = sorted(vta_data, key=lambda x: x.get("U_U_Certified", "N"), reverse=True)
        # ---- Zelfde sorteerlogica als VTA-tab ----
        def find_status(data):
            if isinstance(data, dict):
                for k, v in data.items():
                    if isinstance(v, (dict, list)):
                        s = find_status(v)
                        if s:
                            return s
                    elif isinstance(v, str) and k.lower() == "status":
                        return v
            elif isinstance(data, list):
                for v in data:
                    s = find_status(v)
                    if s:
                        return s
            return None

        def install_sort_key(item):
            por = item.get("POR", {})
            docnum = str(por.get("DocNum", "") or item.get("Besteld op document", "")).strip()
            is_purchase = (len(docnum) >= 4 and docnum[2:4] == "12")
            status = (find_status(item) or "").strip().upper()
            is_in_progress = (status == "IN PROGRESS")
            return (
                0 if is_purchase else (1 if is_in_progress else 2),
                item.get("Artikelnummer", "")
            )

        vta_sorted2 = sorted(vta_data, key=install_sort_key)

        self.installations_table.setRowCount(len(vta_sorted2))
        self.installations_table.setColumnCount(14)
        self.installations_table.setHorizontalHeaderLabels([
            "Art.nr", "Art.omschr.", "Gecertificeerd", "Benodigd", "In mag.", "Bevestigd",
            "Bestel", "Doc.", "Aantal", "Lev.datum", "Picked",
            "Status", "Projectleider", "Locatie"
        ])

        for i, item in enumerate(vta_sorted2):
            self.installations_table.setItem(i, 0, make_cell(item.get("Artikelnummer")))
            self.installations_table.setItem(i, 1, make_cell(item.get("Artikel-/serviceomschrijving")))
            self.installations_table.setItem(i, 2, make_cell(item.get("U_U_Certified")))
            self.installations_table.setItem(i, 3, make_cell(item.get("Benodigd")))
            self.installations_table.setItem(i, 4, make_cell(item.get("In magazijn")))
            self.installations_table.setItem(i, 5, make_cell(item.get("Bevestigd")))
            self.installations_table.setItem(i, 6, make_cell(item.get("In bestelling")))
            doc_text = str(item.get("Besteld op document", ""))
            cell_item = make_cell(doc_text)
            cell_item.setData(Qt.UserRole, item.get("POR", {}))

            # ✅ Groen markeren voor aankooporder
            if isinstance(doc_text, str) and len(doc_text) >= 4 and doc_text[2:4] == "12":
                cell_item.setBackground(QColor(170, 255, 170))

            self.installations_table.setItem(i, 7, cell_item)
            self.installations_table.setItem(i, 8, make_cell(item.get("Aantal")))
            self.installations_table.setItem(i, 9, make_cell(item.get("Bevestigde Leverdatum")))
            self.installations_table.setItem(i, 10, make_cell(item.get("Picked")))
           # self.installations_table.setItem(i, 11, make_cell(item.get("Status")))
                # ---- ✅ Status met rood accent voor actieve staten ----
            status_text = str(item.get("Status", "")).strip()
            cell_status = make_cell(status_text)
            if status_text.upper() in {"OPEN", "IN PROGRESS"}:
                cell_status.setBackground(QColor(255, 180, 180))
                cell_status.setForeground(QColor(120, 0, 0))
            self.installations_table.setItem(i, 11, cell_status)
            self.installations_table.setItem(i, 12, make_cell(item.get("Projectleider")))
            self.installations_table.setItem(i, 13, make_cell(item.get("RealLocation")))

        installations_layout.addWidget(QLabel(f"Aantal rijen: {self.installations_table.rowCount()}"))

        # ------------------------
        # TAB ORDER
        # ------------------------
        tab_map = {
            "vta": (vta_tab, "PRJ Art."),
            "install": (installations_tab, "Installaties"),
            "vta_cert": (vta_cert_tab, "PRJ Art. (cert.)"),
            "art": (art_tab, "Artikels (ART)"),
        }

        for key in load_tab_order():
            if key in tab_map:
                tabs.addTab(tab_map[key][0], tab_map[key][1])
        layout.addWidget(tabs)

    # ------------------------
    # NIEUWE LOGICA
    # ------------------------
    def _open_document_window(self, doc_number: str):
        """Opent correct venster op basis van documenttype (12 = PO, 25 = VTA)."""
        if not doc_number or len(doc_number) < 4:
            return
        doc_type = doc_number[2:4]
        try:
            if doc_type == "12":
                widget = PoWidget()
            elif doc_type == "25":
                from ui_vta import PoWidget as VtaWidget
                widget = VtaWidget()
            else:
                QMessageBox.information(self, "Onbekend", f"Documenttype {doc_type} niet herkend.")
                return

            widget.setWindowFlags(widget.windowFlags() | Qt.WindowStaysOnTopHint)
            widget.show()
            widget.raise_()
            widget.activateWindow()
            widget.po_input.setText(doc_number)
            widget.load_data()
            self.child_windows.append(widget)

        except Exception as e:
            QMessageBox.critical(self, "Fout", str(e))

    def _open_po_from_vta(self, row, column):
        if column != 6:
            return
        item = self.vta_table.item(row, column)
        if not item:
            return
        doc_number = item.text().strip()
        self._open_document_window(doc_number)

    def _handle_install_cell_click(self, row, column):
        if column != 7:
            return
        item = self.installations_table.item(row, column)
        if not item:
            return
        doc_number = item.text().strip()
        self._open_document_window(doc_number)

    # ------------------------
    # HULPFUNCTIES
    # ------------------------
    def _add_truncated_text(self, layout, label, full_text, max_length=50):
        full_text = str(full_text or "")
        if len(full_text) <= max_length:
            layout.addRow(QLabel(f"{label}:"), QLabel(full_text))
            return
        truncated = full_text[:max_length].rstrip() + "..."
        container = QWidget()
        h_layout = QHBoxLayout(container)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(5)
        h_layout.addWidget(QLabel(truncated))
        btn = QPushButton("Meer...")
        btn.clicked.connect(lambda: self._show_full_text_dialog(label, full_text))
        h_layout.addWidget(btn)
        layout.addRow(QLabel(f"{label}:"), container)

    def _show_full_text_dialog(self, title, text):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        layout = QVBoxLayout(dlg)
        label = QLabel(text)
        label.setWordWrap(True)
        layout.addWidget(label)
        close_btn = QPushButton("Sluit")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn)
        dlg.exec()

    def _center_window(self):
        frame_geometry = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def _open_item_detail(self, row, column):
        """Opent ui_detail venster bij dubbelklik op ItemCode (kolom 4)."""
        if column != 4:
            return

        item = self.art_table.item(row, column)
        if not item:
            return

        item_code = item.text().strip()
        if not item_code:
            QMessageBox.information(self, "Geen artikel", "Geen geldig artikelnummer geselecteerd.")
            return

        try:
            # 🔹 Ophalen van detailinformatie
            detail_data = get_item_detail_stockinfo(item_code)
            detail_window = DetailWindow(parent=self, item_code=item_code, detail_data=detail_data or {})
            detail_window.show()
            detail_window.raise_()
            detail_window.activateWindow()
            self.child_windows.append(detail_window)

        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Kon artikelgegevens niet openen:\n{e}")

    def _open_item_detail_from_install(self, row, column):
        """Opent ui_detail venster bij dubbelklik op Art.nr (kolom 0) in Installaties-tab."""
        if column != 0:
            return

        item = self.installations_table.item(row, column)
        if not item:
            return

        item_code = item.text().strip()
        if not item_code:
            QMessageBox.information(self, "Geen artikel", "Geen geldig artikelnummer geselecteerd.")
            return

        try:
            detail_data = get_item_detail_stockinfo(item_code)
            detail_window = DetailWindow(parent=self, item_code=item_code, detail_data=detail_data or {})
            detail_window.show()
            detail_window.raise_()
            detail_window.activateWindow()
            self.child_windows.append(detail_window)
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Kon artikelgegevens niet openen:\n{e}")

    def _open_item_detail_from_vta(self, row, column):
        """Opent ui_detail venster bij dubbelklik op Artikelnummer (kolom 1) in PRJ Art.-tab."""
        if column != 1:
            return

        item = self.vta_table.item(row, column)
        if not item:
            return

        item_code = item.text().strip()
        if not item_code:
            QMessageBox.information(self, "Geen artikel", "Geen geldig artikelnummer geselecteerd.")
            return

        try:
            detail_data = get_item_detail_stockinfo(item_code)
            detail_window = DetailWindow(parent=self, item_code=item_code, detail_data=detail_data or {})
            detail_window.show()
            detail_window.raise_()
            detail_window.activateWindow()
            self.child_windows.append(detail_window)
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Kon artikelgegevens niet openen:\n{e}")
