# help_dialogs.py

import os
import sys
import markdown
from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QLabel
from PySide6.QtCore import Qt
from version import __version__


def _find_help_md() -> str:
    """
    Vind help.md in zowel development als PyInstaller (onedir/onefile) situaties.

    We proberen meerdere paden omdat de output-structuur kan verschillen:
    - sys._MEIPASS\docs\help.md              (embedded via PyInstaller datas)
    - sys._MEIPASS\_internal\docs\help.md    (sommige bundels)
    - <exe_dir>\docs\help.md                 (mee-geïnstalleerd naast exe)
    - <exe_dir>\_internal\docs\help.md       (mee-geïnstalleerd in _internal)
    - <source_dir>\docs\help.md              (development)
    """
    candidates = []

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        exe_dir = os.path.dirname(sys.executable)

        if meipass:
            candidates += [
                os.path.join(meipass, "docs", "help.md"),
                os.path.join(meipass, "_internal", "docs", "help.md"),
            ]

        candidates += [
            os.path.join(exe_dir, "docs", "help.md"),
            os.path.join(exe_dir, "_internal", "docs", "help.md"),
        ]
    else:
        base_dir = os.path.dirname(__file__)
        candidates += [
            os.path.join(base_dir, "docs", "help.md"),
            os.path.join(base_dir, "_internal", "docs", "help.md"),
        ]

    for p in candidates:
        if os.path.exists(p):
            return p

    raise FileNotFoundError("help.md niet gevonden. Gezocht in:\n" + "\n".join(candidates))


def _badge_search_paths() -> list[str]:
    """
    Zoekpaden voor badges/afbeeldingen die in markdown kunnen voorkomen.
    We nemen zowel MEIPASS als exe-dir mee (en in dev de source-dir).
    """
    paths = []

    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        exe_dir = os.path.dirname(sys.executable)

        if meipass:
            paths.append(os.path.join(meipass, "assets", "badges"))
            paths.append(os.path.join(meipass, "_internal", "assets", "badges"))

        paths.append(os.path.join(exe_dir, "assets", "badges"))
        paths.append(os.path.join(exe_dir, "_internal", "assets", "badges"))
    else:
        base_dir = os.path.dirname(__file__)
        paths.append(os.path.join(base_dir, "assets", "badges"))

    # enkel bestaande paden teruggeven
    return [p for p in paths if os.path.exists(p)]


def show_help_dialog(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Help")
    dialog.resize(800, 600)

    layout = QVBoxLayout(dialog)
    help_view = QTextBrowser()

    # Zorg dat afbeeldingen (badges) in markdown gevonden worden
    sp = _badge_search_paths()
    if sp:
        help_view.setSearchPaths(sp)

    try:
        help_file = _find_help_md()
        with open(help_file, "r", encoding="utf-8") as f:
            html = markdown.markdown(
                f.read(),
                extensions=["tables"],  # handig voor markdown tabellen
            )
            help_view.setHtml(html)
    except Exception as e:
        help_view.setPlainText(f"Fout bij laden help.md:\n{e}")

    layout.addWidget(help_view, 1)

    version_label = QLabel(f"Versie: {__version__}")
    version_label.setAlignment(Qt.AlignRight)
    layout.addWidget(version_label)

    dialog.setLayout(layout)
    dialog.exec()
