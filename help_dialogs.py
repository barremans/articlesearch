# help_dialogs.py

import os
import sys
import markdown
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QLabel
from PySide6.QtCore import Qt
from version import __version__

def show_help_dialog(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Help")
    dialog.resize(800, 600)

    layout = QVBoxLayout(dialog)
    help_view = QTextBrowser()
    help_view.setSizePolicy(help_view.sizePolicy().horizontalPolicy(), help_view.sizePolicy().verticalPolicy())

    if getattr(sys, "frozen", False):
        base_dir = sys._MEIPASS
    else:
        base_dir = os.path.dirname(__file__)

    badges_folder = os.path.join(base_dir, "assets", "badges")
    help_view.setSearchPaths([badges_folder])

    help_file = os.path.join(base_dir, "docs", "help.md")
    try:
        with open(help_file, "r", encoding="utf-8") as f:
            html = markdown.markdown(f.read())
            help_view.setHtml(html)
    except Exception as e:
        help_view.setPlainText(f"Fout bij laden help.md:\n{e}")

    layout.addWidget(help_view, 1)

    version_label = QLabel(f"Versie: {__version__}")
    version_label.setAlignment(Qt.AlignRight)
    layout.addWidget(version_label)

    dialog.setLayout(layout)
    dialog.exec()
