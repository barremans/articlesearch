# ui_docs.py (FINAL — AD-only, met filters & grouping terug)
import sys
import os
from typing import Any, Dict, List
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests
import pandas as pd
from PySide6.QtCore import (
    Qt, Signal, Slot, QAbstractTableModel, QModelIndex
)
from PySide6.QtGui import QKeySequence, QShortcut, QIntValidator
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QMessageBox, QGroupBox, QRadioButton, QFileDialog, QSizePolicy,
    QTableView, QHeaderView
)

from auth import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT
from ui_docs_schema import apply_schema, set_sort_mode
from ui_labels import section_full_label, ui
import security_docs  # ✅ AD-only controle

requests.packages.urllib3.disable_warnings()  # type: ignore

CONFIGURATION_ID = os.environ.get("DOCS_CONFIGURATION_ID", "4AA8DF")

SALES_SECTIONS_ORDERED: List[str] = ["OSO", "OSDL", "OSDP", "OSR", "OSI"]
PURCHASE_SECTIONS_ORDERED: List[str] = ["OPO", "OPDL", "OPR", "OPI"]

DATE_FMT_UI = "%d-%m-%Y"


# ----------- Pandas → Qt Model -----------
class PandasModel(QAbstractTableModel):
    def __init__(self, df: pd.DataFrame):
        super().__init__()
        self._df = df

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._df)

    def columnCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self._df.columns)

    def _val(self, r, c):
        return self._df.iat[r, c]

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        val = self._val(index.row(), index.column())

        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            if pd.isna(val):
                return ""
            if isinstance(val, (pd.Timestamp, datetime)):
                return val.strftime(DATE_FMT_UI)
            return str(val)
        if role == Qt.ItemDataRole.UserRole:
            if pd.isna(val):
                return None
            if isinstance(val, (pd.Timestamp, datetime)):
                return pd.Timestamp(val).to_pydatetime()
            try:
                return float(val)
            except Exception:
                return str(val)
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)


# -------------------- Helpers --------------------
def _coerce_numeric(series: pd.Series) -> pd.Series:
    try:
        return pd.to_numeric(series, errors="coerce")
    except Exception:
        return series


def parse_section(items: List[Dict[str, Any]], section_code: str) -> pd.DataFrame:
    df = pd.DataFrame(items)
    if section_code == "OSO":
        if "Comments" not in df.columns:
            df["Comments"] = None
        if "ProjectBased" not in df.columns:
            df["ProjectBased"] = None

    for col in ("DocDate", "DocDueDate"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    if "CardName" not in df.columns:
        df["CardName"] = None
    if "Partner" in df.columns:
        df["CardName"] = df["CardName"].fillna(df["Partner"])
    if "Vendor" in df.columns:
        df["CardName"] = df["CardName"].fillna(df["Vendor"])

    if "DocTotal" in df.columns and "PaidSum" in df.columns:
        df["Outstanding"] = (df["DocTotal"] - df["PaidSum"]).round(2)

    if "OrderCount" not in df.columns:
        fallback = None
        for c in [
            "OrderCount", "DeliveryCount", "DownPaymentCount", "ReturnCount",
            "InvoiceCount", "PurchaseOrderCount", "ReceiptCount"
        ]:
            if c in df.columns:
                fallback = c
                break
        df["OrderCount"] = df[fallback] if fallback else pd.NA

    if "MaandenOud" in df.columns:
        df["MaandenOud"] = _coerce_numeric(df["MaandenOud"])

    for must_have in [
        "DocNum", "CardCode", "CardName", "DocDate", "DocDueDate",
        "DocTotal", "PaidSum", "Outstanding", "OrderCount",
        "MaandenOud", "SalesOwner", "DocOwner", "Buyer"
    ]:
        if must_have not in df.columns:
            df[must_have] = pd.NA
    return df


# ===================== MAIN WINDOW =====================
class DocsWindow(QWidget):
    api_success = Signal(dict, int)
    api_error = Signal(str, int)

    def __init__(self):
        super().__init__()

        # 🔒 Alleen starten als AD actief is
        if not security_docs.is_unlocked():
            QMessageBox.warning(
                self,
                "Geen AD-verbinding",
                "Deze module is enkel beschikbaar bij actieve AD-verbinding.\n"
                "Controleer je netwerk of AD-login."
            )
            self.close()
            return

        self.setWindowTitle("Open Sales/Purchase — Documents")
        self.setContentsMargins(8, 8, 8, 8)

        self._exec = ThreadPoolExecutor(max_workers=2)
        self._req_counter = 0
        self.section_frames_raw = {}
        self.section_frames_view = {}

        root = QVBoxLayout(self)
        content = QWidget()
        content_root = QVBoxLayout(content)
        root.addWidget(content)

        # ---------- Top row ----------
        row_top = QHBoxLayout()
        key_group = QGroupBox(ui("group_count"))
        g = QHBoxLayout(key_group)

        self.rb_6 = QRadioButton("6")
        self.rb_other = QRadioButton("Anders:")
        self.key_custom = QLineEdit()
        self.key_custom.setPlaceholderText("voer eigen aantal in (niet leeg)")
        self.key_custom.setEnabled(False)
        self.key_custom.setValidator(QIntValidator(0, 999999, self))
        self.key_custom.textEdited.connect(self._on_key_custom_edited)
        self.key_custom.returnPressed.connect(self.fetch_api)

        self.rb_6.setChecked(True)
        def on_rb_changed(): self.key_custom.setEnabled(self.rb_other.isChecked())
        self.rb_6.toggled.connect(on_rb_changed)
        self.rb_other.toggled.connect(on_rb_changed)

        g.addWidget(self.rb_6)
        g.addWidget(self.rb_other)
        g.addWidget(self.key_custom, 1)
        row_top.addWidget(key_group)
        content_root.addLayout(row_top)

        # ---------- Grouping filters ----------
        group_box = QGroupBox("Groepering")
        gl = QHBoxLayout(group_box)
        self.rb_group_cardname = QRadioButton("Klantnaam")
        self.rb_group_cardcode = QRadioButton("Klantcode")
        self.rb_group_docowner = QRadioButton("Document Owner")
        self.rb_group_salesowner = QRadioButton("Sales Owner")
        self.rb_group_maand = QRadioButton("Maanden oud")
        self.rb_group_cardname.setChecked(True)

        for rb in (
            self.rb_group_cardname,
            self.rb_group_cardcode,
            self.rb_group_docowner,
            self.rb_group_salesowner,
            self.rb_group_maand,
        ):
            gl.addWidget(rb)

        self.rb_group_cardname.toggled.connect(self._on_grouping_changed)
        self.rb_group_cardcode.toggled.connect(self._on_grouping_changed)
        self.rb_group_docowner.toggled.connect(self._on_grouping_changed)
        self.rb_group_salesowner.toggled.connect(self._on_grouping_changed)
        self.rb_group_maand.toggled.connect(self._on_grouping_changed)

        content_root.addWidget(group_box)

        # ---------- Buttons ----------
        actions = QHBoxLayout()
        self.btn_fetch = QPushButton(ui("btn_fetch"))
        self.btn_export = QPushButton(ui("btn_export"))
        self.btn_export_all = QPushButton(ui("btn_export_all"))

        self.btn_fetch.clicked.connect(self.fetch_api)
        actions.addWidget(self.btn_fetch)
        actions.addWidget(self.btn_export)
        actions.addWidget(self.btn_export_all)
        content_root.addLayout(actions)

        # ---------- Tabs ----------
        self.tabs = QTabWidget()
        content_root.addWidget(self.tabs, 1)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.fetch_api)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)

        # Signals
        self.api_success.connect(self._on_api_success)
        self.api_error.connect(self._on_api_error)

    # ---------- Grouping ----------
    def _current_group_mode(self) -> str:
        if self.rb_group_cardcode.isChecked():
            return "cardcode"
        if self.rb_group_docowner.isChecked():
            return "docowner"
        if self.rb_group_salesowner.isChecked():
            return "salesowner"
        if self.rb_group_maand.isChecked():
            return "maandenoud"
        return "cardname"

    def _on_grouping_changed(self):
        """Herbouwt tabbladen bij groeperingswijziging."""
        if self.section_frames_raw:
            set_sort_mode(self._current_group_mode())
            self._rebuild_views_from_raw()

    # ---------- Key input ----------
    @Slot(str)
    def _on_key_custom_edited(self, text: str):
        text = (text or "").strip()
        if text and not self.rb_other.isChecked():
            self.rb_other.setChecked(True)
        elif not text and not self.rb_6.isChecked():
            self.rb_6.setChecked(True)

    # ---------- API Call ----------
    def fetch_api(self):
        env = API_ENVIRONMENTS.get(ENVIRONMENT, {})
        base_url = env.get("base_url", "").rstrip("/")
        url = f"{base_url}/api/datarequest"
        headers = get_auth_header()
        payload = {"ConfigurationID": CONFIGURATION_ID, "Key": "6"}

        self._req_counter += 1
        req_id = self._req_counter

        def _worker():
            try:
                resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    self.api_success.emit(data, req_id)
                else:
                    self.api_error.emit(f"HTTP {resp.status_code}: {resp.text}", req_id)
            except Exception as e:
                self.api_error.emit(str(e), req_id)
        self._exec.submit(_worker)

    # ---------- Populate ----------
    def populate_from_response(self, data: Dict[str, Any]):
        self.tabs.clear()
        self.section_frames_raw.clear()
        self.section_frames_view.clear()

        root = data.get("Data") if isinstance(data, dict) else None
        if not isinstance(root, dict) or not root:
            QMessageBox.information(self, "Geen documenten", "Geen data van API ontvangen.")
            return

        tmp_raw = {}
        for code, rows in root.items():
            if isinstance(rows, list) and rows:
                tmp_raw[code] = parse_section(rows, code)

        if not tmp_raw:
            QMessageBox.information(self, "Geen data", "Er werden geen secties gevonden.")
            return

        set_sort_mode(self._current_group_mode())
        for code in (SALES_SECTIONS_ORDERED + PURCHASE_SECTIONS_ORDERED):
            if code in tmp_raw:
                self.section_frames_raw[code] = tmp_raw[code]

        self._rebuild_views_from_raw()

    @Slot(dict, int)
    def _on_api_success(self, data: Dict[str, Any], req_id: int):
        try:
            self.populate_from_response(data)
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Kon response niet verwerken:\n{e}")

    @Slot(str, int)
    def _on_api_error(self, err: str, req_id: int):
        QMessageBox.critical(self, "Fout", f"API-fout:\n{err}")

    # ---------- Rebuild ----------
    def _rebuild_views_from_raw(self):
        self.tabs.clear()
        self.section_frames_view.clear()

        def _make_table(df: pd.DataFrame) -> QWidget:
            w = QWidget()
            lay = QVBoxLayout(w)
            tv = QTableView()
            tv.setModel(PandasModel(df))
            tv.horizontalHeader().setStretchLastSection(True)
            tv.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
            tv.setSortingEnabled(True)
            lay.addWidget(tv)
            return w

        for code in SALES_SECTIONS_ORDERED + PURCHASE_SECTIONS_ORDERED:
            if code in self.section_frames_raw:
                df = apply_schema(self.section_frames_raw[code], code)
                self.section_frames_view[code] = df
                page = _make_table(df)
                title = f"{section_full_label(code)} ({len(df)} rijen)"
                self.tabs.addTab(page, title)

        if not self.section_frames_view:
            QMessageBox.information(self, "Geen data", "Geen secties met documenten gevonden.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DocsWindow()
    w.showMaximized()
    sys.exit(app.exec())
