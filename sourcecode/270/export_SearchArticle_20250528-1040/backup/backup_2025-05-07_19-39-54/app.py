import sys
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLineEdit,
    QPushButton, QLabel, QComboBox, QHBoxLayout, QTableWidget, QTableWidgetItem
)
from data_request import send_data_request

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Article Search")

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Geef zoekterm in...")

        self.mode_select = QComboBox()
        self.mode_select.addItems(["AND", "OR"])

        self.search_button = QPushButton("Zoeken")
        self.search_button.clicked.connect(self.perform_search)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ItemCode", "ItemName", "SuppCatNum", "INTERNIDPRODUCT", "PRODUCTNAME"])

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Zoekterm:"))
        layout.addWidget(self.input_field)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Zoekmodus:"))
        mode_layout.addWidget(self.mode_select)
        layout.addLayout(mode_layout)

        layout.addWidget(self.search_button)
        layout.addWidget(QLabel("Resultaten:"))
        layout.addWidget(self.table)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def perform_search(self):
        zoekterm = self.input_field.text()
        mode = self.mode_select.currentText()

        if not zoekterm:
            self.table.setRowCount(0)
            return

        try:
            data = send_data_request(zoekterm, mode)
            self.populate_table(data)
        except Exception as e:
            self.table.setRowCount(0)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Fout"])
            self.table.insertRow(0)
            self.table.setItem(0, 0, QTableWidgetItem(str(e)))

    def populate_table(self, data: list):
        self.table.setRowCount(len(data))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ItemCode", "ItemName", "SuppCatNum", "INTERNIDPRODUCT", "PRODUCTNAME"])

        for row, item in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(item.get("ItemCode", "")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("ItemName", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("SuppCatNum", "")))
            self.table.setItem(row, 3, QTableWidgetItem(item.get("INTERNIDPRODUCT", "")))
            self.table.setItem(row, 4, QTableWidgetItem(item.get("PRODUCTNAME", "")))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
