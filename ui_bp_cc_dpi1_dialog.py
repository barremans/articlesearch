# ui_bp_cc_dpi1_dialog.py
from typing import Any, Iterable, Mapping
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPlainTextEdit, QPushButton, QWidget
)

def _normalize(s: str) -> str:
    return "".join(ch for ch in str(s).lower() if ch.isalnum())

class DownPaymentLinesDialog(QDialog):
    """
    Pop-up voor ODPI (voorschotten) lijninformatie (DPI1).
    Boven: tabel met lijnen
    Onder: groot tekstvak voor FreeTxt/LineMemo
    """
    COLS = [
        "LineNum", "Dscription", "Quantity", "Price",
        "LineTotal", "TaxCode", "VatSum", "TotalInclVAT", "WhsCode"
    ]
    ALIASES: Mapping[str, list[str]] = {
        "LineNum": ["LineNum", "LineNo", "Line"],
        "Dscription": ["Dscription", "Description", "Descr", "ItemName"],
        "Quantity": ["Quantity", "Qty", "QuantityBase"],
        "Price": ["Price", "UnitPrice", "PriceExVAT", "PriceAfVAT"],
        "LineTotal": ["LineTotal", "LineTotalExclVAT", "TotalExclVAT", "OpenAmount_ExclVAT"],
        "TaxCode": ["TaxCode", "VatGroup", "TaxGrp"],
        "VatSum": ["VatSum", "VAT_Amount", "TaxAmount"],
        "TotalInclVAT": ["TotalInclVAT", "LineTotalInclVAT", "TotalInclVat", "OpenAmount_InclVAT"],
        "WhsCode": ["WhsCode", "Warehouse"],
    }

    def __init__(self, parent=None, *, dpi_header: dict | None = None, lines: Iterable[dict] = ()):
        super().__init__(parent)
        self.setWindowTitle(self._mk_title(dpi_header))
        self.resize(1000, 600)
        self._lines = list(lines or [])

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        if isinstance(dpi_header, dict):
            root.addWidget(self._make_header(dpi_header))

        self.table = QTableWidget(0, 0)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 1)

        self.free_txt = QPlainTextEdit()
        self.free_txt.setReadOnly(True)
        self.free_txt.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.free_txt.setPlaceholderText("Vrije tekst / memo van geselecteerde lijn…")
        root.addWidget(self.free_txt, 1)

        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_close = QPushButton("Sluiten")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)

        self._render_lines()
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        if self.table.rowCount() > 0:
            self.table.selectRow(0)
            self._on_selection_changed()

    # ---- intern ----
    def _mk_title(self, hdr: dict | None) -> str:
        if not isinstance(hdr, dict):
            return "Voorschotlijnen"
        num = hdr.get("DocNum", "") or hdr.get("DownPaymentNum", "")
        date = hdr.get("DocDate", "")
        code = hdr.get("CardCode", ""); name = hdr.get("CardName", "")
        suffix = " | ".join([s for s in [f"ODPI {num}" if num else "", str(date) if date else "", code, name] if s])
        return f"Voorschotlijnen — {suffix}" if suffix else "Voorschotlijnen"

    def _make_header(self, hdr: dict) -> QWidget:
        w = QWidget(); l = QHBoxLayout(w); l.setContentsMargins(0,0,0,0)
        left = QLabel(f"<b>DocNum:</b> {hdr.get('DocNum','-')} &nbsp;&nbsp; <b>DocDate:</b> {hdr.get('DocDate','-')}")
        right = QLabel(f"<b>Partner:</b> {hdr.get('CardCode','-')} — {hdr.get('CardName','-')}")
        l.addWidget(left); l.addStretch(1); l.addWidget(right); return w

    def _render_lines(self):
        rows = self._lines
        if not rows:
            self.table.setColumnCount(1); self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setRowCount(1); self.table.setItem(0,0,QTableWidgetItem("Geen lijnen gevonden.")); return

        all_keys = set(); [all_keys.update(r.keys()) for r in rows]
        norm2actual = {_normalize(k): k for k in all_keys}
        col_order, actual_map = [], {}
        for label in self.COLS:
            found = None
            for cand in self.ALIASES.get(label, [label]):
                nk = _normalize(cand)
                if nk in norm2actual: found = norm2actual[nk]; break
            if found: col_order.append(label); actual_map[label] = found

        if not col_order:
            keys = list(rows[0].keys())
            self.table.setColumnCount(len(keys)); self.table.setHorizontalHeaderLabels([str(k) for k in keys])
            self.table.setRowCount(len(rows))
            for r, row in enumerate(rows):
                for c, key in enumerate(keys):
                    val = row.get(key, "")
                    it = QTableWidgetItem("" if val is None else str(val))
                    if isinstance(val, (int, float)): it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(r, c, it)
            self.table.resizeColumnsToContents(); return

        self.table.setColumnCount(len(col_order)); self.table.setHorizontalHeaderLabels(col_order)
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, label in enumerate(col_order):
                key = actual_map[label]; val = row.get(key, "")
                it = QTableWidgetItem("" if val is None else str(val))
                if isinstance(val, (int,float)) or (isinstance(val,str) and self._looks_numeric(val)):
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, c, it)
        self.table.resizeColumnsToContents(); self.table.horizontalHeader().setStretchLastSection(True)

    def _on_selection_changed(self):
        row = self.table.currentRow(); txt = ""
        if 0 <= row < len(self._lines):
            ln = self._lines[row]
            txt = ln.get("LineMemo") or ln.get("FreeTxt") or ln.get("FreeText") or ln.get("Dscription") or ""
        self.free_txt.setPlainText(str(txt))

    @staticmethod
    def _looks_numeric(val: Any) -> bool:
        if isinstance(val, (int, float)): return True
        if isinstance(val, str):
            s = val.strip().replace(" ", "").replace(".", "").replace(",", "")
            return s.replace("-", "", 1).isdigit()
        return False
