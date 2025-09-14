# ui_main.py
import os
import sys
import json  # <-- toegevoegd
import logging
import markdown

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QStatusBar, QMenu, QApplication,
    QHeaderView, QInputDialog, QCheckBox, QTextBrowser, QSizePolicy,
    QAbstractItemView, QTextEdit, QFileDialog,
    QGridLayout, QSpacerItem
)
from PySide6.QtGui import QShortcut, QKeySequence, QMovie, QIcon
from PySide6.QtCore import QEvent, Qt, QPoint, QTimer, QFileSystemWatcher, QMimeData

from data_request import send_data_request
from ui_detail import DetailWindow
from stock_info import get_item_detail_stockinfo
from settings import (
    load_environment, save_environment,
    load_show_stock, save_show_stock,
    load_detail_modal, save_detail_modal,
    load_main_qss_path, load_detail_qss_path, load_upload_qss_path,
    load_default_search_type, save_default_search_type,
    load_language,
    load_bp_default_type, save_bp_default_type  # <-- NIEUW
)
from label.label_generator import generate_label
from label.label_settings_dialog import LabelSettingsDialog
from version import __version__
from updater import check_for_update, download_latest_release
from bug_report_dialog import BugDialog
from github_cases import show_github_cases
from file_editor_dialog import FileEditorDialog
from help_dialogs import show_help_dialog
from settings_dialog import show_settings_dialog

from translations import get_labels

# JSON-viewer voor project/BP (Project gebruikt dit venster)
from project_ui import ProjectWindow

from settings import load_column_headers_s, load_column_headers_default

# ---- NIEUW: BP detailvenster
from ui_bp import BpWindow
# ---- NIEUW: Export/Elements venster
from ui_docs import DocsWindow  # <-- toegevoegd

# Dynamische kolomheaders laden uit settings
COLUMN_HEADERS_S = load_column_headers_s()
COLUMN_HEADERS_DEFAULT = load_column_headers_default()

# Logging voor UI
logger = logging.getLogger("ArticleSearch.UI")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - [ArticleSearch.UI] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        labels = get_labels(load_language())
        
        self.collected_data = []
        self.detail_windows = []
        self.upload_windows = []
        self.project_window = None
        self.bp_windows = []   # <-- BP vensters bijhouden
        self.docs_windows = [] # <-- NIEUW: Docs/Elements vensters bijhouden
        self.setStatusBar(QStatusBar(self))

        QTimer.singleShot(1000, lambda: check_for_update(__version__, self))
        self.update_btn = QPushButton(labels["buttons"]["update_now"])
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(lambda: download_latest_release(self))

        self.setWindowTitle("Artikelzoeker")
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "stocks.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1400, 800)

        css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "style.qss")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        base_css = os.path.join(os.path.dirname(__file__), "assets", "css")
        self._style_qss  = os.path.join(base_css, "style.qss")
        self._detail_qss = os.path.join(base_css, "detail.qss")
        self._upload_qss = os.path.join(base_css, "upload.qss")

        self._qss_watcher = QFileSystemWatcher(self)
        for path in (self._style_qss, self._detail_qss, self._upload_qss):
            if os.path.exists(path):
                self._qss_watcher.addPath(path)
        self._qss_watcher.fileChanged.connect(self._on_qss_file_changed)

        self._center_window()
        self._create_menu_bar()
        self._create_main_layout()

        if load_environment() == "test":
            self.setStyleSheet(self.styleSheet() + "QMainWindow { background-color: #ffeeee; }")

        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.perform_search)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._generate_label)
        QShortcut(QKeySequence("F1"), self).activated.connect(lambda: show_help_dialog(self))
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self._open_selected_row)

        self.installEventFilter(self)
        self.input_field.installEventFilter(self)

    # ---------------- UI OPBOUW ----------------

    def _enable_update_button(self, is_update_available: bool):
        if hasattr(self, 'update_btn') and self.update_btn:
            self.update_btn.setEnabled(is_update_available)

    def _create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Bestand")
        file_menu.addAction("A&fsluiten").triggered.connect(self.close)

        settings_menu = menubar.addMenu("&Instellingen")
        settings_menu.addAction("⚙️ &Kies omgeving (test/live)").triggered.connect(self._choose_environment)
        settings_menu.addAction("🛠️ &Instellingen wijzigen...").triggered.connect(lambda: show_settings_dialog(self))
        settings_menu.addAction("🏷️ &Label-instellingen...").triggered.connect(self._show_label_settings_dialog)
        settings_menu.addSeparator()
        settings_menu.addAction("✏️ Bewerk style.qss").triggered.connect(self._open_style_qss_editor)
        settings_menu.addAction("✏️ Bewerk detail.qss").triggered.connect(self._open_detail_qss_editor)
        settings_menu.addAction("✏️ Bewerk upload.qss").triggered.connect(self._open_upload_qss_editor)

        # ---- NIEUW: Export-menu
        export_menu = menubar.addMenu("&Export")
        export_menu.addAction("Open &Elements").triggered.connect(self._open_docs_window)

        report_menu = menubar.addMenu("&Rapporteren")
        report_menu.addAction("🐞 &Bug of feature melden...").triggered.connect(self._show_bug_report_dialog)
        report_menu.addSeparator()
        report_menu.addAction("Show open cases").triggered.connect(lambda: show_github_cases(self))

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&Help").triggered.connect(lambda: show_help_dialog(self))
        settings_menu.addSeparator()
        help_menu.addAction("&Over...").triggered.connect(self._show_about_dialog)
        help_menu.addAction("📄 &Changelog...").triggered.connect(self._show_changelog_dialog)

    def _create_main_layout(self):
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(
            "Geef zoekterm in… geen prefix = zoeken op art.nr., * omschrijving, - kernwoorden, / leverancier"
        )

        self.search_type_select = QComboBox()
        self.search_type_select.addItems(["Standaard", "Project", "BP"])
        self.search_type_select.setCurrentText(load_default_search_type())
        self.search_type_select.currentTextChanged.connect(self._toggle_fields_by_search_type)
        self.search_type_select.currentTextChanged.connect(self._update_input_tooltip)

        self.mode_label = QLabel("Zoekmodus:")
        self.mode_select = QComboBox()
        self.mode_select.addItems(["AND", "OR"])

        # We hergebruiken deze rij:
        # - Standaard: label = "Toon voorraad:", items = ["R","S","B"]
        # - BP      : label = "Type:", items = ["", "C", "S"]
        self.stock_label = QLabel("Toon voorraad:")
        self.show_stock_select = QComboBox()
        # INIT: stock-items + huidige setting
        self._set_combo_items(self.show_stock_select, ["R", "S", "B"], current=load_show_stock())
        # Routeer opslag via centrale handler (afhankelijk van actieve modus)
        self.show_stock_select.currentTextChanged.connect(self._handle_secondary_combo_change)

        self.search_button = QPushButton("Zoeken")
        self.search_button.clicked.connect(self.perform_search)

        self.table = QTableWidget()
        self.table.itemDoubleClicked.connect(self.handle_row_double_click)
        self.collect_button  = QPushButton("Voeg toe aan lijst")
        self.clear_collected_button = QPushButton("Leeg lijst")
        self.show_list_button = QPushButton("Toon lijst")
        self.select_all_checkbox = QCheckBox("Selecteer alles")

        self.collect_button.clicked.connect(self.collect_selected_rows)
        self.clear_collected_button.clicked.connect(self.clear_collected_list)
        self.show_list_button.clicked.connect(self.show_collected_dialog)
        self.select_all_checkbox.toggled.connect(self._toggle_select_all)

        self.result_count_label = QLabel("Aantal resultaten: 0")

        self.loading_spinner = QLabel()
        spinner_path = os.path.join(os.path.dirname(__file__), "assets", "spinner.gif")
        self.loading_movie = QMovie(spinner_path)
        self.loading_spinner.setMovie(self.loading_movie)
        self.loading_spinner.setAlignment(Qt.AlignCenter)
        self.loading_spinner.hide()

        layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)

        zoekterm_label = QLabel("Zoekterm:")
        search_type_label = QLabel("Search-type:")

        grid.addWidget(self.input_field, 0, 1, 1, 2)
        grid.addWidget(zoekterm_label,     0, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.input_field,   0, 1, 1, 2)

        grid.addWidget(search_type_label,  1, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.search_type_select, 1, 1)

        grid.addWidget(self.mode_label,    2, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.mode_select,   2, 1)

        grid.addWidget(self.stock_label,   3, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.show_stock_select, 3, 1)
        
        self._update_input_tooltip(self.search_type_select.currentText())
        self._toggle_fields_by_search_type(self.search_type_select.currentText())

        layout.addLayout(grid)
        layout.addWidget(self.search_button, alignment=Qt.AlignHCenter)
        layout.addWidget(QLabel("Resultaten:"))
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.collect_button)
        btn_layout.addWidget(self.clear_collected_button)
        btn_layout.addWidget(self.show_list_button)
        btn_layout.addWidget(self.select_all_checkbox)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        layout.addWidget(self.result_count_label)
        layout.addWidget(self.loading_spinner)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # --------------- ZOEKACTIE & TABELLEN ----------------

    def perform_search(self):
        zoekterm   = self.input_field.text().strip()
        mode       = self.mode_select.currentText()
        searchtype = self.search_type_select.currentText()

        self.result_count_label.setText("Aantal resultaten: 0")
        if not zoekterm:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        # start spinner
        self.loading_spinner.show()
        self.loading_movie.start()
        QApplication.processEvents()

        is_project = (searchtype == "Project")
        is_bp      = (searchtype == "BP")
        request_kind = "project" if is_project else ("bp" if is_bp else "data")

        # Voor BP gebruiken we dezelfde combobox voor Type
        bp_type = self.show_stock_select.currentText() if is_bp else ""

        logger.info(f"Zoekactie: type={searchtype} | kind={request_kind} | term='{zoekterm}' | mode='{mode}' | bp_type='{bp_type}'")

        try:
            data = send_data_request(
                zoekterm,
                mode,
                project_search=is_project,
                is_closed="",
                kind=request_kind,
                bp_type=bp_type
            )
        except Exception as e:
            err_msg = str(e)
            # Fout zichtbaar in tabel
            self.table.clearSelection()
            self.table.setRowCount(0)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Fout"])
            self.table.insertRow(0)
            self.table.setItem(0, 0, QTableWidgetItem(err_msg))
            self.loading_movie.stop()
            self.loading_spinner.hide()
            return

        # Render
        if is_project:
            if isinstance(data, dict) and "error" in data:
                QMessageBox.warning(self, "Projectzoeking mislukt", f"❌ {data['error']}")
            elif isinstance(data, list):
                try:
                    self.project_window = ProjectWindow(data, parent=self)
                    self.project_window.show()
                    self.detail_windows.append(self.project_window)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Fout bij tonen projectgegevens",
                        f"❌ Ongeldige projectdata of formaat:\n{e}"
                    )
            else:
                QMessageBox.warning(self, "Geen data", "❌ Geen geldige projectresultaten ontvangen.")
        elif is_bp:
            self.populate_bp_table(data)
        else:
            self.populate_table(data)

        # stop spinner
        self.loading_movie.stop()
        self.loading_spinner.hide()

    def populate_table(self, data: list):
        """Standaard artikelweergave met dynamische kolomdefinities uit settings."""
        show_stock = load_show_stock()

        if show_stock == "S":
            originele_columns = list(COLUMN_HEADERS_S.keys())
            header_labels = ["Selectie"] + list(COLUMN_HEADERS_S.values())
        else:
            originele_columns = list(COLUMN_HEADERS_DEFAULT.keys())
            header_labels = ["Selectie"] + list(COLUMN_HEADERS_DEFAULT.values())

        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(header_labels))
        self.table.setHorizontalHeaderLabels(header_labels)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for idx in range(1, len(header_labels)):
            mode = QHeaderView.Stretch if idx == 2 else QHeaderView.ResizeToContents
            header.setSectionResizeMode(idx, mode)

        for row, item in enumerate(data):
            checkbox = QCheckBox()
            checkbox.setFocusPolicy(Qt.NoFocus)
            self.table.setCellWidget(row, 0, checkbox)
            for col_offset, key in enumerate(originele_columns, start=1):
                val = item.get(key, "")
                val = f"{val:.2f}" if isinstance(val, float) else str(val or "")
                cell = QTableWidgetItem(val)
                cell.setToolTip(val)
                self.table.setItem(row, col_offset, cell)

        self.result_count_label.setText(f"Aantal resultaten: {len(data)}")
        if data:
            self.table.selectRow(0)

    def populate_bp_table(self, data: list):
        """BP-weergave: alleen CardCode, CardName, FederalTaxID, ContactPerson."""
        header_labels = ["Selectie", "CardCode", "CardName", "FederalTaxID", "ContactPerson"]

        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(header_labels))
        self.table.setHorizontalHeaderLabels(header_labels)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for idx in range(1, len(header_labels)):
            mode = QHeaderView.Stretch if header_labels[idx] == "CardName" else QHeaderView.ResizeToContents
            header.setSectionResizeMode(idx, mode)

        def extract_contact_person(item: dict) -> str:
            cp = item.get("ContactPerson") or item.get("Contactperson")
            if cp:
                return str(cp)
            emps = item.get("ContactEmployees") or []
            if isinstance(emps, list) and emps:
                for ce in emps:
                    if (ce.get("Active") == "Y") and ce.get("Name"):
                        return str(ce["Name"])
                if emps[0].get("Name"):
                    return str(emps[0]["Name"])
            return ""

        for row, item in enumerate(data):
            checkbox = QCheckBox()
            checkbox.setFocusPolicy(Qt.NoFocus)
            self.table.setCellWidget(row, 0, checkbox)

            card_code  = str(item.get("CardCode", "") or "")
            card_name  = str(item.get("CardName", "") or "")
            federal_id = str(item.get("FederalTaxID") or item.get("FedralTaxID") or "")
            contact    = extract_contact_person(item)

            values = [card_code, card_name, federal_id, contact]
            for col_offset, val in enumerate(values, start=1):
                cell = QTableWidgetItem(val)
                cell.setToolTip(val)
                self.table.setItem(row, col_offset, cell)

        self.result_count_label.setText(f"Aantal resultaten: {len(data)}")
        if data:
            self.table.selectRow(0)

    # --------------- VERZAMEL / DIALOGEN ----------------

    def collect_selected_rows(self):
        aantal_rijen = self.table.rowCount()
        if aantal_rijen == 0:
            QMessageBox.information(self, "Geen data", "Er staan geen rijen om te verzamelen.")
            return

        iets_aangevinkt = False

        for row in range(aantal_rijen):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                iets_aangevinkt = True

                row_values = []
                for col in range(1, self.table.columnCount()):
                    item = self.table.item(row, col)
                    text = item.text() if item is not None else ""
                    row_values.append(text)

                joined = "\t".join(row_values)
                if joined not in self.collected_data:
                    self.collected_data.append(joined)

        if not iets_aangevinkt:
            QMessageBox.information(self, "Niets aangevinkt", "Vink eerst één of meerdere vakjes aan om toe te voegen.")
            return

        self.show_collected_dialog()

    def show_collected_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Verzamelde rijen")
        dialog.resize(800, 400)

        if self.search_type_select.currentText() == "BP":
            headers = ["CardCode", "CardName", "FederalTaxID", "ContactPerson"]
        else:
            show_stock = load_show_stock()
            headers = list(COLUMN_HEADERS_S.values()) if show_stock == "S" else list(COLUMN_HEADERS_DEFAULT.values())

        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(self.collected_data))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for r, line in enumerate(self.collected_data):
            parts = line.split("\t")
            for c, txt in enumerate(parts):
                table.setItem(r, c, QTableWidgetItem(txt))

        layout = QVBoxLayout(dialog)
        layout.addWidget(table)

        def copy_selection_to_clipboard():
            md = QMimeData()
            sel_rows = [idx.row() for idx in table.selectionModel().selectedRows()]
            if not sel_rows:
                sel_rows = list(range(table.rowCount()))

            tsv_lines = ["\t".join(headers)]
            for r in sel_rows:
                tsv_lines.append("\t".join(table.item(r, c).text() for c in range(table.columnCount())))
            md.setText("\n".join(tsv_lines))

            html = [
                "<html><head><meta charset='utf-8'></head><body>",
                "<table border='1' cellspacing='0' cellpadding='4' "
                "style='border-collapse:collapse; font-family:Arial,sans-serif; font-size:10pt;'>",
                "<thead><tr>"
            ]
            html += [
                f"<th style='background-color:#f0f0f0; border:1px solid #000; padding:4px;'>{h}</th>"
                for h in headers
            ]
            html.append("</tr></thead><tbody>")
            for r in sel_rows:
                html.append("<tr>")
                for c in range(table.columnCount()):
                    val = table.item(r, c).text()
                    html.append(f"<td style='border:1px solid #000; padding:4px;'>{val}</td>")
                html.append("</tr>")
            html.append("</tbody></table></body></html>")

            md.setHtml("".join(html))
            QApplication.clipboard().setMimeData(md)
            QMessageBox.information(dialog, "Klembord", "Gekopieerd als tabel (Outlook & Word compatibel).")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        copy_btn = QPushButton("Alles kopiëren")
        copy_btn.clicked.connect(copy_selection_to_clipboard)
        close_btn = QPushButton("Sluiten")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dialog.exec()

    def clear_collected_list(self):
        if not self.collected_data:
            QMessageBox.information(self, "Lijst is al leeg", "Er staan momenteel geen rijen in de lijst.")
            return

        self.collected_data.clear()

        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.blockSignals(True)
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.blockSignals(False)

        QMessageBox.information(self, "Lijst geleegd", "De verzamelde rijen zijn nu verwijderd en alle vakjes zijn uitgevinkt.")

    # --------------- DETAIL / CONTEXTMENU / LABEL ----------------

    def handle_row_double_click(self, item):
        search_type = self.search_type_select.currentText()

        # Nieuw: BP dubbelklik opent ui_bp en zoekt op CardCode
        if search_type == "BP":
            row = item.row()
            # In populate_bp_table is de kolomvolgorde:
            # ["Selectie", "CardCode", "CardName", "FederalTaxID", "ContactPerson"]
            card_code_item = self.table.item(row, 1)  # kolom 1 = CardCode
            card_code = card_code_item.text() if card_code_item else ""
            if not card_code:
                QMessageBox.information(self, "Info", "Geen geldige CardCode gevonden op deze rij.")
                return

            bpw = BpWindow()
            bpw.showMaximized()
            bpw.preset_and_fetch(card_code, auto_fetch=True)

            self.bp_windows.append(bpw)
            return

        # Bestaande flow voor niet-BP (artikels / detail)
        row = item.row()
        # Kolom 1 bevat ItemCode (kolom 0 is checkbox)
        item_code = self.table.item(row, 1).text()
        self.table.clearSelection()
        try:
            raw_detail = get_item_detail_stockinfo(item_code)

            # --- Belangrijk: normaliseer elk type naar dict ---
            detail_data = self._normalize_detail_payload(raw_detail)

            logger.info(
                "Detail payload type=%s keys=%s",
                type(raw_detail).__name__,
                list(detail_data.keys())[:10] if isinstance(detail_data, dict) else "n/a",
            )

            dialog = DetailWindow(parent=self, item_code=item_code, detail_data=detail_data or {})
            dialog.show()
            self._reposition_detail(dialog)
            self.detail_windows.append(dialog)

        except Exception as e:
            QMessageBox.warning(self, "Detail Fout", f"Kon detail niet openen:\n{e}\n(type: {type(e).__name__})")

    def _open_selected_row(self):
        search_type = self.search_type_select.currentText()
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Geen selectie", "Selecteer een rij om te openen.")
            return
        first_index = selected_items[0].row()

        if search_type == "BP":
            card_code_item = self.table.item(first_index, 1)  # kolom 1 = CardCode
            card_code = card_code_item.text() if card_code_item else ""
            if not card_code:
                QMessageBox.information(self, "Info", "Geen geldige CardCode gevonden op deze rij.")
                return

            bpw = BpWindow()
            bpw.showMaximized()
            bpw.preset_and_fetch(card_code, auto_fetch=True)
            self.bp_windows.append(bpw)
            return

        # Niet-BP: bestaande artikel-detail flow
        self.handle_row_double_click(self.table.item(first_index, 1))

    def show_table_context_menu(self, position: QPoint):
        index = self.table.indexAt(position)
        if not index.isValid():
            return
        row = index.row()
        menu = QMenu(self)
        copy_action = menu.addAction("📋 Kopieer rij")

        if self.search_type_select.currentText() != "BP":
            detail_action = menu.addAction("🔍 Toon detail")
            label_action = menu.addAction("🏷️ Genereer label")
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        if action == copy_action:
            values = [self.table.item(row, col).text() for col in range(1, self.table.columnCount())]
            QApplication.clipboard().setText("\t".join(values))
        elif self.search_type_select.currentText() != "BP":
            if action and action.text().startswith("🔍"):
                self.handle_row_double_click(self.table.item(row, 1))
            elif action and action.text().startswith("🏷️"):
                self._generate_label()

    def _generate_label(self):
        if self.search_type_select.currentText() == "BP":
            QMessageBox.information(self, "Info", "Label genereren is enkel voor artikels.")
            return

        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Geen selectie", "Selecteer een rij om een label te genereren.")
            return
        row = selected[0].row()
        code = self.table.item(row, 1).text()
        desc = self.table.item(row, 2).text()
        supplier = self.table.item(row, 3).text() if self.table.columnCount() > 3 else "-"
        generate_label(code, desc, supplier, "00000000")

    # --------------- DIVERSE HELPERS / DIALOGEN ----------------

    def _show_label_settings_dialog(self):
        dialog = LabelSettingsDialog(self)
        dialog.exec()

    def _clear_search(self):
        self.input_field.clear()
        self.input_field.setFocus()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.result_count_label.setText("Aantal resultaten: 0")

    def eventFilter(self, obj, event):
        if event.type() != QEvent.KeyPress:
            return super().eventFilter(obj, event)
        if event.key() == Qt.Key_Delete:
            self._clear_search()
            return True
        return super().eventFilter(obj, event)

    def _center_window(self):
        frame = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def _choose_environment(self):
        current = load_environment()
        options = ["live", "test"]
        selected, ok = QInputDialog.getItem(
            self, "Omgeving kiezen", "Selecteer omgeving:", options, options.index(current), False
        )
        if ok and selected != current:
            save_environment(selected)
            QMessageBox.information(self, "Herstart vereist", f"Omgeving gewijzigd naar '{selected}'. Gelieve te herstarten.")

    # OVERRIDES zodat DetailWindows mee verplaatsen
    def moveEvent(self, event):
        super().moveEvent(event)
        for dlg in self.detail_windows:
            if dlg.isVisible():
                self._reposition_detail(dlg)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for dlg in self.detail_windows:
            if dlg.isVisible():
                self._reposition_detail(dlg)

    def _reposition_detail(self, dlg):
        hoofd_pos = self.pos()
        offset_x = 50
        offset_y = 50
        nieuwe_x = hoofd_pos.x() + offset_x
        nieuwe_y = hoofd_pos.y() + offset_y
        dlg.move(nieuwe_x, nieuwe_y)

    # Editors
    def _open_style_qss_editor(self):
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "style.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_detail_qss_editor(self):
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "detail.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_upload_qss_editor(self):
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "upload.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_ui_main_py_editor(self):
        path = os.path.join(os.path.dirname(__file__), "ui_main.py")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_ui_detail_py_editor(self):
        path = os.path.join(os.path.dirname(__file__), "ui_detail.py")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_ui_upload_py_editor(self):
        path = os.path.join(os.path.dirname(__file__), "ui_upload.py")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    # QSS live-reload
    def _on_qss_file_changed(self, path: str):
        """Herlaadt het gewijzigde .qss-bestand en past het toe."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                qss = read_qss = f.read()
        except Exception:
            QTimer.singleShot(500, lambda: self._retry_reload(path))
            return

        if path == self._style_qss:
            self.setStyleSheet(qss)
        elif path == self._detail_qss:
            for dlg in self.detail_windows:
                dlg.setStyleSheet(qss)
        elif path == self._upload_qss:
            for uw in self.upload_windows:
                uw.setStyleSheet(qss)

    def _retry_reload(self, path: str):
        """Herkent na korte vertraging of het bestand dan wél bestaat."""
        if os.path.exists(path):
            self._on_qss_file_changed(path)

    # Changelog & Help & About
    def _show_changelog_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Changelog")
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)
        changelog_view = QTextBrowser()
        changelog_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if getattr(sys, "frozen", False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(__file__)

        changelog_file = os.path.join(base_dir, "docs", "changelog.md")
        try:
            with open(changelog_file, "r", encoding="utf-8") as f:
                html = markdown.markdown(f.read())
                changelog_view.setHtml(html)
        except Exception as e:
            changelog_view.setPlainText(f"Fout bij laden changelog.md:\n{e}")

        layout.addWidget(changelog_view)
        dialog.setLayout(layout)
        dialog.exec()

    def _show_help_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Help")
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)

        help_view = QTextBrowser()
        help_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        if getattr(sys, "frozen", False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(__file__)

        badges_folder = os.path.join(base_dir, "assets", "badges")
        help_view.setSearchPaths([badges_folder])

        help_file = os.path.join(base_dir, "docs", "help.md")
        try:
            with open(help_file, "r", encoding="utf-8") as f:
                html = markdown.markdown(f.read())
                help_view.setHtml(html)
        except Exception as e:
            help_view.setPlainText(f"Fout bij laden help.md:\n{e}")

        layout.addWidget(help_view, 1)

        version_label = QLabel(f"Versie: {__version__}")
        version_label.setAlignment(Qt.AlignRight)
        layout.addWidget(version_label)

        dialog.setLayout(layout)
        dialog.exec()

    def _show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Over Artikelzoeker")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Artikelzoeker – zoektool voor artikels"))
        version_label = QLabel(f"Versie: {__version__}")
        version_label.setStyleSheet("color: gray;")
        layout.addWidget(version_label)

        self.update_btn = QPushButton("Update nu")
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(lambda: download_latest_release(dialog))
        layout.addWidget(self.update_btn)

        check_for_update(__version__, dialog, lambda ok: self.update_btn.setEnabled(ok))

        dialog.setLayout(layout)
        dialog.exec()

    def _show_bug_report_dialog(self):
        dialog = BugDialog(self)
        dialog.exec()

    def _toggle_select_all(self, checked: bool):
        """Vink alle checkboxes in kolom 0 aan of uit."""
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(checked)

    def _update_input_tooltip(self, search_type: str):
        if search_type == "Project":
            tip = "Typ projectnummer"
        elif search_type == "BP":
            tip = "Typ BP-nummer of naam"
        else:
            tip = "Geef zoekterm in… geen prefix = zoeken op art.nr., * omschrijving, - kernwoorden, / leverancier"
        self.input_field.setToolTip(tip)
        self.input_field.setPlaceholderText(tip)

    def _set_combo_items(self, combo: QComboBox, items, current=None):
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        if current is not None and current in items:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    # NIEUW: centrale opslag van de "tweede" combobox
    def _handle_secondary_combo_change(self, value: str):
        if self.search_type_select.currentText() == "BP":
            # Opslaan als BP default type
            save_bp_default_type(value if value in ("", "C", "S") else "")
        else:
            # Opslaan als show_stock (alleen R/S/B)
            if value in ("R", "S", "B"):
                save_show_stock(value)

    def _toggle_fields_by_search_type(self, search_type: str):
        """
        - Standaard:     Zoekmodus zichtbaar, label='Toon voorraad:', items R/S/B
        - BP:            Zoekmodus zichtbaar, label='Type:', items "", C, S
        - Project:       Beide verbergen
        """
        is_project = (search_type == "Project")
        is_bp      = (search_type == "BP")

        # Zoekmodus
        self.mode_label.setVisible(not is_project)   # zichtbaar voor Standaard & BP
        self.mode_select.setVisible(not is_project)

        # Rij eronder: dynamisch label + items
        if is_project:
            self.stock_label.setVisible(False)
            self.show_stock_select.setVisible(False)
        elif is_bp:
            self.stock_label.setText("Type:")
            self.stock_label.setVisible(True)
            self.show_stock_select.setVisible(True)
            self._set_combo_items(self.show_stock_select, ["", "C", "S"], current=load_bp_default_type())
        else:
            self.stock_label.setText("Toon voorraad:")
            self.stock_label.setVisible(True)
            self.show_stock_select.setVisible(True)
            self._set_combo_items(self.show_stock_select, ["R", "S", "B"], current=load_show_stock())

        # UI reset
        self.input_field.clear()
        self.input_field.setFocus()
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.result_count_label.setText("Aantal resultaten: 0")
        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.blockSignals(True)
            self.select_all_checkbox.setChecked(False)

    # --------------- Helper: detail-payload normaliseren ---------------

    def _normalize_detail_payload(self, payload):
        """
        Converteer de respons van get_item_detail_stockinfo(*) naar een dictionary.
        Ondersteunt dict, list, str, bytes/bytearray en None.
        """
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list):
            if payload and isinstance(payload[0], dict):
                return payload[0]  # vaak 1 record als [ {...} ]
            return {"RAW": payload}
        if isinstance(payload, (bytes, bytearray)):
            try:
                return json.loads(payload.decode("utf-8", errors="ignore"))
            except Exception:
                return {"RAW_TEXT": payload[:2000].decode("utf-8", errors="ignore")}
        if isinstance(payload, str):
            s = payload.strip()
            try:
                return json.loads(s)
            except Exception:
                return {"RAW_TEXT": s[:2000]}
        # laatste redmiddel
        return {"RAW": payload}

    # --------------- NIEUW: Export/Elements openen ---------------
    def _open_docs_window(self):
        """Opent ui_docs (Elements) vanuit het menu Export."""
        try:
            w = DocsWindow()
            w.showMaximized()
            self.docs_windows.append(w)  # referentie bewaren
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Kon 'Elements' openen:\n{e}")
