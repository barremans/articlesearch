# settings_dialog.py

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton, QListWidget, QListWidgetItem, QMessageBox

from settings import (
    load_environment, save_environment,
    load_show_stock, save_show_stock,
    load_detail_modal, save_detail_modal,
    load_default_search_type, save_default_search_type,
    load_tab_order, save_tab_order
)

def show_settings_dialog(parent):
    dialog = QDialog(parent)
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

    # Tab-volgorde
    tab_order_label = QLabel("Tab-volgorde (versleep om te herschikken):")
    tab_order_list = QListWidget()
    tab_order_list.setDragDropMode(QListWidget.InternalMove)
    current_order = load_tab_order()
    all_tabs = ["art", "install", "vta", "vta_cert"]

    seen = set()
    for tab in current_order + [t for t in all_tabs if t not in current_order]:
        if tab not in seen:
            tab_order_list.addItem(QListWidgetItem(tab))
            seen.add(tab)

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
