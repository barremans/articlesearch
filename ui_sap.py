#ui_sap.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView

from settings import load_sap_headers_map

SAP_HEADERS_MAP = load_sap_headers_map()


class SapTab(QWidget):
    def __init__(self, raw_data):
        super().__init__()
        layout = QVBoxLayout(self)
        table = QTableWidget()

        # Voorbereiden van data (bereken VrijeStock)
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

        headers = list(SAP_HEADERS_MAP.keys())

        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(headers))
            mapped_headers = [SAP_HEADERS_MAP.get(h, h) for h in headers]
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
            table.setItem(0, 0, QTableWidgetItem("❌ Geen SAP data beschikbaar."))

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
