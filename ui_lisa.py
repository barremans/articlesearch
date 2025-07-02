# ui_lisa.py

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView

from settings import load_lisa_headers_map

LISA_HEADERS_MAP = load_lisa_headers_map()


class LisaTab(QWidget):
    def __init__(self, data):
        super().__init__()
        layout = QVBoxLayout(self)
        table = QTableWidget()
        headers = list(LISA_HEADERS_MAP.keys())

        if data:
            table.setRowCount(len(data))
            table.setColumnCount(len(headers))
            mapped_headers = [LISA_HEADERS_MAP.get(h, h) for h in headers]
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
            table.setItem(0, 0, QTableWidgetItem("❌ Geen LISA data beschikbaar."))

        table.horizontalHeader().setStretchLastSection(True)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)
