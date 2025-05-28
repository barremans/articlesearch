#ui_main.py
import os
import markdown
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QStatusBar, QMenu, QApplication,
    QHeaderView, QInputDialog, QCheckBox, QTextBrowser
)
from PySide6.QtGui import QShortcut, QKeySequence, QMovie, QIcon
from PySide6.QtCore import QEvent, Qt, QPoint, QTimer

from data_request import send_data_request
from ui_detail import DetailWindow
from stock_info import get_item_detail_stockinfo
from settings import (
    load_environment, save_environment,
    load_show_stock, save_show_stock,
    load_detail_modal, save_detail_modal
)
from label.label_generator import generate_label
from label.label_settings_dialog import LabelSettingsDialog
from version import __version__
from updater import check_for_update, download_latest_release
from bug_report_dialog import BugDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Artikelzoeker")
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "stocks.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1000, 700)

        css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "style.qss")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

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

        check_for_update(__version__, self, self._enable_update_button)

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

        report_menu = menubar.addMenu("&Rapporteren")
        report_menu.addAction("🐞 &Bug of feature melden...").triggered.connect(self._show_bug_report_dialog)

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&Helpvenster").triggered.connect(self._show_help_dialog)
        help_menu.addAction("&Over...").triggered.connect(self._show_about_dialog)


    def _create_main_layout(self):
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Geef zoekterm in...")

        self.mode_select = QComboBox()
        self.mode_select.addItems(["AND", "OR"])

        self.show_stock_select = QComboBox()
        self.show_stock_select.addItems(["R", "S", "B"])
        self.show_stock_select.setCurrentText(load_show_stock())
        self.show_stock_select.currentTextChanged.connect(save_show_stock)

        self.search_button = QPushButton("Zoeken")
        self.search_button.clicked.connect(self.perform_search)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["ItemCode", "ItemName", "SuppCatNum"])
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_table_context_menu)
        self.table.itemDoubleClicked.connect(self.handle_row_double_click)

        self.result_count_label = QLabel("Aantal resultaten: 0")

        self.loading_spinner = QLabel()
        self.loading_spinner.setAlignment(Qt.AlignCenter)
        gif_path = os.path.join(os.path.dirname(__file__), "assets", "spinner.gif")
        self.loading_movie = QMovie(gif_path)
        self.loading_spinner.setMovie(self.loading_movie)
        self.loading_spinner.hide()

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Zoekterm:"))
        layout.addWidget(self.input_field)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Zoekmodus:"))
        mode_layout.addWidget(self.mode_select)

        stock_layout = QHBoxLayout()
        stock_layout.addWidget(QLabel("Toon voorraad:"))
        stock_layout.addWidget(self.show_stock_select)

        layout.addLayout(mode_layout)
        layout.addLayout(stock_layout)
        layout.addWidget(self.search_button)
        layout.addWidget(QLabel("Resultaten:"))
        layout.addWidget(self.table)
        layout.addWidget(self.result_count_label)
        layout.addWidget(self.loading_spinner)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def perform_search(self):
        zoekterm = self.input_field.text()
        mode = self.mode_select.currentText()
        self.result_count_label.setText("Aantal resultaten: 0")
        if not zoekterm:
            self.table.setRowCount(0)
            return
        self.loading_spinner.show()
        self.loading_movie.start()
        QApplication.processEvents()
        try:
            data = send_data_request(zoekterm, mode)
            self.populate_table(data)
        except Exception as e:
            self.table.setRowCount(0)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Fout"])
            self.table.insertRow(0)
            self.table.setItem(0, 0, QTableWidgetItem(str(e)))
        finally:
            self.loading_movie.stop()
            self.loading_spinner.hide()

    def populate_table(self, data: list):
        show_stock = load_show_stock()
        if show_stock == "S":
            columns = ["ItemCode", "ItemName", "SUPPLIERIDPRODUCT", "QUANTITY", "WHSNAME", "LOCNAME", "QTYMININV", "QTYMAXINV", "SUPPLIERNAME", "PRICESUPPLIER", "NOTE"]
        else:
            columns = ["ItemCode", "ItemName", "SuppCatNum"]

        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        for row, item in enumerate(data):
            for col, key in enumerate(columns):
                val = item.get(key, "")
                val = f"{val:.2f}" if isinstance(val, float) else str(val or "")
                cell = QTableWidgetItem(val)
                cell.setToolTip(val)
                self.table.setItem(row, col, cell)

        self.result_count_label.setText(f"Aantal resultaten: {len(data)}")
        if len(data) > 0:
            self.table.selectRow(0)

    def handle_row_double_click(self, item):
        row = item.row()
        item_code = self.table.item(row, 0).text()
        self.table.clearSelection()
        try:
            detail_data = get_item_detail_stockinfo(item_code)
            dialog = DetailWindow(item_code=item_code, detail_data=detail_data)
            dialog.setWindowModality(Qt.NonModal)
            dialog.show()
        except Exception as e:
            QMessageBox.warning(self, "Detail Fout", str(e))
        QTimer.singleShot(0, lambda: self.input_field.setFocus(Qt.FocusReason.ActiveWindowFocusReason))
        
    
    def _open_selected_row(self):
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Geen selectie", "Selecteer een rij om te openen.")
            return
        self.handle_row_double_click(selected_items[0])


    def show_table_context_menu(self, position: QPoint):
        index = self.table.indexAt(position)
        if not index.isValid():
            return
        row = index.row()
        item_code = self.table.item(row, 0).text()
        menu = QMenu(self)
        copy_action = menu.addAction("📋 Kopieer rij")
        detail_action = menu.addAction("🔍 Toon detail")
        label_action = menu.addAction("🏷️ Genereer label")
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        if action == copy_action:
            values = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
            QApplication.clipboard().setText("\t".join(values))
        elif action == detail_action:
            self.handle_row_double_click(self.table.item(row, 0))
        elif action == label_action:
            self._generate_label()

    def _generate_label(self):
        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Geen selectie", "Selecteer een rij om een label te genereren.")
            return
        row = selected[0].row()
        code = self.table.item(row, 0).text()
        desc = self.table.item(row, 1).text()
        supplier = self.table.item(row, 2).text() if self.table.columnCount() > 2 else "-"
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
        selected, ok = QInputDialog.getItem(self, "Omgeving kiezen", "Selecteer omgeving:", options, options.index(current), False)
        if ok and selected != current:
            save_environment(selected)
            QMessageBox.information(self, "Herstart vereist", f"Omgeving gewijzigd naar '{selected}'. Gelieve te herstarten.")

    def _show_settings_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Instellingen")
        dialog.resize(300, 200)

        layout = QVBoxLayout(dialog)
        env = QComboBox()
        env.addItems(["live", "test"])
        env.setCurrentText(load_environment())

        stock = QComboBox()
        stock.addItems(["R", "S", "B"])
        stock.setCurrentText(load_show_stock())

        modal = QCheckBox("Toon detail als modal dialoog")
        modal.setChecked(load_detail_modal())

        save = QPushButton("Opslaan")
        save.clicked.connect(lambda: self._save_config(dialog, env, stock, modal))

        layout.addWidget(QLabel("Omgeving:"))
        layout.addWidget(env)
        layout.addWidget(QLabel("Toon voorraad:"))
        layout.addWidget(stock)
        layout.addWidget(modal)
        layout.addWidget(save)

        dialog.setLayout(layout)
        dialog.exec()

    def _save_config(self, dialog, env, stock, modal):
        save_environment(env.currentText())
        save_show_stock(stock.currentText())
        save_detail_modal(modal.isChecked())
        QMessageBox.information(dialog, "Instellingen", "Instellingen opgeslagen.")
        dialog.accept()

    def _show_help_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Help")
        layout = QVBoxLayout()
        help_view = QTextBrowser()
        help_file = os.path.join(os.path.dirname(__file__), "help.md")
        try:
            with open(help_file, "r", encoding="utf-8") as f:
                help_view.setHtml(markdown.markdown(f.read()))
        except Exception as e:
            help_view.setPlainText(f"Fout bij laden help.md:\n{e}")
        layout.addWidget(help_view)
        layout.addWidget(QLabel(f"Versie: {__version__}"))
        dialog.setLayout(layout)
        dialog.resize(800, 600)
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

        dialog.setLayout(layout)
        dialog.exec()

    def _show_bug_report_dialog(self):
        dialog = BugDialog(self)
        dialog.exec()
