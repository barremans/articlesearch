#project_ui.py
import os
from collections import defaultdict
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox, QPushButton,
    QHBoxLayout, QAbstractItemView, QMessageBox, QDialogButtonBox,
    QApplication, QScrollArea, QHeaderView
)
from PySide6.QtCore import Qt, QMimeData

from settings import load_tab_order


class ProjectWindow(QDialog):
    def __init__(self, json_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("📁 Project Info")
        self.setWindowFlags(
            Qt.Window |
                Qt.WindowCloseButtonHint |
                Qt.WindowMinimizeButtonHint |
                Qt.WindowMaximizeButtonHint |
                Qt.WindowStaysOnTopHint  # optioneel
        )
        #self.setFixedSize(1400, 800)
        self.resize(1200, 800)                  # standaard grootte
        self.setMinimumSize(1000, 600)          # minimale afmetingen
        #self.setMaximumSize(1920, 1200)         # optioneel: maximale afmetingen
        self._center_window()
        self.child_windows = []

        css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "detail.qss")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        self.collected_rows = []
        self.collected_vta_rows = []

        layout = QVBoxLayout(self)
        tabs = QTabWidget(self)

        root = json_data[0]
        pr_data = root.get("PR", [{}])[0]
        art_data = pr_data.get("ART", [])
        vta_data = root.get("VTA", [])

        # Info-tab
        info_tab = QWidget()
        form_layout = QFormLayout(info_tab)
        layout.addWidget(info_tab)

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

        # ART-tab
        art_tab = QWidget()
        art_layout = QVBoxLayout(art_tab)
        self.art_table = QTableWidget()
        self.art_table.setColumnCount(8)
        self.art_table.setHorizontalHeaderLabels([
            "", "Relatie", "CardName", "PU_SuppNbr", "Artikel", "Omschrijving", "Aantal", "Prijs"
        ])
        self.art_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.art_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

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
        self.art_count_label = QLabel(f"Aantal rijen: {self.art_table.rowCount()}")
        art_layout.addWidget(self.art_count_label)

        art_btns = QHBoxLayout()
        self.select_all_checkbox = QCheckBox("Selecteer alles")
        self.select_all_checkbox.toggled.connect(self._toggle_all_checkboxes)
        collect_btn = QPushButton("Voeg toe aan lijst")
        collect_btn.clicked.connect(self._collect_selected)
        show_btn = QPushButton("Toon lijst")
        show_btn.clicked.connect(self._show_collected)
        clear_btn = QPushButton("Leeg lijst")
        clear_btn.clicked.connect(self._clear_collected)
        art_btns.addWidget(self.select_all_checkbox)
        art_btns.addWidget(collect_btn)
        art_btns.addWidget(show_btn)
        art_btns.addWidget(clear_btn)
        art_btns.addStretch()
        art_layout.addLayout(art_btns)
        #tabs.addTab(art_tab, "Artikels (ART)")

        # VTA-tab (vereenvoudigde versie)
        vta_tab = QWidget()
        vta_layout = QVBoxLayout(vta_tab)
        self.vta_table = QTableWidget()

        vta_sorted = sorted(vta_data, key=lambda x: x.get("U_U_Certified", "N"), reverse=True)
        self.vta_table.setRowCount(len(vta_sorted))
        self.vta_table.setColumnCount(10)
        self.vta_table.setHorizontalHeaderLabels([
            "", "Artikelnummer", "SupplNbr", "PrefSuppl", "Gecert.", "Omschrijving", "Leverancier", "PurchNbr","MD_SuppNbr", "MD_Suppl"
        ])
       
        # Installations-tab
        installations_tab = QWidget()
        installations_layout = QVBoxLayout(installations_tab)
        installations_table = QTableWidget()

        vta_data_sorted = sorted(vta_data, key=lambda x: x.get("U_U_Certified", "N"), reverse=True)
        installations_table.setRowCount(len(vta_data_sorted))
        installations_table.setColumnCount(14)
        installations_table.setHorizontalHeaderLabels([
            "Art.nr", "Art.omschr.", "Gecertificeerd", "Benodigd", "In mag.", "Bevestigd",
            "Bestel", "Doc.", "Aantal", "Lev.datum", "Picked",
            "Status", "Projectleider", "Locatie"
        ])

        for i, item in enumerate(vta_data_sorted):
            #cb = QCheckBox()
            #cb.setFocusPolicy(Qt.NoFocus)
            #installations_table.setCellWidget(i, 0, cb)
            installations_table.setItem(i, 0, make_cell(item.get("Artikelnummer")))
            installations_table.setItem(i, 1, make_cell(item.get("Artikel-/serviceomschrijving")))
            installations_table.setItem(i, 2, make_cell(item.get("U_U_Certified")))
            installations_table.setItem(i, 3, make_cell(item.get("Benodigd")))
            installations_table.setItem(i, 4, make_cell(item.get("In magazijn")))
            installations_table.setItem(i, 5, make_cell(item.get("Bevestigd")))
            installations_table.setItem(i, 6, make_cell(item.get("In bestelling")))
            
            #installations_table.setItem(i, 7, make_cell(item.get("Besteld op document")))
                # → kolom 7 = "Doc." met data uit "In bestelling" en koppeling naar POR
            doc_text = str(item.get("Besteld op document", ""))  # ← juiste veld!
            cell_item = make_cell(doc_text)
            cell_item.setData(Qt.UserRole, item.get("POR", {}))  # ← koppel POR
            installations_table.setItem(i, 7, cell_item)

            installations_table.setItem(i, 8, make_cell(item.get("Aantal")))
            installations_table.setItem(i, 9, make_cell(item.get("Bevestigde Leverdatum")))
            installations_table.setItem(i, 10, make_cell(item.get("Picked")))
            installations_table.setItem(i, 11, make_cell(item.get("Status")))
            installations_table.setItem(i, 12, make_cell(item.get("Projectleider")))
            installations_table.setItem(i, 13, make_cell(item.get("RealLocation")))
            
        # Koppel dubbelklik aan POR-functie
        self.installations_table = installations_table
        self.installations_table.cellDoubleClicked.connect(self._handle_install_cell_click)            

        installations_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        installations_layout.addWidget(installations_table)
        installations_layout.addWidget(QLabel(f"Aantal rijen: {installations_table.rowCount()}"))
        
        
        # Stel kolombreedte-gedrag in
        header = self.vta_table.horizontalHeader()
        for i in range(self.vta_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)  # standaard: manueel verstelbaar
        header.setSectionResizeMode(5, QHeaderView.Stretch)  # "Omschrijving" wordt dynamisch groter

        # Stel vaste breedtes in voor de andere kolommen
        self.vta_table.setColumnWidth(0, 30)    # Checkbox
        self.vta_table.setColumnWidth(1, 100)   # Artikelnummer
        self.vta_table.setColumnWidth(2, 100)   # SupplNbr
        self.vta_table.setColumnWidth(3, 200)   # PrefSuppl
        self.vta_table.setColumnWidth(4, 80)    # Gecertificeerd
        self.vta_table.setColumnWidth(5, 80)    # Leverancier   
        self.vta_table.setColumnWidth(6, 80)    # PurchNbr               

        # Voeg gegevens toe aan de tabel
        for r, item in enumerate(vta_sorted):
            cb = QCheckBox()
            cb.setFocusPolicy(Qt.NoFocus)
            self.vta_table.setCellWidget(r, 0, cb)
            self.vta_table.setItem(r, 1, make_cell(item.get("Artikelnummer")))
            self.vta_table.setItem(r, 2, make_cell(item.get("SupplNbr")))
            self.vta_table.setItem(r, 3, make_cell(item.get("PrefSuppl")))
            self.vta_table.setItem(r, 4, make_cell(item.get("U_U_Certified", "N")))
            self.vta_table.setItem(r, 5, make_cell(item.get("Artikel-/serviceomschrijving")))
            self.vta_table.setItem(r, 6, make_cell(item.get("Leverancier")))
            por = item.get("POR", {})
            docnum = por.get("DocNum", "")
            cell_item = make_cell(docnum)
            cell_item.setData(Qt.UserRole, por)  # ← sla het POR-object op in de cel
            self.vta_table.setItem(r, 7, cell_item)
            # Voeg SuppCatNum en CardName toe (via item["LART"][0])
            lart = (item.get("LART") or [{}])[0]  # veilig ophalen
            self.vta_table.setItem(r, 8, make_cell(lart.get("SuppCatNum")))
            self.vta_table.setItem(r, 9, make_cell(lart.get("CardName")))
            self.vta_table.setColumnWidth(8, 100)  # SuppCatNum
            self.vta_table.setColumnWidth(9, 150)  # CardName   
            
        self.vta_table.cellClicked.connect(self._handle_vta_cell_click)


        # Voeg tabel en knoppen toe aan layout
        vta_layout.addWidget(self.vta_table)
        self.vta_count_label = QLabel(f"Aantal rijen: {self.vta_table.rowCount()}")
        vta_layout.addWidget(self.vta_count_label)

        vta_btns = QHBoxLayout()
        self.vta_select_all = QCheckBox("Selecteer alles")
        self.vta_select_all.toggled.connect(self._toggle_all_vta_checkboxes)
        vta_collect_btn = QPushButton("Voeg toe aan lijst")
        vta_collect_btn.clicked.connect(self._collect_selected_vta)
        vta_show_btn = QPushButton("Toon lijst")
        vta_show_btn.clicked.connect(self._show_collected_vta)
        vta_clear_btn = QPushButton("Leeg lijst")
        vta_clear_btn.clicked.connect(self._clear_collected_vta)
        vta_btns.addWidget(self.vta_select_all)
        vta_btns.addWidget(vta_collect_btn)
        vta_btns.addWidget(vta_show_btn)
        vta_btns.addWidget(vta_clear_btn)
        vta_btns.addStretch()
        vta_layout.addLayout(vta_btns)
        #tabs.addTab(vta_tab, "PRJ Art.")
        
                # VTA (gecertificeerd)-tab
        vta_cert_tab = QWidget()
        vta_cert_layout = QVBoxLayout(vta_cert_tab)
        vta_cert_table = QTableWidget()

        # Filter: enkel gecertificeerde rijen
        certified_data = [item for item in vta_data if item.get("U_U_Certified", "N") == "Y"]

        vta_cert_table.setRowCount(len(certified_data))
        vta_cert_table.setColumnCount(6)  # je kiest zelf de relevante kolommen

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

        vta_cert_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        vta_cert_layout.addWidget(vta_cert_table)
        vta_cert_layout.addWidget(QLabel(f"Aantal rijen: {vta_cert_table.rowCount()}"))
        #tabs.addTab(vta_cert_tab, "PRJ Art. (cert.)")
        
        
        # Tabs dynamisch toevoegen volgens gewenste volgorde
        tab_map = {
            "art": (art_tab, "Artikels (ART)"),
            "install": (installations_tab, "Installaties"),
            "vta": (vta_tab, "PRJ Art."),
            "vta_cert": (vta_cert_tab, "PRJ Art. (cert.)"),
        }

        for key in load_tab_order():
            if key == "info":
                continue  # Skip 'info' tab
            if key in tab_map:
                tabs.addTab(tab_map[key][0], tab_map[key][1])

                layout.addWidget(tabs)

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
        btn.setMaximumWidth(70)
        btn.clicked.connect(lambda: self._show_full_text_dialog(label, full_text))
        h_layout.addWidget(btn)
        layout.addRow(QLabel(f"{label}:"), container)

    def _show_full_text_dialog(self, title, text):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(600, 400)
        layout = QVBoxLayout(dialog)
        label = QLabel(text)
        label.setWordWrap(True)
        label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        label.setAlignment(Qt.AlignTop)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        sublayout = QVBoxLayout(container)
        sublayout.addWidget(label)
        scroll.setWidget(container)
        layout.addWidget(scroll)
        close_btn = QPushButton("Sluit")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        dialog.exec()

    def _toggle_all_checkboxes(self, checked):
        for row in range(self.art_table.rowCount()):
            cb = self.art_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox):
                cb.setChecked(checked)

    def _toggle_all_vta_checkboxes(self, checked):
        for row in range(self.vta_table.rowCount()):
            cb = self.vta_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox):
                cb.setChecked(checked)

    def _collect_selected(self):
        for row in range(self.art_table.rowCount()):
            cb = self.art_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox) and cb.isChecked():
                values = [self.art_table.item(row, col).text() for col in range(1, self.art_table.columnCount())]
                line = "\t".join(values)
                if line not in self.collected_rows:
                    self.collected_rows.append(line)
        QMessageBox.information(self, "Verzameld", f"{len(self.collected_rows)} rijen in lijst.")

    def _clear_collected(self):
        self.collected_rows.clear()
        self.select_all_checkbox.setChecked(False)
        # Deselecteer individuele checkboxjes
        for row in range(self.art_table.rowCount()):
            cb = self.art_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox):
                cb.setChecked(False)
        QMessageBox.information(self, "Leeg", "Lijst is geleegd.")


    def _show_collected(self):
        if not self.collected_rows:
            QMessageBox.information(self, "Leeg", "Geen rijen verzameld.")
            return
        self._show_list_dialog(self.collected_rows, "Verzamelde ART rijen", self.art_table)

    def _collect_selected_vta(self):
        for row in range(self.vta_table.rowCount()):
            cb = self.vta_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox) and cb.isChecked():
                values = [self.vta_table.item(row, col).text() for col in range(1, self.vta_table.columnCount())]
                line = "\t".join(values)
                if line not in self.collected_vta_rows:
                    self.collected_vta_rows.append(line)
        QMessageBox.information(self, "Verzameld", f"{len(self.collected_vta_rows)} VTA rijen in lijst.")

    def _clear_collected_vta(self):
        self.collected_vta_rows.clear()
        self.vta_select_all.setChecked(False)
        # Deselecteer individuele checkboxjes
        for row in range(self.vta_table.rowCount()):
            cb = self.vta_table.cellWidget(row, 0)
            if isinstance(cb, QCheckBox):
                cb.setChecked(False)
        QMessageBox.information(self, "Leeg", "VTA-lijst is geleegd.")


    def _show_collected_vta(self):
        if not self.collected_vta_rows:
            QMessageBox.information(self, "Leeg", "Geen VTA-rijen verzameld.")
            return
        self._show_list_dialog(self.collected_vta_rows, "Verzamelde VTA rijen", self.vta_table)

    def _show_list_dialog(self, lines, title, source_table):
        dialog = QDialog(self)
        dialog.setWindowTitle(title)
        dialog.resize(900, 400)
        layout = QVBoxLayout(dialog)
        table = QTableWidget()
        columns = len(lines[0].split("\t"))
        headers = [source_table.horizontalHeaderItem(i).text() for i in range(1, source_table.columnCount())]
        table.setColumnCount(columns)
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(lines))
        for r, line in enumerate(lines):
            for c, val in enumerate(line.split("\t")):
                table.setItem(r, c, QTableWidgetItem(val))
        layout.addWidget(table)
        layout.addWidget(QLabel(f"Aantal rijen: {table.rowCount()}"))
        btns = QDialogButtonBox()
        copy_btn = QPushButton("📋 Kopieer")
        close_btn = QPushButton("Sluit")
        copy_btn.clicked.connect(lambda: self._copy_to_clipboard(lines, headers))
        close_btn.clicked.connect(dialog.accept)
        btns.addButton(copy_btn, QDialogButtonBox.ActionRole)
        btns.addButton(close_btn, QDialogButtonBox.RejectRole)
        layout.addWidget(btns)
        dialog.setLayout(layout)
        dialog.exec()

    def _copy_to_clipboard(self, lines, headers):
        md = QMimeData()
        md.setText("\n".join(lines))
        html = ["<table border='1'><tr>"]
        html += [f"<th>{h}</th>" for h in headers]
        html.append("</tr>")
        for row in lines:
            html.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row.split("\t")) + "</tr>")
        html.append("</table>")
        md.setHtml("".join(html))
        QApplication.clipboard().setMimeData(md)
        QMessageBox.information(self, "Klembord", "Gekopieerd naar klembord (tekst + tabel).")

    def _center_window(self):
        frame_geometry = self.frameGeometry()
        screen_center = self.screen().availableGeometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

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
        offset_x = 2
        offset_y = 2
        parent_pos = self.pos()
        new_x = parent_pos.x() + offset_x
        new_y = parent_pos.y() + offset_y
        child_widget.move(new_x, new_y)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
            
    def _handle_vta_cell_click(self, row, column):
        if column != 7:
            return  # Alleen reageren op DocNum kolom
        item = self.vta_table.item(row, column)
        if item is None:
            return
        por = item.data(Qt.UserRole)
        if por:
            self._show_por_dialog(por)
            
    def _handle_install_cell_click(self, row, column):
        if column != 7:
            return
        item = self.installations_table.item(row, column)
        if item is None:
            return
        por = item.data(Qt.UserRole)
        if por:
            self._show_por_dialog(por)
            
            

    def _show_por_dialog(self, por):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"Aankoopdocument {por.get('DocNum')}")
        dlg.resize(1000, 400)
        layout = QVBoxLayout(dlg)

        layout.addWidget(QLabel(
            f"<b>Leverancier:</b> {por.get('CardName')}<br>"
            f"<b>CardCode:</b> {por.get('CardCode')}<br>"
            f"<b>Comments:</b> {por.get('Comments')}<br>"
            f"<b>DocNum:</b> {por.get('DocNum')}"
        ))

        lines = por.get("POR1", [])
        table = QTableWidget()
        table.setRowCount(len(lines))
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels(["Line", "ItemCode", "Omschrijving", "Aantal", "Suppl.Art.", "S/N"])

        for r, line in enumerate(lines):
            def make_item(key):
                val = str(line.get(key, ""))
                item = QTableWidgetItem(val)
                item.setToolTip(val)
                return item

        for r, line in enumerate(lines):
            table.setItem(r, 0, make_item("LineNum"))
            table.setItem(r, 1, make_item("ItemCode"))
            table.setItem(r, 2, make_item("Dscription"))
            table.setItem(r, 3, make_item("Quantity"))
            table.setItem(r, 4, make_item("VendorNum"))
            table.setItem(r, 5, make_item("SerialNum"))


        # Kolomgedrag: 'Omschrijving' flexibel, rest vast
        header = table.horizontalHeader()
        for i in range(table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Interactive)

        # Alleen 'Omschrijving' mee laten schalen
        header.setSectionResizeMode(2, QHeaderView.Stretch)

        # Minimum breedte forceren via initiële waarde
        table.setColumnWidth(2, 300)

        # Vaste breedtes voor andere kolommen
        table.setColumnWidth(0, 50)    # Line
        table.setColumnWidth(1, 100)   # ItemCode
        table.setColumnWidth(3, 70)    # Aantal
        table.setColumnWidth(4, 120)   # Suppl.Art.
        table.setColumnWidth(5, 100)   # S/N

        layout.addWidget(table)

        close_btn = QPushButton("Sluit")
        close_btn.clicked.connect(dlg.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        dlg.exec()
