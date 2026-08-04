# =============================================================================
# ArticleSearch
# File:    ui_bp_articles_tab.py
# Role:    Widget voor de tab "Artikels" in BpWindow (ui_bp.py) — toont de
#          artikels gekoppeld aan een leverancier (CardType == "S"), via
#          artbp_info.get_supplier_articles(CardCode). Lazy load: data wordt
#          pas opgehaald bij het eerste bezoek aan deze tab (getriggerd door
#          BpWindow via ensure_loaded()), niet automatisch bij het openen
#          van de BP-kaart. Bevat een eigen, zelfstandige verzamel-lijst
#          ("Voeg toe aan lijst" / "Toon lijst" / "Leeg lijst"), losstaand
#          van de collected_data-lijst van het hoofdvenster — analoog aan de
#          bestaande flow in ui_main.py, maar hier lokaal aan dit tabblad.
# Version: 1.5.0
# Author:  Bart Bossuyt
# Changes: 1.5.0 — Kolommen "CardCode" en "CardName" verwijderd uit
#                   ARTICLE_COLUMNS (op vraag van gebruiker) — logisch ook,
#                   want binnen deze tab is dat altijd dezelfde leverancier
#                   (de kaart die open staat), dus redundant per rij. De
#                   velden komen nog steeds binnen via artbp_info.py, worden
#                   enkel niet meer getoond.
# Changes: 1.4.0 — Zoekbalk toegevoegd (analoog aan ui_bp_addresses_tab.py /
#                   ui_bp_contacts_tab.py): filtert live op Art.Nr.
#                   (ItemCode), Leverancier Art.Nr. (SuppCatNum) en
#                   Omschrijving (ItemName), case-insensitive substring-
#                   match. Interne data nu gesplitst in self._raw_data
#                   (volledige, ongefilterde ophaling) en
#                   self._filtered_data (huidig getoonde subset). Sortering
#                   (dubbelklik header) werkt op de gefilterde set en blijft
#                   toegepast bij het aanpassen van de zoekterm. Status-
#                   label toont "X — Y gefilterd op '...'" wanneer een
#                   zoekterm actief is.
# Changes: 1.3.0 — Op vraag van gebruiker:
#                   - Kolom "Omschrijving (Frgn)" (FrgnName) verwijderd —
#                     stond leeg/weinig gebruikt en nam ruimte in.
#                   - Kolomresize volledig herzien naar Excel-achtig gedrag:
#                     alle kolommen staan nu op Interactive i.p.v. Stretch,
#                     zodat de gebruiker elke kolom (incl. "Omschrijving")
#                     zelf kan verslepen én — ingebouwd Qt-gedrag, werkte
#                     eerder niet door de Stretch-modus — kan dubbelklikken
#                     op een kolomrand voor auto-fit-op-inhoud, net als in
#                     Excel. Initiële breedtes: automatische auto-fit via
#                     resizeColumnsToContents(), behalve "Leverancier
#                     Art.Nr." die bewust op de helft daarvan start.
#                     Laatste kolom vult resterende ruimte
#                     (setStretchLastSection) i.p.v. een lege grijze zone.
# Changes: 1.2.0 — Kolombreedtes gecorrigeerd/aangepast:
#                   - BUGFIX: door het invoegen van "SuppCatNum" (v1.1.0)
#                     schoof de bestaande Stretch-regel (idx==2, oorspronkelijk
#                     bedoeld voor "Omschrijving") per ongeluk naar "Leverancier
#                     Art.Nr." — Omschrijving viel daardoor buiten beeld
#                     (moest scrollen). Nu op key gebaseerd i.p.v. vaste index.
#                   - "Leverancier Art.Nr." (SuppCatNum) krijgt de helft van
#                     zijn automatische content-breedte (Interactive, manueel
#                     nog verbreedbaar door gebruiker).
#                   - "Omschrijving" (ItemName) én "Opmerking" (UserText)
#                     staan nu beide op Stretch (breder, delen resterende
#                     ruimte).
# Changes: 1.1.0 — Nieuw veld "SuppCatNum" (leveranciersartikelnummer) in de
#                   API-respons toegevoegd aan ARTICLE_COLUMNS, net na
#                   "Art.Nr." — niet sorteerbaar (enkel LastPurPrc/
#                   QtyPurchasedLast6Months/QtyPurchasedLast12Months blijven
#                   sorteerbaar, ongewijzigd).
# Changes: 1.0.0 — Initiële versie (ART-BP-1). Toont alle velden uit de
#                   respons. Dubbelklik-sortering (analoog aan SORT-1 in
#                   ui_main.py) enkel op de kolommen "LastPurPrc",
#                   "QtyPurchasedLast6Months" en "QtyPurchasedLast12Months"
#                   (numeriek) — op vraag van gebruiker, bewuste keuze, niet
#                   alle kolommen.
# =============================================================================
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, Signal, Slot, QMimeData
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDialog, QMessageBox, QApplication
)

from artbp_info import get_supplier_articles

# ---------------------------------------------------------------------------
# Kolommen: (data-key uit de API-respons, weergegeven headerlabel)
# "Alle velden uit de JSON-respons" op vraag van gebruiker.
# ---------------------------------------------------------------------------
ARTICLE_COLUMNS = [
    ("ItemCode", "Art.Nr."),
    ("SuppCatNum", "Leverancier Art.Nr."),
    ("ItemName", "Omschrijving"),
    ("ItmsGrpCod", "Groep-ID"),
    ("ItmsGrpNam", "Groep"),
    ("UserText", "Opmerking"),
    ("LastPurPrc", "Laatste inkoopprijs"),
    ("LastPurCur", "Munt"),
    ("QtyPurchasedLast6Months", "Qty laatste 6 maand"),
    ("QtyPurchasedLast12Months", "Qty laatste 12 maand"),
]

# Enkel deze kolommen zijn sorteerbaar via dubbelklik op de header
# (op expliciete vraag van gebruiker — bewuste keuze, niet alle kolommen).
SORTABLE_KEYS = {"LastPurPrc", "QtyPurchasedLast6Months", "QtyPurchasedLast12Months"}

# Kolom die bewust smaller start dan zijn automatische content-breedte
# (nadien manueel versleepbaar door de gebruiker, zie _render_rows).
NARROW_START_KEY = "SuppCatNum"  # Leverancier Art.Nr.


def _numeric_sort_key(record: dict, col_key: str):
    """Gedeelde sorteersleutel (numeriek, None's achteraan) voor SORTABLE_KEYS."""
    val = record.get(col_key)
    if val is None:
        return (1, 0.0)
    try:
        return (0, float(val))
    except (TypeError, ValueError):
        return (1, 0.0)


class ArticlesTab(QWidget):
    """Tab 'Artikels' in BpWindow — artikels gekoppeld aan een leverancier."""

    fetch_success = Signal(list)
    fetch_error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._exec = ThreadPoolExecutor(max_workers=2)
        self._card_code: str = ""
        self._loaded_for: str | None = None   # laatst succesvol geladen CardCode
        self._loading: bool = False
        self._raw_data: list[dict] = []        # volledige, ongefilterde ophaling
        self._filtered_data: list[dict] = []   # huidig getoonde subset (na zoekfilter)
        self._sort_state = {"column_index": None, "ascending": True}

        # Eigen, zelfstandige verzamel-lijst (los van het hoofdvenster)
        self.collected_data: list[str] = []

        layout = QVBoxLayout(self)

        self.status_label = QLabel("Geen leverancier geselecteerd.")
        layout.addWidget(self.status_label)

        # Zoekbalk — analoog aan AddressesTab/ContactsTab
        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Zoek op art.nr, leverancier art.nr of omschrijving...")
        self.search_input.textChanged.connect(self._apply_filters)
        search_row.addWidget(QLabel("Zoek:"))
        search_row.addWidget(self.search_input, 1)
        layout.addLayout(search_row)

        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        header_labels = ["Selectie"] + [lbl for _, lbl in ARTICLE_COLUMNS]
        self.table.setColumnCount(len(header_labels))
        self.table.setHorizontalHeaderLabels(header_labels)
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().sectionDoubleClicked.connect(self._on_header_double_clicked)
        layout.addWidget(self.table, 1)

        btn_row = QHBoxLayout()
        self.btn_collect = QPushButton("Voeg toe aan lijst")
        self.btn_clear_list = QPushButton("Leeg lijst")
        self.btn_show_list = QPushButton("Toon lijst")
        self.chk_select_all = QCheckBox("Selecteer alles")

        self.btn_collect.clicked.connect(self._collect_selected_rows)
        self.btn_clear_list.clicked.connect(self._clear_collected_list)
        self.btn_show_list.clicked.connect(self._show_collected_dialog)
        self.chk_select_all.toggled.connect(self._toggle_select_all)

        btn_row.addWidget(self.btn_collect)
        btn_row.addWidget(self.btn_clear_list)
        btn_row.addWidget(self.btn_show_list)
        btn_row.addWidget(self.chk_select_all)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.fetch_success.connect(self._on_fetch_success)
        self.fetch_error.connect(self._on_fetch_error)

    # ===================== Publieke API — aangeroepen vanuit BpWindow =====================
    def set_card_code(self, card_code: str):
        """
        Nieuw BP-record geselecteerd: interne state resetten. Haalt NOG NIET
        op (lazy load) — dat gebeurt pas via ensure_loaded() wanneer de
        gebruiker effectief op deze tab klikt.
        """
        card_code = (card_code or "").strip()
        if card_code == self._card_code:
            return
        self._card_code = card_code
        self._loaded_for = None
        self._raw_data = []
        self._filtered_data = []
        self._sort_state = {"column_index": None, "ascending": True}
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self._render_rows([])
        if card_code:
            self.status_label.setText(f"Nog niet geladen — open deze tab om artikels van {card_code} op te halen.")
        else:
            self.status_label.setText("Geen leverancier geselecteerd.")

    def ensure_loaded(self):
        """Lazy load: wordt aangeroepen zodra de tab effectief actief wordt."""
        if not self._card_code or self._loading or self._loaded_for == self._card_code:
            return
        self._loading = True
        self.status_label.setText(f"⏳ Artikels laden voor {self._card_code}...")

        card_code = self._card_code

        def _worker():
            try:
                articles = get_supplier_articles(card_code)
                self.fetch_success.emit(articles)
            except Exception as e:
                self.fetch_error.emit(str(e))

        self._exec.submit(_worker)

    def clear(self):
        """Volledige reset — bv. bij clear_search()/_clear_all() in BpWindow."""
        self._card_code = ""
        self._loaded_for = None
        self._loading = False
        self._raw_data = []
        self._filtered_data = []
        self._sort_state = {"column_index": None, "ascending": True}
        self.search_input.blockSignals(True)
        self.search_input.clear()
        self.search_input.blockSignals(False)
        self._render_rows([])
        self.status_label.setText("Geen leverancier geselecteerd.")

    def shutdown(self):
        """Nette afsluiting van de eigen threadpool (bv. vanuit BpWindow.closeEvent)."""
        try:
            self._exec.shutdown(wait=False, cancel_futures=True)
        except TypeError:
            self._exec.shutdown(wait=False)

    # ===================== Slots (UI-thread) =====================
    @Slot(list)
    def _on_fetch_success(self, articles: list):
        self._loading = False
        self._loaded_for = self._card_code
        self._raw_data = articles or []
        self._apply_filters()  # zet status_label + rendert (met eventuele actieve zoekterm)

    @Slot(str)
    def _on_fetch_error(self, msg: str):
        self._loading = False
        self.status_label.setText("❌ Fout bij ophalen artikels.")
        QMessageBox.warning(self, "Artikels ophalen mislukt", msg)

    # ===================== Zoeken/filteren =====================
    def _apply_filters(self):
        """
        Filtert self._raw_data naar self._filtered_data op basis van de
        zoekbalk (Art.Nr., Leverancier Art.Nr., Omschrijving — case-
        insensitive substring-match), past een eventuele actieve sortering
        opnieuw toe, en rendert.
        """
        text = (self.search_input.text() or "").strip().lower()

        if not text:
            self._filtered_data = list(self._raw_data)
        else:
            def _match(record: dict) -> bool:
                haystack = " ".join([
                    str(record.get("ItemCode") or ""),
                    str(record.get("SuppCatNum") or ""),
                    str(record.get("ItemName") or ""),
                ]).lower()
                return text in haystack

            self._filtered_data = [r for r in self._raw_data if _match(r)]

        # Actieve sortering herbevestigen op de (nieuwe) gefilterde set
        col_idx = self._sort_state.get("column_index")
        if col_idx is not None and 0 < col_idx <= len(ARTICLE_COLUMNS):
            col_key, _label = ARTICLE_COLUMNS[col_idx - 1]
            if col_key in SORTABLE_KEYS:
                self._filtered_data.sort(
                    key=lambda rec: _numeric_sort_key(rec, col_key),
                    reverse=not self._sort_state["ascending"]
                )

        self._render_rows(self._filtered_data)

        total = len(self._raw_data)
        shown = len(self._filtered_data)
        if text:
            self.status_label.setText(f"Aantal gekoppelde artikels: {total} — {shown} gefilterd op '{text}'")
        else:
            self.status_label.setText(f"Aantal gekoppelde artikels: {total}")

    # ===================== Tabel opbouwen =====================
    def _render_rows(self, data: list):
        self.table.setRowCount(len(data))

        header = self.table.horizontalHeader()

        # Alle kolommen op Interactive: gebruiker kan zelf breder/smaller
        # slepen, én dubbelklik op de kolomrand doet automatisch auto-fit
        # op inhoud — dit is ingebouwd Qt-gedrag (zoals Excel), maar werkt
        # ENKEL wanneer de resize-modus geen Stretch is. Vandaar geen
        # Stretch meer op "Omschrijving"/"Opmerking".
        for idx in range(self.table.columnCount()):
            header.setSectionResizeMode(idx, QHeaderView.Interactive)

        # Laatste kolom vult resterende (lege) ruimte i.p.v. een grijze
        # leegte rechts te laten — blokkeert het versleepbaar zijn van de
        # overige kolommen niet.
        header.setStretchLastSection(True)

        for row, record in enumerate(data):
            checkbox = QCheckBox()
            checkbox.setFocusPolicy(Qt.NoFocus)
            self.table.setCellWidget(row, 0, checkbox)
            for col_offset, (key, _label) in enumerate(ARTICLE_COLUMNS, start=1):
                val = record.get(key, "")
                val = f"{val:.2f}" if isinstance(val, float) else str(val if val is not None else "")
                cell = QTableWidgetItem(val)
                cell.setToolTip(val)
                self.table.setItem(row, col_offset, cell)

        if data:
            self.table.selectRow(0)

        # Initiële auto-fit op inhoud voor alle kolommen (net als Excel bij
        # het eerste openen) — nadien kan de gebruiker elke kolom vrij
        # aanpassen (slepen of dubbelklik-autofit op de kolomrand).
        self.table.resizeColumnsToContents()

        # "Leverancier Art.Nr." bewust smaller laten starten dan zijn
        # automatische breedte — blijft nadien manueel aanpasbaar.
        narrow_col_offset = next(
            (i for i, (key, _label) in enumerate(ARTICLE_COLUMNS, start=1) if key == NARROW_START_KEY),
            None
        )
        if narrow_col_offset is not None:
            natural_width = self.table.columnWidth(narrow_col_offset)
            self.table.setColumnWidth(narrow_col_offset, max(50, natural_width // 2))

        # Sorteerpijltje in header herstellen na herbouw van de tabel
        col_idx = self._sort_state.get("column_index")
        if col_idx is not None:
            order = Qt.AscendingOrder if self._sort_state["ascending"] else Qt.DescendingOrder
            header.setSortIndicatorShown(True)
            header.setSortIndicator(col_idx, order)

    # ===================== Sortering (dubbelklik op header) =====================
    def _on_header_double_clicked(self, logical_index: int):
        """
        Sorteert enkel op LastPurPrc / QtyPurchasedLast6Months /
        QtyPurchasedLast12Months (numeriek). Andere kolomheaders negeren
        de dubbelklik. Tweede dubbelklik op dezelfde kolom keert de
        richting om.
        """
        if logical_index == 0 or (logical_index - 1) >= len(ARTICLE_COLUMNS):
            return
        col_key, _label = ARTICLE_COLUMNS[logical_index - 1]
        if col_key not in SORTABLE_KEYS:
            return

        if self._sort_state.get("column_index") == logical_index:
            ascending = not self._sort_state["ascending"]
        else:
            ascending = True
        self._sort_state = {"column_index": logical_index, "ascending": ascending}

        self._filtered_data.sort(
            key=lambda rec: _numeric_sort_key(rec, col_key),
            reverse=not ascending
        )
        self._render_rows(self._filtered_data)

    # ===================== Verzamel-lijst (eigen, los van hoofdvenster) =====================
    def _toggle_select_all(self, checked: bool):
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(checked)

    def _collect_selected_rows(self):
        aantal_rijen = self.table.rowCount()
        if aantal_rijen == 0:
            QMessageBox.information(self, "Geen data", "Er staan geen rijen om te verzamelen.")
            return

        iets_aangevinkt = False
        for row in range(aantal_rijen):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox) and widget.isChecked():
                iets_aangevinkt = True
                row_values = []
                for col in range(1, self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_values.append(item.text() if item else "")
                joined = "\t".join(row_values)
                if joined not in self.collected_data:
                    self.collected_data.append(joined)

        if not iets_aangevinkt:
            QMessageBox.information(self, "Niets aangevinkt", "Vink eerst één of meerdere vakjes aan om toe te voegen.")
            return

        self._show_collected_dialog()

    def _clear_collected_list(self):
        if not self.collected_data:
            QMessageBox.information(self, "Lijst is al leeg", "Er staan momenteel geen rijen in de lijst.")
            return

        self.collected_data.clear()
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

        self.chk_select_all.blockSignals(True)
        self.chk_select_all.setChecked(False)
        self.chk_select_all.blockSignals(False)

        QMessageBox.information(self, "Lijst geleegd", "De verzamelde rijen zijn nu verwijderd en alle vakjes zijn uitgevinkt.")

    def _show_collected_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Verzamelde artikels (leverancier)")
        dialog.resize(1100, 400)

        headers = [lbl for _, lbl in ARTICLE_COLUMNS]

        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(self.collected_data))
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for r, line in enumerate(self.collected_data):
            parts = line.split("\t")
            for c, txt in enumerate(parts):
                table.setItem(r, c, QTableWidgetItem(txt))

        layout = QVBoxLayout(dialog)
        layout.addWidget(table)

        def copy_selection_to_clipboard():
            md = QMimeData()
            sel_rows = [idx.row() for idx in table.selectionModel().selectedRows()]
            if not sel_rows:
                sel_rows = list(range(table.rowCount()))

            tsv_lines = ["\t".join(headers)]
            for r in sel_rows:
                tsv_lines.append("\t".join(table.item(r, c).text() for c in range(table.columnCount())))
            md.setText("\n".join(tsv_lines))

            html = [
                "<html><head><meta charset='utf-8'></head><body>",
                "<table border='1' cellspacing='0' cellpadding='4' "
                "style='border-collapse:collapse; font-family:Arial,sans-serif; font-size:10pt;'>",
                "<thead><tr>"
            ]
            html += [
                f"<th style='background-color:#f0f0f0; border:1px solid #000; padding:4px;'>{h}</th>"
                for h in headers
            ]
            html.append("</tr></thead><tbody>")
            for r in sel_rows:
                html.append("<tr>")
                for c in range(table.columnCount()):
                    val = table.item(r, c).text()
                    html.append(f"<td style='border:1px solid #000; padding:4px;'>{val}</td>")
                html.append("</tr>")
            html.append("</tbody></table></body></html>")

            md.setHtml("".join(html))
            QApplication.clipboard().setMimeData(md)
            QMessageBox.information(dialog, "Klembord", "Gekopieerd als tabel (Outlook & Word compatibel).")

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        copy_btn = QPushButton("Alles kopiëren")
        copy_btn.clicked.connect(copy_selection_to_clipboard)
        close_btn = QPushButton("Sluiten")
        close_btn.clicked.connect(dialog.accept)
        btn_layout.addWidget(copy_btn)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        dialog.exec()