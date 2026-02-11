# ui_bp_cc_ordrl_dialog.py
# v1.1.0 - dynamische kolomlabels / vertalingen
from typing import Any, Iterable, Mapping
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextOption
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QPlainTextEdit, QPushButton, QWidget
)

# Importeer algemene vertalingen (optioneel)
from ui_docs_schema import TRANSLATIONS as DOC_TRANSLATIONS


def _normalize(s: str) -> str:
    """Helper om kolomnamen case-insensitive te vergelijken."""
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


class OrderLinesDialog(QDialog):
    """
    Pop-up om ORDRL (orderlijnen) te tonen.
    - Boven: tabel met lijnen
    - Onder: FreeTxt van de (laatst) geselecteerde lijn in een groot tekstvlak
    """

    # Kolommen die we standaard tonen
    COLS = [
        "LineNum", "ItemCode", "Dscription", "OpenQty", "Price",
        "OpenAmount_ExclVAT", "VAT_Amount", "OpenAmount_InclVAT",
        "Currency", "U_TRI_origitem"
    ]

    # Alternatieve veldnamen (zoals uit SAP of database)
    ALIASES: Mapping[str, list[str]] = {
        "LineNum": ["LineNum", "LineNo", "Line"],
        "ItemCode": ["ItemCode", "Item", "Code"],
        "Dscription": ["Dscription", "Description", "Descr", "ItemName"],
        "OpenQty": ["OpenQty", "OpenQuantity", "Quantity", "OpenQtyBase"],
        "Price": ["Price", "UnitPrice", "PriceAfVAT", "PriceExVAT"],
        "OpenAmount_ExclVAT": ["OpenAmount_ExclVAT", "OpenAmountExclVAT", "LineTotalExclVAT", "LineTotal"],
        "VAT_Amount": ["VAT_Amount", "VATAmount", "TaxAmount"],
        "OpenAmount_InclVAT": ["OpenAmount_InclVAT", "OpenAmountInclVAT", "LineTotalInclVAT"],
        "Currency": ["Currency", "Curr"],
        "U_TRI_origitem": ["U_TRI_origitem", "OrigItem", "OriginalItem"],
    }

    # Lokale vertalingen / labels
    TRANSLATIONS = {
        "LineNum": "Regelnummer",
        "ItemCode": "Artikelcode",
        "Dscription": "Omschrijving",
        "OpenQty": "Open hoeveelheid",
        "Price": "Prijs per eenheid",
        "OpenAmount_ExclVAT": "Bedrag excl. btw",
        "VAT_Amount": "Btw-bedrag",
        "OpenAmount_InclVAT": "Bedrag incl. btw",
        "Currency": "Valuta",
        "U_TRI_origitem": "Origineel artikel",
    }

    def __init__(self, parent=None, *, order_header: dict | None = None, lines: Iterable[dict] = (), custom_labels: dict[str, str] | None = None):
        """
        custom_labels: optioneel dict met aangepaste vertalingen, bv.
            {"LineNum": "Regel", "ItemCode": "Code"}
        """
        super().__init__(parent)
        self.setWindowTitle(self._mk_title(order_header))
        self.resize(1000, 600)
        self._lines = list(lines or [])

        # Dynamische labels (kan runtime worden aangepast)
        self._labels = dict(self.TRANSLATIONS)
        if custom_labels:
            self._labels.update(custom_labels)
        self._labels.update(DOC_TRANSLATIONS)  # fallback uit ui_docs_schema

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # Header bovenaan
        if isinstance(order_header, dict):
            head = self._make_header(order_header)
            if head:
                root.addWidget(head)

        # Tabel
        self.table = QTableWidget(0, 0)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        root.addWidget(self.table, 1)

        # Vrije tekstveld
        self.free_txt = QPlainTextEdit()
        self.free_txt.setReadOnly(True)
        self.free_txt.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        self.free_txt.setPlaceholderText("Vrije tekst van geselecteerde lijn…")
        root.addWidget(self.free_txt, 1)

        # Sluitknop
        btn_row = QHBoxLayout()
        btn_row.addStretch(1)
        btn_close = QPushButton("Sluiten")
        btn_close.clicked.connect(self.accept)
        btn_row.addWidget(btn_close)
        root.addLayout(btn_row)

        # Data renderen
        self._render_lines()
        self.table.itemSelectionChanged.connect(self._on_selection_changed)

        if self.table.rowCount() > 0:
            self.table.selectRow(0)
            self._on_selection_changed()

    # ---------------- intern ----------------
    def set_labels(self, new_labels: dict[str, str]):
        """Laat toe labels dynamisch aan te passen."""
        self._labels.update(new_labels)
        self._render_lines()

    def _mk_title(self, order_header: dict | None) -> str:
        if not isinstance(order_header, dict):
            return "Orderlijnen"
        docnum = order_header.get("DocNum") or order_header.get("OrderNum") or ""
        date = order_header.get("DocDate") or order_header.get("OrderDate") or ""
        code = order_header.get("CardCode") or ""
        name = order_header.get("CardName") or ""
        parts = ["Orderlijnen"]
        suffix = []
        if docnum: suffix.append(f"DocNr. {docnum}")
        if date: suffix.append(str(date))
        if code: suffix.append(str(code))
        if name: suffix.append(str(name))
        if suffix:
            parts.append("— " + " | ".join(suffix))
        return " ".join(parts)

    def _make_header(self, hdr: dict) -> QWidget | None:
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(0, 0, 0, 0)
        left = QLabel(f"<b>DocNr.:</b> {hdr.get('DocNum', '-')} &nbsp;&nbsp; "
                      f"<b>Datum:</b> {hdr.get('DocDate', '-')}")
        right = QLabel(f"<b>Partner:</b> {hdr.get('CardCode', '-')} — {hdr.get('CardName', '-')}")
        l.addWidget(left)
        l.addStretch(1)
        l.addWidget(right)
        return w

    def _render_lines(self):
        rows = self._lines
        if not rows:
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Status"])
            self.table.setRowCount(1)
            self.table.setItem(0, 0, QTableWidgetItem("Geen lijnen gevonden."))
            return

        all_keys = set()
        [all_keys.update(r.keys()) for r in rows]
        norm2actual = {_normalize(k): k for k in all_keys}

        col_order = []
        actual_map = {}
        for label in self.COLS:
            found = None
            for cand in self.ALIASES.get(label, [label]):
                nk = _normalize(cand)
                if nk in norm2actual:
                    found = norm2actual[nk]
                    break
            if found:
                col_order.append(label)
                actual_map[label] = found

        self.table.setColumnCount(len(col_order))
        headers = [self._labels.get(label, label) for label in col_order]
        self.table.setHorizontalHeaderLabels(headers)
        self.table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, label in enumerate(col_order):
                key = actual_map[label]
                val = row.get(key, "")
                it = QTableWidgetItem("" if val is None else str(val))
                if isinstance(val, (int, float)) or (isinstance(val, str) and self._looks_numeric(val)):
                    it.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, c, it)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

    def _on_selection_changed(self):
        row = self.table.currentRow()
        ft = ""
        if 0 <= row < len(self._lines):
            line = self._lines[row]
            ft = (line.get("FreeTxt") or line.get("FreeText") or line.get("LineMemo") or "") or ""
        self.free_txt.setPlainText(str(ft))

    @staticmethod
    def _looks_numeric(val: Any) -> bool:
        if isinstance(val, (int, float)):
            return True
        if isinstance(val, str):
            s = val.strip().replace(" ", "").replace(".", "").replace(",", "")
            return s.replace("-", "", 1).isdigit()
        return False
