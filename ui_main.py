# ui_main.py

import os
import sys
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
    load_default_search_type, save_default_search_type
)
from label.label_generator import generate_label
from label.label_settings_dialog import LabelSettingsDialog
from version import __version__
from updater import check_for_update, download_latest_release
from bug_report_dialog import BugDialog

# import van je nieuwe JSON-viewer voor project searches
from project_ui import ProjectWindow


class FileEditorDialog(QDialog):
    def __init__(self, parent: QWidget, file_path: str):
        super().__init__(parent)
        self.file_path = file_path
        self.setWindowTitle(f"Bestand bewerken: {os.path.basename(file_path)}")
        self.resize(700, 600)
        layout = QVBoxLayout(self)

        self.info_label = QLabel(f"<b>Bestand:</b> {file_path}")
        layout.addWidget(self.info_label)

        self.editor = QTextEdit()
        layout.addWidget(self.editor, stretch=1)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self._save_file)
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(self.save_btn)
        layout.addLayout(btn_layout)

        self._load_file()

    def _load_file(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            QMessageBox.warning(self, "Fout bij openen bestand", f"Kan bestand niet lezen:\n{e}")
            self.close()
            return
        self.editor.setPlainText(content)

    def _save_file(self):
        new_content = self.editor.toPlainText()
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            QMessageBox.information(self, "Opgeslagen", f"{os.path.basename(self.file_path)} is bewaard.")
            self.accept()
        except Exception as e:
            QMessageBox.warning(self, "Fout bij opslaan", f"Kon bestand niet opslaan:\n{e}")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.collected_data = []
        self.detail_windows = []
        self.upload_windows = []
        self.project_window = None
        # Voeg update-knop toe bij init zodat check_for_update() niet faalt
        self.setStatusBar(QStatusBar(self))
        # ❗ Vertraagde updatecheck zodat QMessageBox correct toont
        QTimer.singleShot(1000, lambda: check_for_update(__version__, self))
        self.update_btn = QPushButton("Update nu")
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
        QShortcut(QKeySequence("F1"), self).activated.connect(self._show_help_dialog)
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self._open_selected_row)

        self.installEventFilter(self)
        self.input_field.installEventFilter(self)
        self.setStatusBar(QStatusBar(self))

        #check_for_update(__version__, self, self._enable_update_button)
        #check_for_update(__version__, self)
        #QTimer.singleShot(1000, lambda: check_for_update(__version__, self))




    def _enable_update_button(self, is_update_available: bool):
        if hasattr(self, 'update_btn') and self.update_btn:
            self.update_btn.setEnabled(is_update_available)

    def _create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Bestand")
        file_menu.addAction("A&fsluiten").triggered.connect(self.close)

        settings_menu = menubar.addMenu("&Instellingen")
        settings_menu.addAction("⚙️ &Kies omgeving (test/live)").triggered.connect(self._choose_environment)
        settings_menu.addAction("🛠️ &Instellingen wijzigen...").triggered.connect(self._show_settings_dialog)
        settings_menu.addAction("🏷️ &Label-instellingen...").triggered.connect(self._show_label_settings_dialog)
        settings_menu.addSeparator()
        settings_menu.addAction("✏️ Bewerk style.qss").triggered.connect(self._open_style_qss_editor)
        settings_menu.addAction("✏️ Bewerk detail.qss").triggered.connect(self._open_detail_qss_editor)
        settings_menu.addAction("✏️ Bewerk upload.qss").triggered.connect(self._open_upload_qss_editor)

        report_menu = menubar.addMenu("&Rapporteren")
        report_menu.addAction("🐞 &Bug of feature melden...").triggered.connect(self._show_bug_report_dialog)

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&Help").triggered.connect(self._show_help_dialog)
        settings_menu.addSeparator()
        help_menu.addAction("&Over...").triggered.connect(self._show_about_dialog)
        help_menu.addAction("📄 &Changelog...").triggered.connect(self._show_changelog_dialog)


    def _create_main_layout(self):
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(
            "Geef zoekterm in… geen prefix= zoeken op art.nr., * omschrijving, - kernwoorden, / leverancier"
        )

        self.search_type_select = QComboBox()
        self.search_type_select.addItems(["Standaard", "Project"])
        #self.search_type_select.setCurrentText("Standaard")
        self.search_type_select.setCurrentText(load_default_search_type())
        self.search_type_select.currentTextChanged.connect(self._toggle_fields_by_search_type)

        self.search_type_select.currentTextChanged.connect(self._update_input_tooltip)


        self.mode_label = QLabel("Zoekmodus:")
        self.mode_select = QComboBox()
        self.mode_select.addItems(["AND", "OR"])

        self.stock_label = QLabel("Toon voorraad:")
        self.show_stock_select = QComboBox()
        self.show_stock_select.addItems(["R", "S", "B"])
        self.show_stock_select.setCurrentText(load_show_stock())
        self.show_stock_select.currentTextChanged.connect(save_show_stock)

        self.search_button = QPushButton("Zoeken")
        self.search_button.clicked.connect(self.perform_search)

        self.table = QTableWidget()
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

        #labels = ["Zoekterm:", "Search-type:", "Zoekmodus:", "Toon voorraad:"]
        #lbl_objs = [QLabel(t) for t in labels]
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

    def perform_search(self):
        zoekterm     = self.input_field.text().strip()
        mode         = self.mode_select.currentText()
        is_project   = (self.search_type_select.currentText() == "Project")
        self.result_count_label.setText("Aantal resultaten: 0")

        if not zoekterm:
            self.table.setRowCount(0)
            return

        # start spinner
        self.loading_spinner.show()
        self.loading_movie.start()
        QApplication.processEvents()

        try:
            data = send_data_request(
                zoekterm,
                mode,
                project_search=is_project,
                is_closed=""
            )
        except Exception as e:
            if is_project:
                # bij project altijd JSON-venster, ook op error
                data = {"error": str(e)}
            else:
                # standaard: fout in tabel en return
                self.table.setRowCount(0)
                self.table.setColumnCount(1)
                self.table.setHorizontalHeaderLabels(["Fout"])
                self.table.insertRow(0)
                self.table.setItem(0, 0, QTableWidgetItem(str(e)))
                self.loading_movie.stop()
                self.loading_spinner.hide()
                return

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
        else:
            self.populate_table(data)

        # stop spinner
        self.loading_movie.stop()
        self.loading_spinner.hide()


    def populate_table(self, data: list):
        show_stock = load_show_stock()
        if show_stock == "S":
            originele_columns = [
                "ItemCode", "ItemName", "SUPPLIERIDPRODUCT", "QUANTITY",
                "WHSNAME", "LOCNAME", "QTYMININV", "QTYMAXINV",
                "SUPPLIERNAME", "PRICESUPPLIER", "NOTE"
            ]
        else:
            originele_columns = ["ItemCode", "ItemName", "SuppCatNum"]

        columns = ["Selectie"] + originele_columns
        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for idx in range(1, len(columns)):
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
        from settings import load_show_stock
        from PySide6.QtCore import QMimeData

        dialog = QDialog(self)
        dialog.setWindowTitle("Verzamelde rijen")
        dialog.resize(800, 400)

        # Bepaal kolomnamen volgens de voorraad-keuze
        show_stock = load_show_stock()
        if show_stock == "S":
            headers = [
                "Art.Nr.", "Desc.", "Vendor Nr.", "Qty",
                "Whs.", "LOCNAME", "QTYMIN", "QTYMAX",
                "Suppl", "Price Suppl", "NOTE"
            ]
        else:
            headers = ["Art.Nr.", "Desc.", "Vendor Nr."]

        # Tabel opbouwen
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

        # Kopieer geselecteerde (of alle) rijen als TSV én HTML-tabel
        def copy_selection_to_clipboard():
            md = QMimeData()
            sel_rows = [idx.row() for idx in table.selectionModel().selectedRows()]
            if not sel_rows:
                sel_rows = list(range(table.rowCount()))

            # Maak TSV
            tsv_lines = ["\t".join(headers)]
            for r in sel_rows:
                tsv_lines.append("\t".join(table.item(r, c).text() for c in range(table.columnCount())))
            md.setText("\n".join(tsv_lines))

            # Maak HTML
            html = ["<table border='1' cellspacing='0' cellpadding='2'>"]
            html.append("<tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr>")
            for r in sel_rows:
                html.append(
                    "<tr>" +
                    "".join(f"<td>{table.item(r, c).text()}</td>" for c in range(table.columnCount())) +
                    "</tr>"
                )
            html.append("</table>")
            md.setHtml("".join(html))

            QApplication.clipboard().setMimeData(md)

        # Knoppen
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

        # 1) Maak de interne lijst leeg
        self.collected_data.clear()

        # 2) Haal alle checkbox-selecties uit de hoofd-tabel
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

        # 3) Zet de 'Selecteer alles' checkbox terug uit, indien aanwezig
        if hasattr(self, 'select_all_checkbox'):
            # Blokkeren van signaal om toggling niet opnieuw _toggle_select_all te triggeren
            self.select_all_checkbox.blockSignals(True)
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.blockSignals(False)

        QMessageBox.information(self, "Lijst geleegd", "De verzamelde rijen zijn nu verwijderd en alle vakjes zijn uitgevinkt.")

    def handle_row_double_click(self, item):
        row = item.row()
        # Kolom 1 bevat ItemCode (kolom 0 is checkbox)
        item_code = self.table.item(row, 1).text()
        self.table.clearSelection()
        try:
            detail_data = get_item_detail_stockinfo(item_code) or {}

            dialog = DetailWindow(parent=self, item_code=item_code, detail_data=detail_data)
            dialog.show()
            self._reposition_detail(dialog)
            self.detail_windows.append(dialog)

        except Exception as e:
            QMessageBox.warning(self, "Detail Fout", str(e))

        #QTimer.singleShot(0, lambda: self.input_field.setFocus(Qt.FocusReason.ActiveWindowFocusReason))

    def _open_selected_row(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Geen selectie", "Selecteer een rij om te openen.")
            return
        first_index = selected_items[0].row()
        self.handle_row_double_click(self.table.item(first_index, 1))

    def show_table_context_menu(self, position: QPoint):
        index = self.table.indexAt(position)
        if not index.isValid():
            return
        row = index.row()
        # Kolom 1 is ItemCode
        item_code = self.table.item(row, 1).text()
        menu = QMenu(self)
        copy_action = menu.addAction("📋 Kopieer rij")
        detail_action = menu.addAction("🔍 Toon detail")
        label_action = menu.addAction("🏷️ Genereer label")
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        if action == copy_action:
            values = [self.table.item(row, col).text() for col in range(1, self.table.columnCount())]
            QApplication.clipboard().setText("\t".join(values))
        elif action == detail_action:
            self.handle_row_double_click(self.table.item(row, 1))
        elif action == label_action:
            self._generate_label()

    def _generate_label(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Geen selectie", "Selecteer een rij om een label te genereren.")
            return
        row = selected[0].row()
        code = self.table.item(row, 1).text()
        desc = self.table.item(row, 2).text()
        supplier = self.table.item(row, 3).text() if self.table.columnCount() > 3 else "-"
        generate_label(code, desc, supplier, "00000000")

    def _show_label_settings_dialog(self):
        dialog = LabelSettingsDialog(self)
        dialog.exec()

    def _clear_search(self):
        self.input_field.clear()
        self.input_field.setFocus()
        self.table.setRowCount(0)
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

    # — OVERRIDES voor moveEvent en resizeEvent zodat DetailWindows mee verplaatsen —
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
    # — EINDE OVERRIDES —
    
    # ————————————————
    #  Vier nieuwe methods in MainWindow voor de FileEditorDialog
    # ————————————————

    def _open_style_qss_editor(self):
        """Open de editor voor ./assets/css/style.qss"""
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "style.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_detail_qss_editor(self):
        """Open de editor voor ./assets/css/detail.qss"""
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "detail.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_upload_qss_editor(self):
        """Open de editor voor ./assets/css/upload.qss"""
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "upload.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_ui_main_py_editor(self):
        """Open de editor voor ui_main.py zelf"""
        path = os.path.join(os.path.dirname(__file__), "ui_main.py")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_ui_detail_py_editor(self):
        """Open de editor voor ui_detail.py"""
        path = os.path.join(os.path.dirname(__file__), "ui_detail.py")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_ui_upload_py_editor(self):
        """Open de editor voor ui_upload.py (of hoe jouw upload-bestand ook heet)"""
        path = os.path.join(os.path.dirname(__file__), "ui_upload.py")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()
    # —————————————— Einde nieuwe methods —

    def _on_qss_file_changed(self, path: str):
        """Herlaadt het gewijzigde .qss-bestand en past het toe."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                qss = f.read()
        except Exception:
            # bestand kan nog in flux zijn: probeer na 0.5s opnieuw
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

    def _show_settings_dialog(self):
        from settings import (
            load_environment, save_environment,
            load_show_stock, save_show_stock,
            load_detail_modal, save_detail_modal,
            load_default_search_type, save_default_search_type,
            load_tab_order, save_tab_order
        )
        from PySide6.QtWidgets import QListWidget, QListWidgetItem

        dialog = QDialog(self)
        dialog.setWindowTitle("Instellingen")
        dialog.resize(400, 500)

        layout = QVBoxLayout(dialog)

        # Omgeving
        env = QComboBox()
        env.addItems(["live", "test"])
        env.setCurrentText(load_environment())

        # Voorraad
        stock = QComboBox()
        stock.addItems(["R", "S", "B"])
        stock.setCurrentText(load_show_stock())

        # Detailweergave als modal
        modal = QCheckBox("Toon detail als modal dialoog")
        modal.setChecked(load_detail_modal())

        # Zoektype
        search_type_default = QComboBox()
        search_type_default.addItems(["Standaard", "Project"])
        search_type_default.setCurrentText(load_default_search_type())

        # Tab-volgorde editor
        tab_order_label = QLabel("Tab-volgorde (versleep om te herschikken):")
        tab_order_list = QListWidget()
        tab_order_list.setDragDropMode(QListWidget.InternalMove)
        current_order = load_tab_order()
        all_tabs = ["art", "install", "vta", "vta_cert"]

        # Voeg alle aanwezige + ontbrekende tabs toe
        seen = set()
        for tab in current_order + [t for t in all_tabs if t not in current_order]:
            if tab not in seen:
                tab_order_list.addItem(QListWidgetItem(tab))
                seen.add(tab)

        # Saveknop
        save = QPushButton("Opslaan")

        def _save_config():
            save_environment(env.currentText())
            save_show_stock(stock.currentText())
            save_detail_modal(modal.isChecked())
            save_default_search_type(search_type_default.currentText())

            new_order = [tab_order_list.item(i).text() for i in range(tab_order_list.count())]
            save_tab_order(new_order)

            QMessageBox.information(dialog, "Instellingen", "Instellingen opgeslagen.")
            dialog.accept()

        save.clicked.connect(_save_config)

        # Layout samenstellen
        layout.addWidget(QLabel("Omgeving:"))
        layout.addWidget(env)
        layout.addWidget(QLabel("Toon voorraad:"))
        layout.addWidget(stock)
        layout.addWidget(modal)
        layout.addWidget(QLabel("Standaard zoektype:"))
        layout.addWidget(search_type_default)
        layout.addSpacing(10)
        layout.addWidget(tab_order_label)
        layout.addWidget(tab_order_list)
        layout.addStretch()
        layout.addWidget(save)

        dialog.setLayout(layout)
        dialog.exec()

    def _save_config(self, dialog, env, stock, modal, search_type_default):
        save_environment(env.currentText())
        save_show_stock(stock.currentText())
        save_detail_modal(modal.isChecked())
        save_default_search_type(search_type_default.currentText())
        QMessageBox.information(dialog, "Instellingen", "Instellingen opgeslagen.")
        dialog.accept()

    def _show_changelog_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Changelog")
        dialog.resize(800, 600)

        layout = QVBoxLayout(dialog)
        changelog_view = QTextBrowser()
        changelog_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Zoek pad naar changelog.md
        if getattr(sys, "frozen", False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(__file__)

        #changelog_file = os.path.join(base_dir, "changelog.md")
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

        #help_file = os.path.join(base_dir, "help.md")
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

        # ✅ Updatecontrole met knop activatie via callback
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
        else:
            tip = "Geef zoekterm in… geen prefix = zoeken op art.nr., * omschrijving, - kernwoorden, / leverancier"
        self.input_field.setToolTip(tip)
        self.input_field.setPlaceholderText(tip)

    def _toggle_fields_by_search_type(self, search_type: str):
        is_project = (search_type == "Project")
        self.mode_label.setVisible(not is_project)
        self.mode_select.setVisible(not is_project)
        self.stock_label.setVisible(not is_project)
        self.show_stock_select.setVisible(not is_project)

        # Leeg de zoekinput en focus erop
        self.input_field.clear()
        self.input_field.setFocus()

