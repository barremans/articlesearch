# ui_bp_contacts_tab.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QButtonGroup,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QGridLayout
)
from PySide6.QtCore import Qt
from ui_bp_helper import make_caption_label, make_value_label


def role_text(c: dict) -> str:
    pos = (c.get("Position") or "").strip()
    udf = (c.get("U_Functieprofiel") or "").strip()
    if pos and udf:
        return f"{pos} / {udf}"
    return pos or udf or ""


def active_label(val: str | None) -> str:
    return "Ja" if (val or "").upper() == "Y" else "Nee"


class ContactDialog(QDialog):
    def __init__(self, parent=None, contact: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Contactdetails")
        self.resize(520, 340)

        grid = QGridLayout(self)
        grid.setColumnMinimumWidth(0, 110)
        grid.setColumnMinimumWidth(1, 260)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(6)

        def add_row(r, cap, val="-"):
            cap_lbl = make_caption_label(cap)
            cap_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            grid.addWidget(cap_lbl, r, 0)

            v = make_value_label()
            v.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            v.setText(str(val) if val is not None else "-")
            grid.addWidget(v, r, 1)
            return v

        self.v_title = add_row(0, "Titel:", "-")
        self.v_name  = add_row(1, "Naam:", "-")
        self.v_func  = add_row(2, "Functie:", "-")
        self.v_tel1  = add_row(3, "Tel.1:", "-")
        self.v_tel2  = add_row(4, "Tel.2:", "-")
        self.v_gsm   = add_row(5, "GSM:", "-")
        self.v_mail  = add_row(6, "Mail:", "-")
        self.v_act   = add_row(7, "Actief:", "-")

        if contact:
            self.fill(contact)

    def fill(self, c: dict):
        first  = (c.get("FirstName") or "").strip()
        middle = (c.get("MiddleName") or "").strip()
        last   = (c.get("LastName") or "").strip()
        fallback = (c.get("Name") or "").strip()
        full = " ".join(x for x in [first, middle, last] if x) or fallback

        self.v_title.setText(str(c.get("Title") or "-"))
        self.v_name.setText(full or "-")
        self.v_func.setText(role_text(c) or "-")
        self.v_tel1.setText(str(c.get("Phone1") or "-"))
        self.v_tel2.setText(str(c.get("Phone2") or "-"))
        self.v_gsm.setText(str(c.get("MobilePhone") or "-"))
        self.v_mail.setText(str(c.get("E_Mail") or "-"))
        self.v_act.setText(active_label(c.get("Active")))


class ContactsTab(QWidget):
    """
    Tabel met 'Naam', 'Functie' + lege spacer-kolom.
    Zoeken in naam/functie/telefoons/mail. Filter op status (Alle/Actief/Inactief).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.contacts: list[dict] = []
        self.filtered: list[dict] = []

        layout = QVBoxLayout(self)

        # Zoek + filter
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek op naam, functie, tel of mail…")
        self.search.textChanged.connect(self._apply_filters)

        self.rb_all = QRadioButton("Alle"); self.rb_all.setChecked(True)
        self.rb_y   = QRadioButton("Actief")
        self.rb_n   = QRadioButton("Inactief")
        self.group = QButtonGroup(self)
        for i, rb in enumerate([self.rb_all, self.rb_y, self.rb_n]):
            self.group.addButton(rb, i)
        self.group.buttonToggled.connect(lambda *_: self._apply_filters())

        top.addWidget(QLabel("Zoek:"))
        top.addWidget(self.search, 1)
        top.addSpacing(10)
        top.addWidget(QLabel("Status:"))
        top.addWidget(self.rb_all)
        top.addWidget(self.rb_y)
        top.addWidget(self.rb_n)
        top.addStretch(1)
        layout.addLayout(top)

        # Tabel (Naam, Functie, spacer)
        self.table = QTableWidget(0, 3)

        hdr_name = QTableWidgetItem("Naam")
        hdr_name.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hdr_func = QTableWidgetItem("Functie")
        hdr_func.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hdr_spc  = QTableWidgetItem("")
        self.table.setHorizontalHeaderItem(0, hdr_name)
        self.table.setHorizontalHeaderItem(1, hdr_func)
        self.table.setHorizontalHeaderItem(2, hdr_spc)

        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

        self.table.setColumnWidth(0, 420)
        self.table.setColumnWidth(1, 380)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSortingEnabled(True)
        self.table.cellDoubleClicked.connect(self._open_dialog)

        layout.addWidget(self.table, 1)

    # ---- externe API ----
    def clear(self):
        self.contacts = []
        self.filtered = []
        self.table.setRowCount(0)

    def set_contacts(self, contacts: list[dict]):
        self.contacts = contacts or []
        self._apply_filters()

    # ---- intern ----
    def _apply_filters(self):
        text = (self.search.text() or "").strip().lower()
        status = "ALL"
        if self.rb_y.isChecked():
            status = "Y"
        elif self.rb_n.isChecked():
            status = "N"

        def match(c: dict) -> bool:
            if status != "ALL" and (c.get("Active") or "").upper() != status:
                return False
            if not text:
                return True

            name = " ".join(
                x for x in [
                    str(c.get("FirstName") or ""),
                    str(c.get("MiddleName") or ""),
                    str(c.get("LastName") or "")
                ] if x
            ).strip() or str(c.get("Name") or "")

            func = role_text(c)
            tel1 = str(c.get("Phone1") or "")
            tel2 = str(c.get("Phone2") or "")
            gsm  = str(c.get("MobilePhone") or "")
            mail = str(c.get("E_Mail") or "")

            blob = " ".join([name, func, tel1, tel2, gsm, mail]).lower()
            return text in blob

        self.filtered = [c for c in self.contacts if match(c)]
        self.filtered.sort(key=lambda c: (
            " ".join(
                x for x in [
                    (c.get("FirstName") or "").strip(),
                    (c.get("MiddleName") or "").strip(),
                    (c.get("LastName") or "").strip()
                ] if x
            ).strip() or (c.get("Name") or "").strip()
        ).lower())

        self._render()

    def _render(self):
        was_sorting = self.table.isSortingEnabled()
        if was_sorting:
            self.table.setSortingEnabled(False)

        self.table.setRowCount(len(self.filtered))
        for r, c in enumerate(self.filtered):
            first  = (c.get("FirstName") or "").strip()
            middle = (c.get("MiddleName") or "").strip()
            last   = (c.get("LastName") or "").strip()
            fallback = (c.get("Name") or "").strip()
            full = " ".join(x for x in [first, middle, last] if x) or fallback

            it0 = QTableWidgetItem(full);           it0.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            it1 = QTableWidgetItem(role_text(c));   it1.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            it2 = QTableWidgetItem("")  # spacer

            self.table.setItem(r, 0, it0)
            self.table.setItem(r, 1, it1)
            self.table.setItem(r, 2, it2)

        if was_sorting:
            self.table.setSortingEnabled(True)
            self.table.sortItems(0, Qt.AscendingOrder)

    def _open_dialog(self, row: int, _col: int):
        contact = self.filtered[row] if 0 <= row < len(self.filtered) else None
        dlg = ContactDialog(self, contact=contact)
        dlg.exec()
