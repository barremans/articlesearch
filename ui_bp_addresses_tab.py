# ui_bp_addresses_tab.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QRadioButton, QButtonGroup,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView, QDialog, QGridLayout
)
from PySide6.QtCore import Qt
from ui_bp_helper import make_caption_label, make_value_label, build_place


class AddressDialog(QDialog):
    def __init__(self, parent=None, address: dict | None = None):
        super().__init__(parent)
        self.setWindowTitle("Adresdetails")
        self.resize(520, 360)

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

        self.v_name = add_row(0, "Naam:", "-")
        self.v_type = add_row(1, "Type:", "-")
        self.v_street = add_row(2, "Straat:", "-")
        self.v_city = add_row(3, "Plaats:", "-")
        self.v_block = add_row(4, "Blok:", "-")
        self.v_bfr = add_row(5, "Verd./Kamer:", "-")
        self.v_tel = add_row(6, "Tel:", "-")

        if address:
            self.fill(address)

    def fill(self, address: dict):
        atype = (address.get("AddressType") or "").upper()
        self.v_name.setText(str(address.get("AddressName") or "-"))
        self.v_type.setText("Betaling (B)" if atype == "B" else "Levering (S)" if atype == "S" else atype or "-")
        self.v_street.setText(str(address.get("Street") or "-"))
        self.v_city.setText(build_place(address.get("Country"), address.get("ZipCode"), address.get("City")))
        self.v_block.setText(str(address.get("Block") or "-"))
        self.v_bfr.setText(str(address.get("BuildingFloorRoom") or "-"))
        self.v_tel.setText(str(address.get("County") or "-"))  # in dataset = tel


class AddressesTab(QWidget):
    """
    Tabel met 'Adres titel', 'Plaats', 'Type' + lege spacer-kolom.
    Zoek op titel/postcode/plaats en filter op type.
    Externe API:
      - set_addresses(list[dict])
      - clear()
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        self.addresses: list[dict] = []
        self.filtered: list[dict] = []

        layout = QVBoxLayout(self)

        # zoek & filter
        top = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText("Zoek op titel, postcode of plaats...")
        self.search.textChanged.connect(self._apply_filters)

        self.rb_all = QRadioButton("Alle"); self.rb_all.setChecked(True)
        self.rb_b   = QRadioButton("B (Betaling)")
        self.rb_s   = QRadioButton("S (Levering)")
        self.group = QButtonGroup(self)
        for i, rb in enumerate([self.rb_all, self.rb_b, self.rb_s]):
            self.group.addButton(rb, i)
        self.group.buttonToggled.connect(lambda *_: self._apply_filters())

        top.addWidget(QLabel("Zoek:"))
        top.addWidget(self.search, 1)
        top.addSpacing(10)
        top.addWidget(QLabel("Type:"))
        top.addWidget(self.rb_all)
        top.addWidget(self.rb_b)
        top.addWidget(self.rb_s)
        top.addStretch(1)
        layout.addLayout(top)

        # tabel: 4 kolommen (laatste is een lege spacer)
        self.table = QTableWidget(0, 4)

        # custom header-items om uitlijning te sturen
        hdr_title = QTableWidgetItem("Adres titel")
        hdr_title.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hdr_place = QTableWidgetItem("Plaats")
        hdr_place.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        hdr_type  = QTableWidgetItem("Type")
        hdr_type.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
        hdr_spc   = QTableWidgetItem("")  # spacer

        self.table.setHorizontalHeaderItem(0, hdr_title)
        self.table.setHorizontalHeaderItem(1, hdr_place)
        self.table.setHorizontalHeaderItem(2, hdr_type)
        self.table.setHorizontalHeaderItem(3, hdr_spc)

        # kolombreedtes: 0 en 1 compacter; 2 naar inhoud; 3 rekt
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)

        self.table.setColumnWidth(0, 420)
        self.table.setColumnWidth(1, 260)

        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.cellDoubleClicked.connect(self._open_dialog)
        layout.addWidget(self.table, 1)

    # ---- externe API ----
    def clear(self):
        self.addresses = []
        self.filtered = []
        self.table.setRowCount(0)

    def set_addresses(self, addresses: list[dict]):
        self.addresses = addresses or []
        self._apply_filters()

    # ---- intern ----
    def _apply_filters(self):
        text = (self.search.text() or "").strip().lower()
        type_sel = "ALL"
        if self.rb_b.isChecked():
            type_sel = "B"
        elif self.rb_s.isChecked():
            type_sel = "S"

        def match(a: dict) -> bool:
            if type_sel != "ALL":
                if (a.get("AddressType") or "").upper() != type_sel:
                    return False
            if not text:
                return True
            title = str(a.get("AddressName") or "").lower()
            zipcode = str(a.get("ZipCode") or "").lower()
            city = str(a.get("City") or "").lower()
            country = str(a.get("Country") or "").lower()
            place = f"{country+'-' if country else ''}{zipcode}{' '+city if city else ''}".strip()
            return (text in title) or (text in zipcode) or (text in city) or (text in place)

        self.filtered = [a for a in self.addresses if match(a)]
        self._render()

    def _render(self):
        rows = self.filtered
        self.table.setRowCount(len(rows))
        for r, a in enumerate(rows):
            title = str(a.get("AddressName") or "")
            place = build_place(a.get("Country"), a.get("ZipCode"), a.get("City"))
            atype = (a.get("AddressType") or "").upper()
            type_label = "B" if atype == "B" else "S" if atype == "S" else atype

            it0 = QTableWidgetItem(title); it0.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            it1 = QTableWidgetItem(place); it1.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            it2 = QTableWidgetItem(type_label); it2.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
            it3 = QTableWidgetItem("")  # spacer

            self.table.setItem(r, 0, it0)
            self.table.setItem(r, 1, it1)
            self.table.setItem(r, 2, it2)
            self.table.setItem(r, 3, it3)

    def _open_dialog(self, row: int, _col: int):
        addr = None
        if 0 <= row < len(self.filtered):
            addr = self.filtered[row]
        dlg = AddressDialog(self, address=addr)
        dlg.exec()
