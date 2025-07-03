# file_editor_dialog.py

import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTextEdit, QPushButton, QHBoxLayout, QMessageBox, QWidget

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
