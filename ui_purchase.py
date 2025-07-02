# ui_purchase.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from settings import load_field_labels

class PurchaseTab(QWidget):
    def __init__(self, data):
        super().__init__()
        layout = QVBoxLayout(self)
        table = QTableWidget()

        # Labels ophalen uit settings
        labels_map = load_field_labels("purchase")
        headers = list(labels_map.keys())
        mapped_headers = [labels_map.get(h, h) for h in headers]

        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(headers))
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
            table.setItem(0, 0, QTableWidgetItem("❌ Geen aankoopdata beschikbaar."))

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
