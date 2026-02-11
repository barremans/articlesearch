# ui_pep.py
# V1.0.3

import sys
import json
from pathlib import Path

import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QHBoxLayout
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt

from pep_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT


# -----------------------------
# Error mapping (external JSON)
# -----------------------------
ERROR_MAP_PATH = Path("pep_errors.json")


def load_error_map() -> dict:
    """
    Laadt error mapping uit pep_errors.json.
    Als bestand ontbreekt/kapot is: return {} (fallback blijft werken).
    """
    if not ERROR_MAP_PATH.exists():
        return {}

    try:
        with open(ERROR_MAP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def format_datetime_for_header(dt_str: str) -> tuple[str, str]:
    if not dt_str:
        return "-", "-"
    s = str(dt_str).strip()

    if len(s) < 10 or s[4] != "-" or s[7] != "-":
        return "-", "-"

    date_part = f"{s[8:10]}-{s[5:7]}-{s[0:4]}"

    time_part = "-"
    if len(s) >= 16 and s[10] == " ":
        hh = s[11:13]
        mm = s[14:16]
        if hh.isdigit() and mm.isdigit():
            time_part = f"{hh}:{mm}"

    return date_part, time_part


def format_datetime_ddmmyyyy_hhmm(dt_str: str) -> str:
    d, t = format_datetime_for_header(dt_str)
    if d == "-" and t == "-":
        return "-"
    return f"{d} {t}"


class PepWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Peppol Invoice status")
        self.resize(1200, 800)

        # Load external error map once
        self.error_map = load_error_map()

        # Default language (voor later uitbreiden)
        self.lang = "nl"

        layout = QVBoxLayout(self)

        # --- Invoice input ---
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Geef factuur nummer in")
        layout.addWidget(QLabel("Invoice Nbr:"))
        layout.addWidget(self.key_input)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        self.fetch_button = QPushButton("Ophalen")
        self.fetch_button.clicked.connect(self.load_data)
        btn_row.addWidget(self.fetch_button)

        self.clear_button = QPushButton("Wissen")
        self.clear_button.clicked.connect(self.clear_input)
        btn_row.addWidget(self.clear_button)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # --- Header info ---
        self.header_text = QTextEdit()
        self.header_text.setReadOnly(True)
        self.header_text.setFixedHeight(90)
        layout.addWidget(QLabel("Header info:"))
        layout.addWidget(self.header_text)

        # --- Tabs ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.info_tab = QWidget()
        info_layout = QVBoxLayout(self.info_tab)

        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Zoek (in statusregels):"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Typ om te filteren...")
        self.search_input.textChanged.connect(self.filter_status_table)
        search_layout.addWidget(self.search_input)
        info_layout.addLayout(search_layout)

        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        info_layout.addWidget(self.table)

        self.tabs.addTab(self.info_tab, "Info")

        self.status_cache = []

        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.load_data)
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.close)

    # -----------------------------
    # Helper: string OR dict -> string
    # -----------------------------
    def _pick_text(self, value, fallback: str = "") -> str:
        """
        Ondersteunt:
          - "tekst" (string)
          - {"nl": "tekst", "fr": "texte"} (dict)
        """
        if isinstance(value, str):
            return value
        if isinstance(value, dict) and value:
            # voorkeurstaal, anders eerste waarde
            if self.lang in value and isinstance(value[self.lang], str):
                return value[self.lang]
            for v in value.values():
                if isinstance(v, str):
                    return v
        return fallback

    def clear_input(self):
        self.key_input.clear()
        self.key_input.setFocus()

    def clear_table(self):
        self.status_cache = []
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    def show_header_info(self, api_json: dict):
        data_field = api_json.get("Data", {})

        docentry = "-"
        task_status = "-"
        datum = "-"
        tijd = "-"

        if isinstance(data_field, dict):
            docentry = data_field.get("DocEntry", "-")
            task = data_field.get("TASK", {})
            if isinstance(task, dict):
                task_status = task.get("U_TaskStatus", "-")
                datum, tijd = format_datetime_for_header(task.get("U_CreateDateTime", ""))

        self.header_text.setPlainText(
            f"DocEntry: {docentry}\n"
            f"Status: {task_status}\n"
            f"Datum: {datum} {tijd}"
        )

    def extract_status_rows(self, api_json: dict) -> list[dict]:
        task = api_json.get("Data", {}).get("TASK", {})
        rows = task.get("STATUS", [])
        return [r for r in rows if isinstance(r, dict)]

    # -----------------------------
    # Status message translation
    # -----------------------------
    def translate_status_message(self, raw_message: str) -> str:
        """
        Vertaalt statusregel fouten via pep_errors.json.
        Fallback = exact originele tekst.
        """
        if not raw_message or "{" not in raw_message:
            return raw_message

        try:
            json_part = raw_message[raw_message.index("{"):]
            parsed = json.loads(json_part)
        except Exception:
            return raw_message

        errors = parsed.get("errors")
        if not isinstance(errors, list) or not errors or not isinstance(errors[0], dict):
            return raw_message

        first = errors[0]
        code = first.get("Code")
        description = first.get("Description", "")

        mapped = self.error_map.get(code) if code else None
        if isinstance(mapped, dict):
            user_msg = self._pick_text(mapped.get("user_message"), fallback=str(description))
            return user_msg

        return raw_message

    def show_status_table(self, rows: list[dict]):
        self.status_cache = rows

        columns = [
            ("U_LineNum", "Line"),
            ("U_CreateDateTime", "Datum"),
            ("U_Message", "Message"),
        ]

        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[1] for c in columns])
        self.table.setRowCount(len(rows))

        for r_idx, r in enumerate(rows):
            for c_idx, (key, _) in enumerate(columns):
                val = r.get(key, "")

                if key == "U_CreateDateTime":
                    val = format_datetime_ddmmyyyy_hhmm(val)

                if key == "U_Message":
                    val = self.translate_status_message(str(val))

                self.table.setItem(r_idx, c_idx, QTableWidgetItem(str(val)))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)

    def filter_status_table(self):
        query = self.search_input.text().lower().strip()
        if not query:
            self.show_status_table(self.status_cache)
            return

        filtered = []
        for r in self.status_cache:
            if any(query in str(v).lower() for v in r.values()):
                filtered.append(r)

        self.show_status_table(filtered)

    def translate_api_error(self, api_json: dict) -> tuple[str, str]:
        errors = api_json.get("errors", [])
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            first = errors[0]
            code = first.get("Code")
            description = first.get("Description", "")

            mapped = self.error_map.get(code) if code else None
            if isinstance(mapped, dict):
                title = self._pick_text(mapped.get("title"), fallback="API Fout")
                user_msg = self._pick_text(mapped.get("user_message"), fallback=str(description))
                return title, user_msg

            return "API Fout", str(description)

        return "API Fout", str(api_json.get("ErrorMessage") or "Onbekende fout")

    def load_data(self):
        invoice_nbr = self.key_input.text().strip()
        if not invoice_nbr:
            QMessageBox.warning(self, "Fout", "Geef een geldig factuurnummer in.")
            return

        env = API_ENVIRONMENTS[ENVIRONMENT]
        url = f"{env.get('base_url')}/api/datarequest"

        payload = {"ConfigurationID": env["pep_config_id"], "Key": invoice_nbr}
        headers = get_auth_header()
        headers.setdefault("Content-Type", "application/json")

        try:
            resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            self.show_header_info(data)

            if data.get("IsError"):
                title, msg = self.translate_api_error(data)
                QMessageBox.critical(self, title, msg)
                self.clear_table()
                return

            self.show_status_table(self.extract_status_rows(data))
            self.tabs.setCurrentWidget(self.info_tab)
            self.search_input.setText("")

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Fout", f"Request error: {e}")
        except ValueError:
            QMessageBox.critical(self, "Fout", "Response was geen geldige JSON.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PepWidget()
    w.show()
    sys.exit(app.exec())
