# ui_no_access.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt
from translations import get_labels
from settings import load_language


class NoAccessWindow(QWidget):
    def __init__(self):
        super().__init__()

        labels = get_labels(load_language()).get("no_access", {})

        self.setWindowTitle(labels.get("title", "Geen toegang"))
        self.setFixedSize(520, 260)

        layout = QVBoxLayout(self)

        title = QLabel("🚫 " + labels.get("title", "Geen toegang"))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size:20px; font-weight:bold;")

        message = QLabel(
            labels.get(
                "message",
                "U bent niet gemachtigd om deze applicatie te gebruiken."
            )
        )
        message.setAlignment(Qt.AlignCenter)
        message.setWordWrap(True)

        hint = QLabel(
            labels.get(
                "hint",
                "U moet lid zijn van de Azure AD-groep 'Alle gebruikers'."
            )
        )
        hint.setAlignment(Qt.AlignCenter)
        hint.setStyleSheet("color:gray;")

        layout.addStretch()
        layout.addWidget(title)
        layout.addSpacing(10)
        layout.addWidget(message)
        layout.addSpacing(15)
        layout.addWidget(hint)
        layout.addStretch()
