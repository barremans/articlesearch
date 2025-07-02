# ui_logistics.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView
from settings import load_field_labels

class LogisticsTab(QWidget):
    def __init__(self, data):
        super().__init__()
        layout = QVBoxLayout(self)
        table = QTableWidget()

        excluded_keys = {
            "validFor", "validFrom", "validTo",
            "frozenFor", "frozenFrom", "frozenTo",
            "BlockOut", "ItemClass", "CLASSITEM"
        }

        labels_map = load_field_labels("logistics")
        filtered_data = [{"Veld": labels_map.get(k, k), "Waarde": v} for k, v in data.items() if k not in excluded_keys]

        headers = ["Veld", "Waarde"]
        table.setColumnCount(2)

        if filtered_data:
            table.setRowCount(len(filtered_data))
            table.setHorizontalHeaderLabels(headers)
            for row, record in enumerate(filtered_data):
                for col, key in enumerate(headers):
                    val = str(record.get(key, ""))
                    item = QTableWidgetItem(val)
                    item.setToolTip(val)
                    table.setItem(row, col, item)
        else:
            table.setRowCount(1)
            table.setHorizontalHeaderLabels(["Informatie"])
            table.setItem(0, 0, QTableWidgetItem("❌ Geen logistiek data beschikbaar."))

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
