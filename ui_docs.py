# ui_docs.py
import sys
import os
from typing import Any, Dict, List, Tuple
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

import requests
import pandas as pd
from PySide6.QtCore import (
    Qt, Signal, Slot, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QTimer
)
from PySide6.QtGui import QKeySequence, QShortcut, QIntValidator
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QMessageBox, QTableView, QFileDialog, QGroupBox, QRadioButton,
    QHeaderView, QSizePolicy, QStackedLayout, QFrame, QInputDialog
)

from auth import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT
from ui_docs_schema import apply_schema, set_sort_mode
from ui_labels import col_label, translate_df_columns, section_full_label, ui
import security_docs  # sessie-lock; gebruikt zelfde wachtwoord als BP

requests.packages.urllib3.disable_warnings()  # type: ignore

CONFIGURATION_ID = os.environ.get("DOCS_CONFIGURATION_ID", "4AA8DF")

SALES_SECTIONS_ORDERED: List[str]    = ["OSO", "OSDL", "OSDP", "OSR", "OSI"]
PURCHASE_SECTIONS_ORDERED: List[str] = ["OPO", "OPDL", "OPR", "OPI"]

DATE_FMT_UI   = "%d-%m-%Y"
DATE_FMT_XLSX = "dd-mm-yyyy"
DATE_FMT_CSV  = "%d-%m-%Y"


def date_stamp() -> str:
    return datetime.now().strftime("%Y%m%d")


# ----------- Pandas → Qt Model met correcte sorteerwaarden -----------
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

        # Ruwe waarden voor sorteren (numeriek/datum)
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

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
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
    """
    Parser die de API-lijst omzet naar DataFrame en basisvelden aanvult.
    """
    df = pd.DataFrame(items)

    # Datums
    for col in ("DocDate", "DocDueDate"):
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # CardName fallback
    if "CardName" not in df.columns:
        df["CardName"] = None
    if "Partner" in df.columns:
        df["CardName"] = df["CardName"].fillna(df["Partner"])
    if "Vendor" in df.columns:
        df["CardName"] = df["CardName"].fillna(df["Vendor"])

    # Outstanding
    if "DocTotal" in df.columns and "PaidSum" in df.columns:
        df["Outstanding"] = (df["DocTotal"] - df["PaidSum"]).round(2)

    # OrderCount generiek afleiden
    if "OrderCount" not in df.columns:
        src_counts = [
            "OrderCount", "DeliveryCount", "DownPaymentCount", "ReturnCount",
            "InvoiceCount", "PurchaseOrderCount", "ReceiptCount"
        ]
        found = None
        for c in src_counts:
            if c in df.columns:
                found = c
                break
        df["OrderCount"] = df[found] if found else pd.NA

    # MaandenOud numeriek
    if "MaandenOud" in df.columns:
        df["MaandenOud"] = _coerce_numeric(df["MaandenOud"])

    # Minimum-set aan kolommen garanderen
    for must_have in [
        "DocNum", "CardCode", "CardName", "DocDate", "DocDueDate",
        "DocTotal", "PaidSum", "Outstanding", "OrderCount",
        "MaandenOud", "SalesOwner", "DocOwner", "Buyer"
    ]:
        if must_have not in df.columns:
            df[must_have] = pd.NA

    return df


def pick_excel_engine() -> str | None:
    try:
        import openpyxl  # noqa: F401
        return "openpyxl"
    except Exception:
        try:
            import xlsxwriter  # noqa: F401
            return "xlsxwriter"
        except Exception:
            return None


def downloads_dir() -> str:
    d = os.path.expanduser("~/Downloads")
    if os.path.isdir(d):
        return d
    up = os.environ.get("USERPROFILE")
    if up:
        d2 = os.path.join(up, "Downloads")
        if os.path.isdir(d2):
            return d2
    return os.getcwd()


# ===================== HOOFDVENSTER =====================
class DocsWindow(QWidget):
    api_success = Signal(dict, int)
    api_error = Signal(str, int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Open Sales/Purchase — Documents")
        self.setContentsMargins(8, 8, 8, 8)

        self._exec = ThreadPoolExecutor(max_workers=2)
        self._req_counter = 0

        # Data
        self.section_frames_raw: Dict[str, pd.DataFrame] = {}
        self.section_frames_view: Dict[str, pd.DataFrame] = {}
        self.sum_sales_sections: pd.DataFrame | None = None
        self.sum_purchase_sections: pd.DataFrame | None = None
        self.sum_customers: pd.DataFrame | None = None
        self.sum_docowner: pd.DataFrame | None = None
        self.sum_salesowner: pd.DataFrame | None = None
        self.sum_buyer: pd.DataFrame | None = None

        # ========== STACKED LAYOUT: LOCKED / CONTENT ==========
        root = QVBoxLayout(self)
        root.setSpacing(8)
        self.stack = QStackedLayout()
        root.addLayout(self.stack, 1)

        # ----- LOCKED VIEW -----
        locked = QWidget()
        lyt_lock = QVBoxLayout(locked)
        lyt_lock.setAlignment(Qt.AlignCenter)
        lock_icon = QLabel("🔒")
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setStyleSheet("font-size: 42px;")
        self.lock_msg = QLabel("Deze module is vergrendeld.\nKlik op 'Ontgrendel' en voer het wachtwoord in.")
        self.lock_msg.setAlignment(Qt.AlignCenter)
        self.lock_msg.setStyleSheet("color: #555;")
        btn_unlock = QPushButton("Ontgrendel")
        btn_unlock.setFixedWidth(160)
        btn_unlock.clicked.connect(self._unlock_prompt)
        lyt_lock.addWidget(lock_icon)
        lyt_lock.addSpacing(8)
        lyt_lock.addWidget(self.lock_msg)
        lyt_lock.addSpacing(12)
        lyt_lock.addWidget(btn_unlock, alignment=Qt.AlignCenter)

        # ----- CONTENT VIEW -----
        content = QWidget()
        content_root = QVBoxLayout(content)
        content_root.setSpacing(8)
        content_root.setContentsMargins(0, 0, 0, 0)

        # ---------- Boven: Aantal + Export-bereik ----------
        row_top = QHBoxLayout()
        row_top.setSpacing(12)

        key_group = QGroupBox(ui("group_count"))
        key_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        g = QHBoxLayout(key_group)
        g.setSpacing(10)
        self.rb_6 = QRadioButton("6")
        self.rb_other = QRadioButton("Anders:")
        self.key_custom = QLineEdit()
        self.key_custom.setPlaceholderText("voer eigen aantal in (niet leeg)")
        self.key_custom.setEnabled(False)
        self.key_custom.setValidator(QIntValidator(0, 999999, self))
        self.key_custom.textEdited.connect(self._on_key_custom_edited)
        self.key_custom.returnPressed.connect(self.fetch_api)
        self.rb_6.setChecked(True)

        def on_rb_changed():
            self.key_custom.setEnabled(self.rb_other.isChecked())

        self.rb_6.toggled.connect(on_rb_changed)
        self.rb_other.toggled.connect(on_rb_changed)
        g.addWidget(self.rb_6)
        g.addWidget(self.rb_other)
        g.addWidget(self.key_custom, 1)

        range_group = QGroupBox(ui("group_export"))
        range_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        rg = QHBoxLayout(range_group)
        rg.setSpacing(12)
        self.rb_range_current = QRadioButton(ui("rb_current"))
        self.rb_range_all = QRadioButton(ui("rb_all"))
        self.rb_range_sales = QRadioButton(ui("rb_sales"))
        self.rb_range_purchase = QRadioButton(ui("rb_purchase"))
        self.rb_range_current.setChecked(True)
        for w in (
            self.rb_range_current,
            self.rb_range_all,
            self.rb_range_sales,
            self.rb_range_purchase,
        ):
            rg.addWidget(w)

        row_top.addWidget(key_group)
        row_top.addWidget(range_group)
        content_root.addLayout(row_top)

        # ---------- Opties — groepering/sortering ----------
        options_group = QGroupBox(ui("group_options"))
        og = QHBoxLayout(options_group)
        og.setSpacing(12)
        self.rb_group_cardname = QRadioButton(ui("opt_cardname"))
        self.rb_group_cardcode = QRadioButton(ui("opt_cardcode"))
        self.rb_group_docowner = QRadioButton(ui("opt_docowner"))
        self.rb_group_salesowner = QRadioButton(ui("opt_salesowner"))
        self.rb_group_maand = QRadioButton(ui("opt_maanden"))
        self.rb_group_cardname.setChecked(True)

        for w in (
            self.rb_group_cardname,
            self.rb_group_cardcode,
            self.rb_group_docowner,
            self.rb_group_salesowner,
            self.rb_group_maand,
        ):
            og.addWidget(w)
        content_root.addWidget(options_group)

        # ---------- Actieknoppen ----------
        actions = QHBoxLayout()
        actions.setSpacing(10)
        self.btn_fetch = QPushButton(ui("btn_fetch"))
        self.btn_export = QPushButton(ui("btn_export"))
        self.btn_export_all = QPushButton(ui("btn_export_all"))
        for b in (self.btn_fetch, self.btn_export, self.btn_export_all):
            b.setStyleSheet("font-weight:600; padding:8px 14px;")
        self.btn_fetch.setDefault(True)
        self.btn_fetch.clicked.connect(self.fetch_api)
        self.btn_export.clicked.connect(self.export_by_range)
        self.btn_export_all.clicked.connect(self.export_all)
        actions.addWidget(self.btn_fetch)
        actions.addWidget(self.btn_export)
        actions.addWidget(self.btn_export_all)
        actions.addStretch(1)
        content_root.addLayout(actions)

        # ---------- Tabs ----------
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabBar::tab:disabled { color: #666; font-weight: 700; }"
        )
        content_root.addWidget(self.tabs, 1)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.fetch_api)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)

        # Optie events
        self.rb_group_cardname.toggled.connect(self._on_grouping_changed)
        self.rb_group_cardcode.toggled.connect(self._on_grouping_changed)
        self.rb_group_docowner.toggled.connect(self._on_grouping_changed)
        self.rb_group_salesowner.toggled.connect(self._on_grouping_changed)
        self.rb_group_maand.toggled.connect(self._on_grouping_changed)

        # Stack
        self.stack.addWidget(locked)   # index 0
        self.stack.addWidget(content)  # index 1

        # Tonen volgens lock-status
        if security_docs.is_unlocked():
            self._show_content()
        else:
            self._show_locked()

        # Signals
        self.api_success.connect(self._on_api_success)
        self.api_error.connect(self._on_api_error)

    # ---------- Lock helpers ----------
    def _show_locked(self):
        self.stack.setCurrentIndex(0)

    def _show_content(self):
        security_docs.unlock()
        self.stack.setCurrentIndex(1)

    def _unlock_prompt(self):
        # Dev-bypass
        if security_docs.lock_disabled():
            self._show_content()
            return

        expected = (security_docs.password() or "").strip()
        if not expected:
            QMessageBox.warning(self, "Configuratie", "Er is geen wachtwoord geconfigureerd (DOCS_PASSWORD of via BP).")
            return

        pw, ok = QInputDialog.getText(
            self, "Ontgrendel Documenten",
            "Wachtwoord:", QLineEdit.EchoMode.Password  # type: ignore[attr-defined]
        )
        if not ok:
            return
        if pw.strip() == expected:
            self._show_content()
        else:
            QMessageBox.warning(self, "Onjuist wachtwoord", "Het wachtwoord is onjuist.")

    def showEvent(self, e):
        super().showEvent(e)
        # Bij openen meteen prompten indien nog vergrendeld
        if not security_docs.is_unlocked():
            QTimer.singleShot(0, self._unlock_prompt)

    # ---------- Groepeer/sorteer modus ----------
    def _current_group_mode(self) -> str:
        if self.rb_group_cardname.isChecked():
            return "cardname"
        if self.rb_group_cardcode.isChecked():
            return "cardcode"
        if self.rb_group_docowner.isChecked():
            return "docowner"
        if self.rb_group_salesowner.isChecked():
            return "salesowner"
        if self.rb_group_maand.isChecked():
            return "maandenoud"
        return "cardname"  # fallback

    def _apply_grouping_mode(self):
        set_sort_mode(self._current_group_mode())
        self._rebuild_views_from_raw()

    # ---------- Key/Aantal helpers ----------
    def _current_key_value(self) -> str:
        """
        - Wat in het veld staat (cijfer) heeft voorrang
        - Leeg veld + '6' geselecteerd => "6"
        - 'Anders' + leeg veld => fout
        """
        txt = self.key_custom.text().strip()
        if txt:
            return txt
        if self.rb_6.isChecked():
            return "6"
        if self.rb_other.isChecked():
            raise ValueError("Aantal mag niet leeg zijn.")
        return "6"

    @Slot(str)
    def _on_key_custom_edited(self, text: str):
        text = (text or "").strip()
        if text:
            if not self.rb_other.isChecked():
                self.rb_other.setChecked(True)
        else:
            if not self.rb_6.isChecked():
                self.rb_6.setChecked(True)

    # ---------- API helpers ----------
    def _build_payload(self) -> Dict[str, Any]:
        # Lege Key is niet toegestaan door de API
        return {"ConfigurationID": CONFIGURATION_ID, "Key": self._current_key_value()}

    @staticmethod
    def _post(url: str, headers: Dict[str, str], payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("IsError"):
            raise RuntimeError(data.get("ErrorMessage") or "API gaf een fout terug.")
        return data

    # ---------- Autosize helper ----------
    def _auto_size_table(self, tv: QTableView, max_section: int = 520):
        hh = tv.horizontalHeader()
        tv.resizeColumnsToContents()
        model = tv.model()
        if model is None:
            return
        try:
            cols = model.columnCount()
        except Exception:
            return
        for c in range(cols):
            w = hh.sectionSize(c)
            if w > max_section:
                hh.resizeSection(c, max_section)

    # ---------- TableView ----------
    def _make_table_view(self, df: pd.DataFrame, *, sortable: bool) -> QTableView:
        df_view = translate_df_columns(df)
        src_model = PandasModel(df_view)

        if sortable:
            proxy = QSortFilterProxyModel(self)
            proxy.setSourceModel(src_model)
            proxy.setSortRole(int(Qt.ItemDataRole.UserRole))
            proxy.setDynamicSortFilter(True)
            model = proxy
        else:
            model = src_model

        tv = QTableView()
        tv.setModel(model)
        tv.setAlternatingRowColors(True)
        tv.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        if sortable:
            tv.setSortingEnabled(True)
            tv.horizontalHeader().setSortIndicatorShown(True)
        else:
            tv.setSortingEnabled(False)
            tv.horizontalHeader().setSortIndicatorShown(False)

        QTimer.singleShot(0, lambda tv=tv: self._auto_size_table(tv))
        if sortable:
            tv.horizontalHeader().sortIndicatorChanged.connect(
                lambda *_args, tv=tv: self._auto_size_table(tv)
            )
        m = tv.model()
        for sig_name in ("layoutChanged", "modelReset", "rowsInserted", "columnsInserted"):
            sig = getattr(m, sig_name, None)
            if sig is not None:
                sig.connect(lambda *a, tv=tv: self._auto_size_table(tv))
        return tv

    # ---------- Visuele separators ----------
    def _add_separator_tab(self, label: str):
        sep = QWidget()
        self.tabs.addTab(sep, label)
        idx = self.tabs.indexOf(sep)
        self.tabs.setTabEnabled(idx, False)

    # ---------- Tabselectie (OSO na ophalen) ----------
    def _select_tab_by_label(self, label: str) -> bool:
        for i in range(self.tabs.count()):
            if self.tabs.tabText(i) == label and self.tabs.isTabEnabled(i):
                self.tabs.setCurrentIndex(i)
                return True
        return False

    def _select_initial_tab(self):
        if self._select_tab_by_label("OSO"):
            return
        for code in SALES_SECTIONS_ORDERED:
            if self._select_tab_by_label(code):
                return
        if self._select_tab_by_label(ui("tab_summary")):
            return
        for i in range(self.tabs.count()):
            if self.tabs.isTabEnabled(i) and not self.tabs.tabText(i).startswith("—"):
                self.tabs.setCurrentIndex(i)
                return

    # ===================== Ophalen =====================
    def fetch_api(self):
        if not security_docs.is_unlocked():
            self._unlock_prompt()
            if not security_docs.is_unlocked():
                return

        env = API_ENVIRONMENTS[ENVIRONMENT]
        base = env["base_url"].rstrip("/")
        url = f"{base}/api/datarequest"
        headers = get_auth_header()
        headers.setdefault("Content-Type", "application/json")

        try:
            payload = self._build_payload()
        except Exception as e:
            QMessageBox.warning(self, "Input fout", str(e))
            return

        self.btn_fetch.setEnabled(False)
        self.setCursor(Qt.WaitCursor)
        self._req_counter += 1
        req_id = self._req_counter

        def _worker():
            try:
                data = DocsWindow._post(url, headers, payload)
                self.api_success.emit(data, req_id)
            except Exception as e:
                self.api_error.emit(str(e), req_id)

        ThreadPoolExecutor(max_workers=1).submit(_worker)

    # ---------- Populate ----------
    def _clear_tabs(self):
        self.tabs.clear()
        self.section_frames_raw.clear()
        self.section_frames_view.clear()
        self.sum_sales_sections = None
        self.sum_purchase_sections = None
        self.sum_customers = None
        self.sum_docowner = None
        self.sum_salesowner = None
        self.sum_buyer = None

    def _add_section_tab(self, code: str, df_view: pd.DataFrame):
        page = QWidget()
        v = QVBoxLayout(page)
        title = section_full_label(code)

        total = df_view.get("DocTotal", pd.Series(dtype=float)).sum() if "DocTotal" in df_view.columns else 0.0
        outstanding = (
            df_view.get("Outstanding", pd.Series(dtype=float)).sum()
            if "Outstanding" in df_view.columns
            else 0.0
        )

        hdr = QLabel(
            f"<b>{title}</b> — {len(df_view)} rijen — Totaal: {total:,.2f} — Openstaand: {outstanding:,.2f}"
        )
        hdr.setTextFormat(Qt.TextFormat.RichText)
        v.addWidget(hdr)

        tv = self._make_table_view(df_view, sortable=False)
        v.addWidget(tv)
        self.tabs.addTab(page, code)

    # ------ Summary builders ------
    def _build_sections_summary(self, codes: List[str]) -> pd.DataFrame:
        rows = []
        for code in codes:
            df = self.section_frames_raw.get(code)
            if df is None or df.empty:
                continue
            total = df["DocTotal"].sum() if "DocTotal" in df.columns else 0.0
            outstanding = df["Outstanding"].sum() if "Outstanding" in df.columns else 0.0
            earliest = df["DocDueDate"].min() if "DocDueDate" in df.columns else pd.NaT
            latest = df["DocDueDate"].max() if "DocDueDate" in df.columns else pd.NaT
            rows.append(
                {
                    "Section": code,
                    "Section (decoded)": section_full_label(code),
                    "Count": int(len(df)),
                    "Total DocTotal": round(float(total), 2),
                    "Total Outstanding": round(float(outstanding), 2),
                    "Earliest Due": earliest,
                    "Latest Due": latest,
                }
            )
        return translate_df_columns(pd.DataFrame(rows))

    def _build_summary_by_customer(self) -> pd.DataFrame:
        sales_codes = [c for c in SALES_SECTIONS_ORDERED if c in self.section_frames_raw]
        purch_codes = [c for c in PURCHASE_SECTIONS_ORDERED if c in self.section_frames_raw]

        def _concat(codes: List[str]) -> pd.DataFrame:
            frames = [
                self.section_frames_raw[c][["CardCode", "CardName"]]
                for c in codes
                if "CardCode" in self.section_frames_raw[c].columns
            ]
            return (
                pd.concat(frames, ignore_index=True)
                if frames
                else pd.DataFrame(columns=["CardCode", "CardName"])
            )

        sales = _concat(sales_codes)
        purch = _concat(purch_codes)

        sales_count = (
            sales.groupby(["CardCode", "CardName"], dropna=False)
            .size()
            .reset_index(name="SalesOpen")
        )
        purch_count = (
            purch.groupby(["CardCode", "CardName"], dropna=False)
            .size()
            .reset_index(name="PurchaseOpen")
        )

        df = pd.merge(sales_count, purch_count, on=["CardCode", "CardName"], how="outer").fillna(0)
        df["SalesOpen"] = pd.to_numeric(df["SalesOpen"], errors="coerce").fillna(0).astype(int)
        df["PurchaseOpen"] = pd.to_numeric(df["PurchaseOpen"], errors="coerce").fillna(0).astype(int)
        return translate_df_columns(df.sort_values(["CardCode", "CardName"]).reset_index(drop=True))

    def _build_summary_group(self, field: str, codes: List[str]) -> pd.DataFrame:
        frames = []
        for c in codes:
            df = self.section_frames_raw.get(c)
            if df is not None and field in df.columns:
                frames.append(df[[field]])
        if not frames:
            return translate_df_columns(pd.DataFrame(columns=[field, "Count"]))
        merged = pd.concat(frames, ignore_index=True)
        out = merged.groupby(field, dropna=False).size().reset_index(name="Count")
        out["Count"] = pd.to_numeric(out["Count"], errors="coerce").fillna(0).astype(int)
        return translate_df_columns(out.sort_values([field]).reset_index(drop=True))

    def _add_summary_tab(self):
        page = QWidget()
        v = QVBoxLayout(page)
        v.addWidget(QLabel(f"<b>{ui('tab_summary')}</b>"))

        sub = QTabWidget()

        self.sum_sales_sections = self._build_sections_summary(
            [c for c in SALES_SECTIONS_ORDERED if c in self.section_frames_raw]
        )
        self.sum_customers = self._build_summary_by_customer()
        self.sum_purchase_sections = self._build_sections_summary(
            [c for c in PURCHASE_SECTIONS_ORDERED if c in self.section_frames_raw]
        )
        self.sum_docowner = self._build_summary_group(
            "DocOwner", [c for c in (SALES_SECTIONS_ORDERED + PURCHASE_SECTIONS_ORDERED) if c in self.section_frames_raw]
        )
        self.sum_salesowner = self._build_summary_group(
            "SalesOwner", [c for c in SALES_SECTIONS_ORDERED if c in self.section_frames_raw]
        )
        self.sum_buyer = self._build_summary_group(
            "Buyer", [c for c in PURCHASE_SECTIONS_ORDERED if c in self.section_frames_raw]
        )

        def _add_df_tab(df: pd.DataFrame, name: str):
            sub_page = QWidget()
            sv = QVBoxLayout(sub_page)
            tv = self._make_table_view(df, sortable=True)
            sv.addWidget(tv)
            sub.addTab(sub_page, name)

        _add_df_tab(self.sum_sales_sections, ui("sub_sales_sections"))
        _add_df_tab(self.sum_customers, ui("sub_customers"))
        _add_df_tab(self.sum_purchase_sections, ui("sub_purchase_sections"))
        _add_df_tab(self.sum_docowner, ui("sub_docowner"))
        _add_df_tab(self.sum_salesowner, ui("sub_salesowner"))
        _add_df_tab(self.sum_buyer, ui("sub_buyer"))

        v.addWidget(sub)
        self.tabs.addTab(page, ui("tab_summary"))

    def _rebuild_views_from_raw(self):
        self.tabs.clear()
        self.section_frames_view.clear()

        # Verkoop
        self._add_separator_tab(ui("sep_sales"))
        for code in SALES_SECTIONS_ORDERED:
            if code in self.section_frames_raw:
                view = apply_schema(self.section_frames_raw[code], code)
                self.section_frames_view[code] = view
                self._add_section_tab(code, view)

        # Samenvatting
        self._add_separator_tab(ui("sep_summary"))
        self._add_summary_tab()

        # Aankoop
        self._add_separator_tab(ui("sep_purchase"))
        for code in PURCHASE_SECTIONS_ORDERED:
            if code in self.section_frames_raw:
                view = apply_schema(self.section_frames_raw[code], code)
                self.section_frames_view[code] = view
                self._add_section_tab(code, view)

        # Automatisch OSO selecteren (of fallback)
        self._select_initial_tab()

    def populate_from_response(self, data: Dict[str, Any]):
        self.tabs.clear()
        self.section_frames_raw.clear()
        self.section_frames_view.clear()
        self.sum_sales_sections = self.sum_purchase_sections = None
        self.sum_customers = self.sum_docowner = self.sum_salesowner = self.sum_buyer = None

        root = data.get("Data") if isinstance(data, dict) else None
        if not isinstance(root, dict):
            QMessageBox.warning(
                self,
                "Onverwachte structuur",
                "Verwachte structuur: { 'Data': { 'OSO': [...], ... } }",
            )
            return

        tmp_raw: Dict[str, pd.DataFrame] = {}
        for code, rows in root.items():
            if not isinstance(rows, list) or not rows:
                continue
            tmp_raw[code] = parse_section(rows, code)

        # Pas de huidige groeperingsmodus toe (default = cardname)
        set_sort_mode(self._current_group_mode())

        # Respecteer tab-volgorde
        for code in (SALES_SECTIONS_ORDERED + PURCHASE_SECTIONS_ORDERED):
            if code in tmp_raw:
                self.section_frames_raw[code] = tmp_raw[code]

        self._rebuild_views_from_raw()

    # ---------- Export helpers ----------
    def _export_df_excel(self, df: pd.DataFrame, path: str, sheet_name: str):
        engine = pick_excel_engine()
        if engine is None:
            raise RuntimeError(
                "Geen Excel-engine gevonden. Installeer 'openpyxl' of 'XlsxWriter', of kies CSV."
            )
        with pd.ExcelWriter(path, engine=engine, datetime_format=DATE_FMT_XLSX) as writer:
            translate_df_columns(df).to_excel(writer, index=False, sheet_name=sheet_name[:31])

    def _export_multiple(self, sheets: List[Tuple[str, pd.DataFrame]], path: str):
        engine = pick_excel_engine()
        if engine is None:
            raise RuntimeError(
                "Geen Excel-engine gevonden. Installeer 'openpyxl' of 'XlsxWriter'."
            )
        with pd.ExcelWriter(path, engine=engine, datetime_format=DATE_FMT_XLSX) as writer:
            for name, df in sheets:
                translate_df_columns(df).to_excel(writer, index=False, sheet_name=name[:31])

    # ---------- Export volgens bereik ----------
    def export_by_range(self):
        if not security_docs.is_unlocked():
            self._unlock_prompt()
            if not security_docs.is_unlocked():
                return

        if not self.section_frames_view:
            QMessageBox.information(self, "Geen data", "Er is nog geen data geladen.")
            return

        stamp = date_stamp()
        idx = self.tabs.currentIndex()
        if idx < 0:
            QMessageBox.information(self, "Geen tab", "Er is geen tab geselecteerd.")
            return

        label = self.tabs.tabText(idx)
        if label.startswith("—"):
            QMessageBox.information(self, "Kies tab", "Selecteer eerst een echte datatab.")
            return

        # Huidige tab
        if self.rb_range_current.isChecked():
            if label == ui("tab_summary"):
                sheets: List[Tuple[str, pd.DataFrame]] = []
                if self.sum_sales_sections is not None:
                    sheets.append(("Summary_Secties_Sales", self.sum_sales_sections))
                if self.sum_customers is not None:
                    sheets.append(("Summary_Klanten", self.sum_customers))
                if self.sum_purchase_sections is not None:
                    sheets.append(("Summary_Secties_Purchase", self.sum_purchase_sections))
                if self.sum_docowner is not None:
                    sheets.append(("Summary_DocOwner", self.sum_docowner))
                if self.sum_salesowner is not None:
                    sheets.append(("Summary_SalesOwner", self.sum_salesowner))
                if self.sum_buyer is not None:
                    sheets.append(("Summary_Buyer", self.sum_buyer))

                default_name = f"Summary_{stamp}.xlsx"
                default_path = os.path.join(downloads_dir(), default_name)
                path, _ = QFileDialog.getSaveFileName(self, "Exporteer Summary", default_path, "Excel (*.xlsx)")
                if not path:
                    return
                if not path.lower().endswith(".xlsx"):
                    path += ".xlsx"
                try:
                    self._export_multiple(sheets, path)
                    QMessageBox.information(self, "Succes", f"Export voltooid:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "Fout", f"Export mislukt:\n{e}")
                return
            else:
                df = self.section_frames_view.get(label)
                if df is None:
                    QMessageBox.warning(self, "Onbekend", f"Geen data voor '{label}'.")
                    return
                default_name = f"{label}_{stamp}.xlsx"
                default_path = os.path.join(downloads_dir(), default_name)
                path, sel_filter = QFileDialog.getSaveFileName(
                    self, f"Exporteer '{label}'", default_path, "Excel (*.xlsx);;CSV (*.csv)"
                )
                if not path:
                    return
                try:
                    if path.lower().endswith(".csv"):
                        translate_df_columns(df).to_csv(path, index=False, date_format=DATE_FMT_CSV)
                    else:
                        if not path.lower().endswith(".xlsx"):
                            path += ".xlsx"
                        self._export_df_excel(df, path, label)
                    QMessageBox.information(self, "Succes", f"Geselecteerde export voltooid:\n{path}")
                except Exception as e:
                    QMessageBox.critical(self, "Fout", f"Export mislukt:\n{e}")
                return

        # Multi-sheet export (Alle / Sales / Purchase)
        if self.rb_range_all.isChecked():
            codes = [c for c in (SALES_SECTIONS_ORDERED + PURCHASE_SECTIONS_ORDERED) if c in self.section_frames_view]
            default_name = f"OpenDocuments_{stamp}.xlsx"
        elif self.rb_range_sales.isChecked():
            codes = [c for c in SALES_SECTIONS_ORDERED if c in self.section_frames_view]
            default_name = f"OpenSales_{stamp}.xlsx"
        else:
            codes = [c for c in PURCHASE_SECTIONS_ORDERED if c in self.section_frames_view]
            default_name = f"OpenAankoop_{stamp}.xlsx"

        if not codes:
            QMessageBox.information(self, "Geen secties", "Er zijn geen secties voor dit bereik.")
            return

        # Sheets samenstellen: Summary + geselecteerde secties
        sheets: List[Tuple[str, pd.DataFrame]] = []
        sheets.append(
            (
                "Summary_Secties_Sales",
                self._build_sections_summary([c for c in SALES_SECTIONS_ORDERED if c in codes]),
            )
        )
        sheets.append(("Summary_Klanten", self._build_summary_by_customer()))
        sheets.append(
            (
                "Summary_Secties_Purchase",
                self._build_sections_summary([c for c in PURCHASE_SECTIONS_ORDERED if c in codes]),
            )
        )
        sheets.append(("Summary_DocOwner", self._build_summary_group("DocOwner", codes)))
        sheets.append(
            (
                "Summary_SalesOwner",
                self._build_summary_group("SalesOwner", [c for c in SALES_SECTIONS_ORDERED if c in codes]),
            )
        )
        sheets.append(
            (
                "Summary_Buyer",
                self._build_summary_group("Buyer", [c for c in PURCHASE_SECTIONS_ORDERED if c in codes]),
            )
        )

        for code in codes:
            sheets.append((code, self.section_frames_view[code]))

        default_path = os.path.join(downloads_dir(), default_name)
        path, _ = QFileDialog.getSaveFileName(self, "Exporteer", default_path, "Excel (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            self._export_multiple(sheets, path)
            QMessageBox.information(self, "Succes", f"Export voltooid:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Export mislukt:\n{e}")

    def export_all(self):
        if not security_docs.is_unlocked():
            self._unlock_prompt()
            if not security_docs.is_unlocked():
                return

        if not self.section_frames_view:
            QMessageBox.information(self, "Geen data", "Er is nog geen data geladen.")
            return

        stamp = date_stamp()
        codes = [c for c in (SALES_SECTIONS_ORDERED + PURCHASE_SECTIONS_ORDERED) if c in self.section_frames_view]

        sheets: List[Tuple[str, pd.DataFrame]] = []
        sheets.append(
            (
                "Summary_Secties_Sales",
                self._build_sections_summary([c for c in SALES_SECTIONS_ORDERED if c in codes]),
            )
        )
        sheets.append(("Summary_Klanten", self._build_summary_by_customer()))
        sheets.append(
            (
                "Summary_Secties_Purchase",
                self._build_sections_summary([c for c in PURCHASE_SECTIONS_ORDERED if c in codes]),
            )
        )
        sheets.append(("Summary_DocOwner", self._build_summary_group("DocOwner", codes)))
        sheets.append(
            (
                "Summary_SalesOwner",
                self._build_summary_group("SalesOwner", [c for c in SALES_SECTIONS_ORDERED if c in codes]),
            )
        )
        sheets.append(
            (
                "Summary_Buyer",
                self._build_summary_group("Buyer", [c for c in PURCHASE_SECTIONS_ORDERED if c in codes]),
            )
        )

        for code in codes:
            sheets.append((code, self.section_frames_view[code]))

        default_name = f"OpenDocuments_All_{stamp}.xlsx"
        default_path = os.path.join(downloads_dir(), default_name)
        path, _ = QFileDialog.getSaveFileName(self, "Exporteer alles", default_path, "Excel (*.xlsx)")
        if not path:
            return
        if not path.lower().endswith(".xlsx"):
            path += ".xlsx"
        try:
            self._export_multiple(sheets, path)
            QMessageBox.information(self, "Succes", f"Export voltooid:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Export mislukt:\n{e}")

    # ---------- Slots ----------
    @Slot()
    def _on_grouping_changed(self):
        if self.section_frames_raw:
            self._apply_grouping_mode()

    @Slot(dict, int)
    def _on_api_success(self, data: dict, req_id: int):
        if req_id != self._req_counter:
            return
        self.btn_fetch.setEnabled(True)
        self.unsetCursor()
        try:
            self.populate_from_response(data)
        except Exception as e:
            QMessageBox.critical(self, "Fout", f"Kon response niet verwerken:\n{e}")

    @Slot(str, int)
    def _on_api_error(self, msg: str, req_id: int):
        if req_id != self._req_counter:
            return
        self.btn_fetch.setEnabled(True)
        self.unsetCursor()
        QMessageBox.critical(self, "Ophalen mislukt", msg)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DocsWindow()
    w.showMaximized()
    sys.exit(app.exec())
