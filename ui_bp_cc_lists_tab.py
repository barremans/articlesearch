# ui_bp_cc_lists_tab.py
from typing import Any, Iterable, Mapping, Dict, List, Optional
from PySide6.QtCore import Qt, QModelIndex
from PySide6.QtWidgets import (
    QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView
)

from ui_bp_cc_ordrl_dialog import OrderLinesDialog
from ui_bp_cc_dnl1_dialog import DeliveryLinesDialog
from ui_bp_cc_inv1_dialog import InvoiceLinesDialog
from ui_bp_cc_rin1_dialog import CreditNoteLinesDialog
from ui_bp_cc_dpi1_dialog import DownPaymentLinesDialog  # <<< NIEUW


def _normalize(s: str) -> str:
    """Vergelijkingssleutel: lowercase + enkel alnum."""
    return "".join(ch for ch in str(s).lower() if ch.isalnum())


# -------- Qt6 enum-compat layer (lint + runtime) --------
try:
    RESIZE_TO_CONTENTS = QHeaderView.ResizeMode.ResizeToContents
except AttributeError:  # oudere bindings
    RESIZE_TO_CONTENTS = QHeaderView.ResizeToContents

try:
    SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
except AttributeError:
    SELECT_ROWS = QAbstractItemView.SelectRows

try:
    NO_EDIT_TRIGGERS = QAbstractItemView.EditTrigger.NoEditTriggers
except AttributeError:
    NO_EDIT_TRIGGERS = QAbstractItemView.NoEditTriggers

try:
    ITEM_IS_EDITABLE = Qt.ItemFlag.ItemIsEditable
except AttributeError:
    ITEM_IS_EDITABLE = Qt.ItemIsEditable
# --------------------------------------------------------


class CreditControlListsTab(QTabWidget):
    """
    Subtabs voor Credit Control:
      - Orders        (ORDR)   → dubbelklik toont ORDRL
      - Leveringen    (ODLN)   → dubbelklik toont DNL1
      - Voorschotten  (ODPI)   → dubbelklik toont DPI1  (DPI1 niet als kolom)
      - Facturen      (OINV)   → dubbelklik toont INV1  (INV1 niet als kolom)
      - Kredietnota's (ORIN)   → dubbelklik toont RIN1  (RIN1 niet als kolom)
    """

    # Gewenste kolommen (labels)
    ORDERS_COLS = ["DocNum", "DocDate", "Amount_exclVAT", "VAT_Amount", "OPenAmount_InclVAT", "Currency"]
    DELIVERIES_COLS = ["DeliveryNum", "DeliveryDate", "TotalExcelVAT", "TotalVAT", "TotalTotalInclVAT", "PaidAmount", "OpenAmountInclVat"]

    # Alias-mapping: label -> mogelijke keys in JSON
    ORDERS_ALIASES: Mapping[str, list[str]] = {
        "DocNum": ["DocNum", "OrderNum", "OrderID"],
        "DocDate": ["DocDate", "OrderDate", "Doc_Date"],
        "Amount_exclVAT": ["Amount_exclVAT", "AmountExclVAT", "TotalExclVAT", "OpenAmount_ExclVAT"],
        "VAT_Amount": ["VAT_Amount", "VATAmount", "TaxAmount"],
        "OPenAmount_InclVAT": ["OPenAmount_InclVAT", "OpenAmount_InclVAT", "OpenAmountInclVAT"],
        "Currency": ["Currency", "Curr", "DocCurrency"],
    }
    DELIVERIES_ALIASES: Mapping[str, list[str]] = {
        "DeliveryNum": ["DeliveryNum", "DocNum", "DLNNum"],
        "DeliveryDate": ["DeliveryDate", "DocDate", "DLNDate"],
        "TotalExcelVAT": ["TotalExcelVAT", "TotalExclVAT"],
        "TotalVAT": ["TotalVAT", "VAT_Amount", "TaxAmount"],
        "TotalTotalInclVAT": ["TotalTotalInclVAT", "TotalInclVAT", "GrandTotal", "DocTotal"],
        "PaidAmount": ["PaidAmount", "Paid", "AmountPaid"],
        "OpenAmountInclVat": ["OpenAmountInclVat", "OpenAmountInclVAT"],
    }

    # Sleutels (genormaliseerd) die NIET als kolom moeten verschijnen
    STRIP_KEYS_ADVANCES = {"dpi1"}     # voor ODPI
    STRIP_KEYS_INVOICES = {"inv1"}     # voor OINV
    STRIP_KEYS_CREDITNOTES = {"rin1"}  # voor ORIN

    def __init__(self, parent=None, debug: bool = False):
        super().__init__(parent)
        self.setDocumentMode(True)
        self._debug: bool = bool(debug)

        # datasets voor rendering (gestripte tabellen)
        self._orders: list[dict[str, Any]] = []
        self._deliveries: list[dict[str, Any]] = []
        self._advances: list[dict[str, Any]] = []
        self._invoices: list[dict[str, Any]] = []
        self._credit_notes: list[dict[str, Any]] = []

        # originele payloads met lijncollecties voor popups
        self._advances_payload: list[dict[str, Any]] = []
        self._invoices_payload: list[dict[str, Any]] = []
        self._credit_notes_payload: list[dict[str, Any]] = []

        # tabellen
        self.table_orders = self._mk_table();       self.addTab(self.table_orders, "Orders")
        self.table_deliveries = self._mk_table();   self.addTab(self.table_deliveries, "Leveringen")
        self.table_advances = self._mk_table();     self.addTab(self.table_advances, "Voorschotten")
        self.table_invoices = self._mk_table();     self.addTab(self.table_invoices, "Facturen")
        self.table_credit_notes = self._mk_table(); self.addTab(self.table_credit_notes, "Kredietnota's")

        # Double-click events
        self.table_orders.doubleClicked.connect(self._on_orders_double_clicked)
        self.table_deliveries.doubleClicked.connect(self._on_deliveries_double_clicked)
        self.table_advances.doubleClicked.connect(self._on_advances_double_clicked)   # <<< NIEUW
        self.table_invoices.doubleClicked.connect(self._on_invoices_double_clicked)
        self.table_credit_notes.doubleClicked.connect(self._on_credit_notes_double_clicked)

        # tooltips
        self.table_orders.setToolTip("Dubbelklik op een rij om de orderlijnen (ORDRL) te bekijken.")
        self.table_deliveries.setToolTip("Dubbelklik op een rij om de leveringslijnen (DNL1) te bekijken.")
        self.table_advances.setToolTip("Dubbelklik op een rij om de voorschotlijnen (DPI1) te bekijken.")
        self.table_invoices.setToolTip("Dubbelklik op een rij om de factuurlijnen (INV1) te bekijken.")
        self.table_credit_notes.setToolTip("Dubbelklik op een rij om de kredietnota-lijnen (RIN1) te bekijken.")

        self.set_loading()

    # ---------- Debug ----------
    def set_debug(self, enabled: bool):
        self._debug = bool(enabled)
        self._dbg(f"Debug {'aan' if self._debug else 'uit'}.")

    def _dbg(self, msg: str):
        if self._debug:
            print(f"[CC-LISTS] {msg}")

    def snapshot(self) -> Dict[str, int]:
        return {
            "orders": len(self._orders),
            "deliveries": len(self._deliveries),
            "advances": len(self._advances),
            "invoices": len(self._invoices),
            "credit_notes": len(self._credit_notes),
        }

    # ---------- Public API ----------
    def clear(self):
        self._dbg("clear() → alle datasets leeg.")
        self._orders.clear(); self._deliveries.clear()
        self._advances.clear(); self._invoices.clear(); self._credit_notes.clear()
        self._advances_payload.clear(); self._invoices_payload.clear(); self._credit_notes_payload.clear()
        for t in (self.table_orders, self.table_deliveries, self.table_advances,
                  self.table_invoices, self.table_credit_notes):
            t.clear(); t.setRowCount(0); t.setColumnCount(0)

    def set_loading(self, card_code: str | None = None):
        msg = f"Laden… ({card_code})" if card_code else "Laden…"
        self._dbg(f"set_loading: {msg}")
        for t in (self.table_orders, self.table_deliveries, self.table_advances,
                  self.table_invoices, self.table_credit_notes):
            self._render_placeholder(t, msg)

    def set_from_json(self, json_data: dict[str, Any] | None):
        if not json_data:
            self._dbg("set_from_json: GEEN json_data.")
            return
        if "ORDR" in json_data:
            self.set_orders(json_data.get("ORDR") or [])
        if "ODLN" in json_data:
            self.set_deliveries(json_data.get("ODLN") or [])
        if "ODPI" in json_data:
            self.set_advances(json_data.get("ODPI") or [])
        if "OINV" in json_data:
            self.set_invoices(json_data.get("OINV") or [])
        if "ORIN" in json_data:
            self.set_credit_notes(json_data.get("ORIN") or [])

    def set_orders(self, rows: Iterable[dict[str, Any]]):
        rows = list(rows or [])
        self._dbg(f"set_orders: {len(rows)} rows.")
        self._orders = rows
        self._render_with_aliases(
            self.table_orders, rows=self._orders,
            desired_cols=self.ORDERS_COLS, aliases=self.ORDERS_ALIASES,
            tabname="Orders", payload_rows=self._orders
        )

    def set_deliveries(self, rows: Iterable[dict[str, Any]]):
        rows = list(rows or [])
        self._dbg(f"set_deliveries: {len(rows)} rows.")
        self._deliveries = rows
        self._render_with_aliases(
            self.table_deliveries, rows=self._deliveries,
            desired_cols=self.DELIVERIES_COLS, aliases=self.DELIVERIES_ALIASES,
            tabname="Leveringen", payload_rows=self._deliveries
        )

    def set_advances(self, rows: Iterable[dict[str, Any]]):
        rows = list(rows or [])
        # bewaar originele payload (met DPI1) voor popup
        self._advances_payload = rows
        # strip DPI1 kolom uit de zichtbare tabel
        stripped = self._strip_keys(rows, self.STRIP_KEYS_ADVANCES)
        self._dbg(f"set_advances: {len(rows)} rows (after strip {len(stripped)}).")
        self._advances = stripped
        # generiek renderen, maar payload van originele rows aan kolom 0 hangen
        self._render_generic(self.table_advances, self._advances, tabname="Voorschotten", payload_rows=self._advances_payload)

    def set_invoices(self, rows: Iterable[dict[str, Any]]):
        rows = list(rows or [])
        self._invoices_payload = rows
        stripped = self._strip_keys(rows, self.STRIP_KEYS_INVOICES)
        self._dbg(f"set_invoices: {len(rows)} rows (after strip {len(stripped)}).")
        self._invoices = stripped
        self._render_generic(self.table_invoices, self._invoices, tabname="Facturen", payload_rows=self._invoices_payload)

    def set_credit_notes(self, rows: Iterable[dict[str, Any]]):
        rows = list(rows or [])
        self._credit_notes_payload = rows
        stripped = self._strip_keys(rows, self.STRIP_KEYS_CREDITNOTES)
        self._dbg(f"set_credit_notes: {len(rows)} rows (after strip {len(stripped)}).")
        self._credit_notes = stripped
        self._render_generic(self.table_credit_notes, self._credit_notes, tabname="Kredietnota's", payload_rows=self._credit_notes_payload)

    def set_all(self, *, orders=None, deliveries=None, advances=None, invoices=None, credit_notes=None):
        self._dbg(
            f"set_all: ORDR={len(orders or [])} ODLN={len(deliveries or [])} "
            f"ODPI={len(advances or [])} OINV={len(invoices or [])} ORIN={len(credit_notes or [])}"
        )
        if orders is not None: self.set_orders(orders)
        if deliveries is not None: self.set_deliveries(deliveries)
        if advances is not None: self.set_advances(advances)
        if invoices is not None: self.set_invoices(invoices)
        if credit_notes is not None: self.set_credit_notes(credit_notes)

    def show_after_unlock(self, card_code: str | None = None):
        snap = self.snapshot()
        self._dbg(f"show_after_unlock: snapshot={snap}")
        if any(snap.values()):
            self._refresh_all()
        else:
            self.set_loading(card_code)

    # ---------- Intern ----------
    def _refresh_all(self):
        self._dbg("Refresh alle tabellen met bestaande datasets.")
        self._render_with_aliases(
            self.table_orders, self._orders, self.ORDERS_COLS, self.ORDERS_ALIASES,
            tabname="Orders", payload_rows=self._orders
        )
        self._render_with_aliases(
            self.table_deliveries, self._deliveries, self.DELIVERIES_COLS, self.DELIVERIES_ALIASES,
            tabname="Leveringen", payload_rows=self._deliveries
        )
        self._render_generic(self.table_advances, self._advances, tabname="Voorschotten", payload_rows=self._advances_payload)
        self._render_generic(self.table_invoices, self._invoices, tabname="Facturen", payload_rows=self._invoices_payload)
        self._render_generic(self.table_credit_notes, self._credit_notes, tabname="Kredietnota's", payload_rows=self._credit_notes_payload)

    def _mk_table(self) -> QTableWidget:
        t = QTableWidget(0, 0)
        t.horizontalHeader().setSectionResizeMode(RESIZE_TO_CONTENTS)
        t.horizontalHeader().setStretchLastSection(True)
        t.setSelectionBehavior(SELECT_ROWS)
        t.setEditTriggers(NO_EDIT_TRIGGERS)
        t.setSortingEnabled(True)
        return t

    def _render_placeholder(self, table: QTableWidget, text: str):
        table.setColumnCount(1)
        table.setHorizontalHeaderLabels(["Status"])
        table.setRowCount(1)
        it = QTableWidgetItem(text)
        it.setFlags(it.flags() & ~ITEM_IS_EDITABLE)
        table.setItem(0, 0, it)

    def _render_with_aliases(
        self,
        table: QTableWidget,
        rows: List[dict[str, Any]],
        desired_cols: List[str],
        aliases: Mapping[str, list[str]],
        *,
        tabname: str = "",
        payload_rows: Optional[List[dict[str, Any]]] = None
    ):
        table.clear()
        if not rows:
            self._dbg(f"_render_with_aliases[{tabname}]: geen rows → placeholder.")
            self._render_placeholder(table, "Geen gegevens.")
            return

        # Bepaal mapping
        all_keys = set()
        for r in rows: all_keys.update(r.keys())
        normalized_to_actual = {_normalize(k): k for k in all_keys}
        effective_map: Dict[str, str] = {}
        for want in desired_cols:
            found_key = None
            for cand in aliases.get(want, [want]):
                nk = _normalize(cand)
                if nk in normalized_to_actual:
                    found_key = normalized_to_actual[nk]
                    break
            if found_key:
                effective_map[want] = found_key

        if not effective_map:
            self._dbg(f"_render_with_aliases[{tabname}]: geen gewenste kolommen gevonden → generiek.")
            self._render_generic(table, rows, tabname=tabname, payload_rows=payload_rows)
            return

        cols = [c for c in desired_cols if c in effective_map]
        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels(cols)
        table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, want in enumerate(cols):
                key = effective_map[want]
                val = row.get(key, "")
                item = QTableWidgetItem("" if val is None else str(val))
                if self._looks_numeric(val):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item.setFlags(item.flags() & ~ITEM_IS_EDITABLE)
                table.setItem(r, c, item)
            # payload aan kolom 0 hangen (originele row indien beschikbaar)
            if payload_rows and r < len(payload_rows) and table.item(r, 0) is not None:
                table.item(r, 0).setData(Qt.UserRole, payload_rows[r])
            elif table.item(r, 0) is not None:
                table.item(r, 0).setData(Qt.UserRole, rows[r])

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    def _render_generic(
        self,
        table: QTableWidget,
        rows: List[dict[str, Any]],
        *,
        tabname: str = "",
        payload_rows: Optional[List[dict[str, Any]]] = None
    ):
        table.clear()
        if not rows:
            self._dbg(f"_render_generic[{tabname}]: geen rows → placeholder.")
            self._render_placeholder(table, "Geen gegevens.")
            return

        first_keys = list(rows[0].keys())
        other_keys: List[str] = []
        seen = set(first_keys)
        for row in rows[1:]:
            for k in row.keys():
                if k not in seen:
                    seen.add(k)
                    other_keys.append(k)
        cols = first_keys + other_keys

        table.setColumnCount(len(cols))
        table.setHorizontalHeaderLabels([str(c) for c in cols])
        table.setRowCount(len(rows))

        for r, row in enumerate(rows):
            for c, key in enumerate(cols):
                val = row.get(key, "")
                item = QTableWidgetItem("" if val is None else str(val))
                if self._looks_numeric(val):
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                item.setFlags(item.flags() & ~ITEM_IS_EDITABLE)
                table.setItem(r, c, item)
            # payload aan kolom 0 hangen (originele row indien beschikbaar)
            if payload_rows and r < len(payload_rows) and table.item(r, 0) is not None:
                table.item(r, 0).setData(Qt.UserRole, payload_rows[r])
            elif table.item(r, 0) is not None:
                table.item(r, 0).setData(Qt.UserRole, rows[r])

        table.resizeColumnsToContents()
        table.horizontalHeader().setStretchLastSection(True)

    @staticmethod
    def _looks_numeric(val: Any) -> bool:
        if isinstance(val, (int, float)):
            return True
        if isinstance(val, str):
            s = val.strip().replace(" ", "").replace(".", "").replace(",", "")
            return s.replace("-", "", 1).isdigit()
        return False

    # ---------- helpers ----------
    def _strip_keys(self, rows: List[dict[str, Any]], strip_norm_keys: set[str]) -> List[dict[str, Any]]:
        """
        Verwijder kolommen waarvan de (genormaliseerde) sleutel in strip_norm_keys zit.
        (Gebruik voor ODPI/OINV/ORIN om DPI1/INV1/RIN1 niet als kolom te tonen.)
        """
        out: List[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                out.append(row)
                continue
            new_row: dict[str, Any] = {}
            for k, v in row.items():
                if _normalize(k) in strip_norm_keys:
                    continue
                new_row[k] = v
            out.append(new_row)
        return out

    # ---------- events (double click) ----------
    def _on_orders_double_clicked(self, index: QModelIndex):
        r = index.row()
        if r < 0 or r >= self.table_orders.rowCount(): return
        first_item = self.table_orders.item(r, 0)
        order_dict = first_item.data(Qt.UserRole) if first_item else None
        if not isinstance(order_dict, dict): return

        lines = []
        for key in ("ORDRL", "RDR1", "Lines"):
            if isinstance(order_dict.get(key), list):
                lines = order_dict[key]; break

        dlg = OrderLinesDialog(self, order_header=order_dict, lines=lines)
        dlg.exec()

    def _on_deliveries_double_clicked(self, index: QModelIndex):
        r = index.row()
        if r < 0 or r >= self.table_deliveries.rowCount(): return
        first_item = self.table_deliveries.item(r, 0)
        delivery = first_item.data(Qt.UserRole) if first_item else None
        if not isinstance(delivery, dict): return

        lines = []
        for key in ("DNL1", "Lines"):
            if isinstance(delivery.get(key), list):
                lines = delivery[key]; break

        dlg = DeliveryLinesDialog(self, delivery_header=delivery, lines=lines)
        dlg.exec()

    def _on_advances_double_clicked(self, index: QModelIndex):
        r = index.row()
        if r < 0 or r >= self.table_advances.rowCount(): return
        first_item = self.table_advances.item(r, 0)
        dpi = first_item.data(Qt.UserRole) if first_item else None
        if not isinstance(dpi, dict): return

        lines = []
        for key in ("DPI1", "Lines"):
            if isinstance(dpi.get(key), list):
                lines = dpi[key]; break

        dlg = DownPaymentLinesDialog(self, dpi_header=dpi, lines=lines)
        dlg.exec()

    def _on_invoices_double_clicked(self, index: QModelIndex):
        r = index.row()
        if r < 0 or r >= self.table_invoices.rowCount(): return
        first_item = self.table_invoices.item(r, 0)
        inv = first_item.data(Qt.UserRole) if first_item else None
        if not isinstance(inv, dict): return

        lines = []
        for key in ("INV1", "Lines"):
            if isinstance(inv.get(key), list):
                lines = inv[key]; break

        dlg = InvoiceLinesDialog(self, invoice_header=inv, lines=lines)
        dlg.exec()

    def _on_credit_notes_double_clicked(self, index: QModelIndex):
        r = index.row()
        if r < 0 or r >= self.table_credit_notes.rowCount(): return
        first_item = self.table_credit_notes.item(r, 0)
        cn = first_item.data(Qt.UserRole) if first_item else None
        if not isinstance(cn, dict): return

        lines = []
        for key in ("RIN1", "Lines"):
            if isinstance(cn.get(key), list):
                lines = cn[key]; break

        dlg = CreditNoteLinesDialog(self, credit_header=cn, lines=lines)
        dlg.exec()
