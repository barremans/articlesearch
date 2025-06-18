from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit

class DetailWindow(QDialog):
    def __init__(self, item_code, detail_data):
        super().__init__()
        self.setWindowTitle(f"Detail: {item_code}")
        layout = QVBoxLayout()

        layout.addWidget(QLabel("Detailinformatie:"))

        detail_text = QTextEdit()
        detail_text.setPlainText(detail_data)
        detail_text.setReadOnly(True)

        layout.addWidget(detail_text)
        self.setLayout(layout)
