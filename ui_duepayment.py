# =============================================================================
# ArticleSearch
# File:    ui_duepayment.py
# Role:    GUI-venster "Betalingsgedrag & Openstaande Posten" (PaymentsDue),
#          geopend vanuit het Export-menu (ui_main.py). Twee tabs:
#            - "Klanten"     (standaard geladen): 1 rij per klant, gemiddelden
#                             (duepayment_info.get_payments_due_detail)
#            - "Facturen"    : 1 rij per factuur/voorschot
#                             (duepayment_info.get_payments_due_overview)
#          Per tab: filtervelden + knop "Ophalen" (GEEN automatische call bij
#          openen — data wordt pas bevraagd na klik, zelfde principe als
#          Open Elements/ui_docs.py). Kolomklik = sorteren (numeriek/datum-
#          bewust via UserRole-sortkey), live zoekbalk filtert alle kolommen.
#          Tab "Facturen" heeft bijkomend een filter op "Verschil vervaldatum"
#          (alles / enkel te laat / enkel correct betaald), client-side
#          gecombineerd met de zoekbalk. Export: "Exporteer..." (huidige tab)
#          / "Exporteer alles" (beide tabs) — formaatkeuze CSV / XLSX / Beide
#          via _ask_export_format(); na export wordt de bevattende map
#          automatisch geopend in de bestandsverkenner.
#          Zelfde AD-toegang als Open Elements (GPP_Finance) — check gebeurt
#          in ui_main.py._open_duepayment_window(), niet in dit bestand zelf.
#          Inputvelden "Aantal maanden"/"Klantcode" van de Klanten-tab worden
#          automatisch overgenomen naar de Facturen-tab (één richting).
#          Sneltoetsen: Ctrl+Return = Ophalen (actieve tab), Ctrl+E =
#          Exporteer... (actieve tab), Alt+1/Alt+2 = wissel tab, Esc = sluiten.
# Version: 1.3.0
# Author:  Bart Bossuyt
# Changes: 1.3.0 — Laatst gebruikte exportmap wordt onthouden (QSettings,
#                   org "CGK Group" / app "ArticleSearch", key
#                   "duepayment/last_export_dir") en automatisch voorgesteld
#                   als startmap bij een volgende export (_export_tab en
#                   _export_all) — zowel binnen dezelfde sessie als na een
#                   herstart van de app. Nieuwe helpers _last_export_dir()/
#                   _remember_export_dir().
# Changes: 1.2.0 — Dubbelklik op een rij in de Klanten-tab wisselt nu naar
#                   de Facturen-tab, vult diens Klantcode-filter in met de
#                   `CardCode` van de aangeklikte klant, en haalt automatisch
#                   de bijhorende facturen op (_on_detail_row_double_clicked,
#                   gekoppeld aan detail_table.cellDoubleClicked). Laat het
#                   "alle klanten"-resultaat op de Klanten-tab zelf
#                   ongewijzigd — enkel de Facturen-tab wordt gefilterd.
# Changes: 1.1.0 — Bijsturing: (1) map met geëxporteerde bestand(en)
#                   automatisch openen na export (_open_containing_folder,
#                   os.startfile — Windows). (2) Inputs "Aantal maanden"/
#                   "Klantcode" van tab Klanten worden nu automatisch
#                   overgenomen naar tab Facturen (one-way sync via
#                   textChanged). (3) Tabnaam "Documenten" hernoemd naar
#                   "Facturen" (ook sheet-naam/CSV-suffix bij export
#                   aangepast: "_documenten" -> "_facturen"). (4) Nieuwe
#                   filter "Verschil vervaldatum" (Alles / enkel positief =
#                   te laat / enkel negatief = correct betaald) in de
#                   Facturen-tab, client-side gecombineerd met de bestaande
#                   zoekbalk via nieuwe _apply_overview_filters(). (5)
#                   Sneltoetsen toegevoegd (waren nog niet aanwezig):
#                   Ctrl+Return (Ophalen, actieve tab), Ctrl+E (Exporteer...,
#                   actieve tab), Alt+1/Alt+2 (tab wisselen), Esc (sluiten).
# Changes: 1.0.0 — Eerste versie.
# =============================================================================
import csv
import os
import sys
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtCore import Qt, Signal, Slot, QSettings
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QFileDialog, QGroupBox
)

from duepayment_info import get_payments_due_detail, get_payments_due_overview

try:
    import openpyxl
    _HAS_OPENPYXL = True
except Exception:
    _HAS_OPENPYXL = False


# ----------------------------------------------------------------------
# Kolomdefinities: (data-key, kolomlabel, kind)  kind = "text" | "num" | "date"
# ----------------------------------------------------------------------
DETAIL_COLUMNS = [
    ("CardCode", "Klantcode", "text"),
    ("Klant", "Klant", "text"),
    ("BetalingsvoorwaardeKlantenfiche", "Betalingsvoorwaarde", "text"),
    ("AantalDocumenten", "Aantal documenten", "num"),
    ("AantalBetaald", "Aantal betaald", "num"),
    ("AantalOpen", "Aantal open", "num"),
    ("AantalAfwijkendVsKlantenfiche", "Afwijkend tov klantenfiche", "num"),
    ("GemDagenTotBetaling", "Gem. dagen tot betaling", "num"),
    ("GemVerschilVervaldatumVsBetaling", "Gem. verschil vervaldatum", "num"),
    ("TotaalBedrag", "Totaalbedrag", "num"),
    ("TotaalOpenstaand", "Totaal openstaand", "num"),
]

OVERVIEW_COLUMNS = [
    ("DocType", "Type", "text"),
    ("DocNum", "Docnr.", "num"),
    ("CardCode", "Klantcode", "text"),
    ("Klant", "Klant", "text"),
    ("DocDate", "Factuurdatum", "date"),
    ("DocDueDate", "Vervaldatum", "date"),
    ("DocTotal", "Totaalbedrag", "num"),
    ("PaidToDate", "Betaald", "num"),
    ("OpenAmount", "Openstaand", "num"),
    ("BetalingsvoorwaardeKlantenfiche", "Betalingsvw. klantenfiche", "text"),
    ("BetalingsvoorwaardeToegepast", "Betalingsvw. toegepast", "text"),
    ("AfwijkingVsKlantenfiche", "Afwijking", "text"),
    ("LastPaymentDate", "Laatste betaaldatum", "date"),
    ("TotalApplied", "Toegepast bedrag", "num"),
    ("DagenTotBetaling", "Dagen tot betaling", "num"),
    ("VerschilVervaldatumVsBetaling", "Verschil vervaldatum", "num"),
    ("Status", "Status", "text"),
    ("Maand", "Maand", "text"),
    ("Kwartaal", "Kwartaal", "text"),
    ("Semester", "Semester", "text"),
    ("Jaar", "Jaar", "text"),
]


def _fmt_date(raw):
    """'2025-10-22T00:00:00' -> '22-10-2025'; laat onbekende/lege waarden ongemoeid."""
    if not raw or not isinstance(raw, str):
        return "" if raw is None else str(raw)
    try:
        date_part = raw.split("T")[0]
        y, m, d = date_part.split("-")
        return f"{d}-{m}-{y}"
    except Exception:
        return raw


class _SortItem(QTableWidgetItem):
    """QTableWidgetItem met correcte sortering (numeriek/datum) via UserRole-sortkey."""

    def __lt__(self, other):
        try:
            return self.data(Qt.UserRole) < other.data(Qt.UserRole)
        except Exception:
            return super().__lt__(other)


class DuePaymentWindow(QWidget):
    fetch_success = Signal(list, str)   # (rows, tab_key)
    fetch_error = Signal(str, str)      # (message, tab_key)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Betalingsgedrag & Openstaande Posten")
        self.resize(1400, 800)

        self._exec = ThreadPoolExecutor(max_workers=2)

        # Onthoudt de laatst gebruikte exportmap (persistent, ook na herstart)
        self._settings = QSettings("CGK Group", "ArticleSearch")

        # Ruwe data per tab, bijgehouden voor export (respecteert geen filter,
        # export gebeurt op wat zichtbaar/geladen is in de tabel zelf)
        self._detail_rows: list = []
        self._overview_rows: list = []

        root = QVBoxLayout(self)

        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        # ---- Tab 1: Klanten (Detail, UIY02H) — standaard-tab ----
        self.detail_table = QTableWidget()
        self.detail_search = QLineEdit()
        self.detail_months = QLineEdit("24")
        self.detail_cardcode = QLineEdit()
        self.detail_due = QComboBox()
        detail_tab = self._build_detail_tab()
        self.tabs.addTab(detail_tab, "Klanten")

        # ---- Tab 2: Facturen (Overview, YCT5LR) ----
        self.overview_table = QTableWidget()
        self.overview_search = QLineEdit()
        self.overview_months = QLineEdit("24")
        self.overview_cardcode = QLineEdit()
        self.overview_diff_filter = QComboBox()
        overview_tab = self._build_overview_tab()
        self.tabs.addTab(overview_tab, "Facturen")

        # ---- Inputs Klanten-tab automatisch overnemen naar Facturen-tab ----
        self.detail_months.textChanged.connect(self.overview_months.setText)
        self.detail_cardcode.textChanged.connect(self.overview_cardcode.setText)

        # ---- Dubbelklik op klant (Klanten-tab) -> Facturen-tab, gefilterd op CardCode ----
        self.detail_table.cellDoubleClicked.connect(self._on_detail_row_double_clicked)

        # ---- Export alles (buiten de tabs, geldt voor beide) ----
        export_all_row = QHBoxLayout()
        export_all_row.addStretch(1)
        self.btn_export_all = QPushButton("Exporteer alles (beide tabs)")
        self.btn_export_all.clicked.connect(self._export_all)
        export_all_row.addWidget(self.btn_export_all)
        root.addLayout(export_all_row)

        self.fetch_success.connect(self._on_fetch_success)
        self.fetch_error.connect(self._on_fetch_error)

        # ---- Sneltoetsen ----
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._fetch_current_tab)
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._export_current_tab)
        QShortcut(QKeySequence("Alt+1"), self).activated.connect(lambda: self.tabs.setCurrentIndex(0))
        QShortcut(QKeySequence("Alt+2"), self).activated.connect(lambda: self.tabs.setCurrentIndex(1))
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.close)

    # ------------------------------------------------------------------
    # Tab-opbouw
    # ------------------------------------------------------------------
    def _build_detail_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        filt_box = QGroupBox("Filter")
        grid = QGridLayout(filt_box)
        grid.addWidget(QLabel("Aantal maanden:"), 0, 0)
        self.detail_months.setPlaceholderText("24")
        grid.addWidget(self.detail_months, 0, 1)
        grid.addWidget(QLabel("Klantcode:"), 0, 2)
        self.detail_cardcode.setPlaceholderText("leeg = alle klanten")
        grid.addWidget(self.detail_cardcode, 0, 3)
        grid.addWidget(QLabel("Betaalgedrag:"), 0, 4)
        self.detail_due.addItem("Alle klanten", "")
        self.detail_due.addItem("Enkel slechte betalers (te laat)", "0")
        self.detail_due.addItem("Enkel op tijd of vroeger", "1")
        grid.addWidget(self.detail_due, 0, 5)
        lay.addWidget(filt_box)

        actions = QHBoxLayout()
        btn_fetch = QPushButton("Ophalen")
        btn_fetch.clicked.connect(self._fetch_detail)
        btn_export = QPushButton("Exporteer...")
        btn_export.clicked.connect(lambda: self._export_tab("detail"))
        actions.addWidget(btn_fetch)
        actions.addWidget(btn_export)
        actions.addStretch(1)
        actions.addWidget(QLabel("Zoeken:"))
        self.detail_search.setPlaceholderText("filter over alle kolommen...")
        self.detail_search.textChanged.connect(lambda t: self._apply_text_filter(self.detail_table, t))
        actions.addWidget(self.detail_search, 1)
        lay.addLayout(actions)

        self._init_table(self.detail_table, DETAIL_COLUMNS)
        lay.addWidget(self.detail_table)
        return w

    def _build_overview_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)

        filt_box = QGroupBox("Filter")
        grid = QGridLayout(filt_box)
        grid.addWidget(QLabel("Aantal maanden:"), 0, 0)
        self.overview_months.setPlaceholderText("24")
        grid.addWidget(self.overview_months, 0, 1)
        grid.addWidget(QLabel("Klantcode:"), 0, 2)
        self.overview_cardcode.setPlaceholderText("leeg = alle klanten")
        grid.addWidget(self.overview_cardcode, 0, 3)
        grid.addWidget(QLabel("Verschil vervaldatum:"), 0, 4)
        self.overview_diff_filter.addItem("Alles", "")
        self.overview_diff_filter.addItem("Enkel te laat (positief)", "positive")
        self.overview_diff_filter.addItem("Enkel correct betaald (negatief/op tijd)", "negative")
        self.overview_diff_filter.currentIndexChanged.connect(lambda _i: self._apply_overview_filters())
        grid.addWidget(self.overview_diff_filter, 0, 5)
        lay.addWidget(filt_box)

        actions = QHBoxLayout()
        btn_fetch = QPushButton("Ophalen")
        btn_fetch.clicked.connect(self._fetch_overview)
        btn_export = QPushButton("Exporteer...")
        btn_export.clicked.connect(lambda: self._export_tab("overview"))
        actions.addWidget(btn_fetch)
        actions.addWidget(btn_export)
        actions.addStretch(1)
        actions.addWidget(QLabel("Zoeken:"))
        self.overview_search.setPlaceholderText("filter over alle kolommen...")
        self.overview_search.textChanged.connect(lambda _t: self._apply_overview_filters())
        actions.addWidget(self.overview_search, 1)
        lay.addLayout(actions)

        self._init_table(self.overview_table, OVERVIEW_COLUMNS)
        lay.addWidget(self.overview_table)
        return w

    # index van de kolom "VerschilVervaldatumVsBetaling" binnen OVERVIEW_COLUMNS
    _overview_diff_col_index = next(
        (i for i, c in enumerate(OVERVIEW_COLUMNS) if c[0] == "VerschilVervaldatumVsBetaling"), None
    )
    # index van de kolom "CardCode" binnen DETAIL_COLUMNS (voor dubbelklik -> Facturen-tab)
    _detail_cardcode_col_index = next(
        (i for i, c in enumerate(DETAIL_COLUMNS) if c[0] == "CardCode"), None
    )

    @Slot(int, int)
    def _on_detail_row_double_clicked(self, row: int, _column: int):
        """Dubbelklik op een klant (Klanten-tab): wissel naar Facturen-tab, gefilterd op die CardCode."""
        col = self._detail_cardcode_col_index
        if col is None:
            return
        item = self.detail_table.item(row, col)
        cardcode = item.text().strip() if item else ""
        if not cardcode:
            return

        self.overview_cardcode.setText(cardcode)
        self.tabs.setCurrentIndex(1)
        self._fetch_overview()

    @staticmethod
    def _init_table(table: QTableWidget, columns: list):
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels([c[1] for c in columns])
        table.setSortingEnabled(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectRows)
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Interactive)
        header.setStretchLastSection(True)

    # ------------------------------------------------------------------
    # Zoeken/filteren (live, alle kolommen)
    # ------------------------------------------------------------------
    @staticmethod
    def _apply_text_filter(table: QTableWidget, text: str):
        text = (text or "").strip().lower()
        for row in range(table.rowCount()):
            if not text:
                table.setRowHidden(row, False)
                continue
            match = False
            for col in range(table.columnCount()):
                item = table.item(row, col)
                if item and text in item.text().lower():
                    match = True
                    break
            table.setRowHidden(row, not match)

    def _apply_overview_filters(self):
        """Facturen-tab: combineert de zoekbalk MET de 'Verschil vervaldatum'-filter."""
        text = (self.overview_search.text() or "").strip().lower()
        diff_mode = self.overview_diff_filter.currentData() or ""
        diff_col = self._overview_diff_col_index

        for row in range(self.overview_table.rowCount()):
            visible = True

            if text:
                visible = False
                for col in range(self.overview_table.columnCount()):
                    item = self.overview_table.item(row, col)
                    if item and text in item.text().lower():
                        visible = True
                        break

            if visible and diff_mode and diff_col is not None:
                item = self.overview_table.item(row, diff_col)
                raw = item.data(Qt.UserRole) if item else None
                try:
                    val = float(raw)
                except (TypeError, ValueError):
                    val = None
                if diff_mode == "positive" and not (val is not None and val > 0):
                    visible = False
                elif diff_mode == "negative" and not (val is not None and val <= 0):
                    visible = False

            self.overview_table.setRowHidden(row, not visible)

    # ------------------------------------------------------------------
    # Sneltoetsen-helpers (actieve tab)
    # ------------------------------------------------------------------
    def _fetch_current_tab(self):
        if self.tabs.currentIndex() == 0:
            self._fetch_detail()
        else:
            self._fetch_overview()

    def _export_current_tab(self):
        if self.tabs.currentIndex() == 0:
            self._export_tab("detail")
        else:
            self._export_tab("overview")

    # ------------------------------------------------------------------
    # Ophalen
    # ------------------------------------------------------------------
    def _fetch_detail(self):
        months = self.detail_months.text().strip() or "24"
        cardcode = self.detail_cardcode.text().strip()
        due = self.detail_due.currentData()

        def _worker():
            try:
                rows = get_payments_due_detail(months=months, cardcode=cardcode, due=due)
                self.fetch_success.emit(rows, "detail")
            except Exception as e:
                self.fetch_error.emit(str(e), "detail")

        self._exec.submit(_worker)

    def _fetch_overview(self):
        months = self.overview_months.text().strip() or "24"
        cardcode = self.overview_cardcode.text().strip()

        def _worker():
            try:
                rows = get_payments_due_overview(months=months, cardcode=cardcode)
                self.fetch_success.emit(rows, "overview")
            except Exception as e:
                self.fetch_error.emit(str(e), "overview")

        self._exec.submit(_worker)

    @Slot(list, str)
    def _on_fetch_success(self, rows: list, tab_key: str):
        if tab_key == "detail":
            self._detail_rows = rows
            self._populate_table(self.detail_table, DETAIL_COLUMNS, rows)
            self._apply_text_filter(self.detail_table, self.detail_search.text())
        else:
            self._overview_rows = rows
            self._populate_table(self.overview_table, OVERVIEW_COLUMNS, rows)
            self._apply_overview_filters()

        if not rows:
            QMessageBox.information(self, "Geen resultaten", "Geen documenten/klanten gevonden voor deze filters.")

    @Slot(str, str)
    def _on_fetch_error(self, msg: str, tab_key: str):
        QMessageBox.critical(self, "Fout bij ophalen", msg)

    def _populate_table(self, table: QTableWidget, columns: list, rows: list):
        table.setSortingEnabled(False)
        table.setRowCount(len(rows))
        for r, row_data in enumerate(rows):
            for c, (key, _label, kind) in enumerate(columns):
                raw = row_data.get(key)
                if kind == "date":
                    display = _fmt_date(raw)
                    sort_key = raw if isinstance(raw, str) else ""
                elif kind == "num":
                    display = "" if raw is None else str(raw)
                    try:
                        sort_key = float(raw)
                    except (TypeError, ValueError):
                        sort_key = float("-inf")
                else:
                    display = "" if raw is None else str(raw)
                    sort_key = display.lower()

                item = _SortItem(display)
                item.setData(Qt.UserRole, sort_key)
                table.setItem(r, c, item)
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def _ask_export_format(self) -> set:
        """Toont een keuzedialoog CSV / XLSX / Beide. Retourneert bv. {'csv'}, {'xlsx'} of {'csv','xlsx'}."""
        box = QMessageBox(self)
        box.setWindowTitle("Exportformaat")
        box.setText("Kies het exportformaat:")
        btn_csv = box.addButton("CSV", QMessageBox.ActionRole)
        btn_xlsx = box.addButton("XLSX", QMessageBox.ActionRole)
        btn_both = box.addButton("Beide", QMessageBox.ActionRole)
        box.addButton("Annuleer", QMessageBox.RejectRole)
        box.exec()

        clicked = box.clickedButton()
        if clicked is btn_csv:
            return {"csv"}
        if clicked is btn_xlsx:
            return {"xlsx"}
        if clicked is btn_both:
            return {"csv", "xlsx"}
        return set()

    @staticmethod
    def _visible_rows_as_dicts(table: QTableWidget, columns: list) -> list:
        """Geeft de huidige (gesorteerde/gefilterde) tabelinhoud terug als lijst van dicts."""
        result = []
        for row in range(table.rowCount()):
            if table.isRowHidden(row):
                continue
            row_dict = {}
            for col, (key, _label, _kind) in enumerate(columns):
                item = table.item(row, col)
                row_dict[key] = item.text() if item else ""
            result.append(row_dict)
        return result

    def _write_csv(self, path: str, columns: list, rows: list):
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow([label for _key, label, _kind in columns])
            for row in rows:
                writer.writerow([row.get(key, "") for key, _label, _kind in columns])

    def _write_xlsx(self, path: str, sheets: dict):
        """sheets: {sheet_naam: (columns, rows)}"""
        if not _HAS_OPENPYXL:
            QMessageBox.critical(self, "Ontbrekende library", "openpyxl is niet beschikbaar — XLSX-export niet mogelijk.")
            return False
        wb = openpyxl.Workbook()
        wb.remove(wb.active)
        for sheet_name, (columns, rows) in sheets.items():
            ws = wb.create_sheet(title=sheet_name[:31])
            ws.append([label for _key, label, _kind in columns])
            for row in rows:
                ws.append([row.get(key, "") for key, _label, _kind in columns])
        wb.save(path)
        return True

    @staticmethod
    def _open_containing_folder(path: str):
        """Opent de map van het geëxporteerde bestand in de bestandsverkenner (Windows)."""
        try:
            folder = os.path.dirname(os.path.abspath(path))
            if hasattr(os, "startfile"):
                os.startfile(folder)  # type: ignore[attr-defined]
        except Exception:
            pass  # niet-fataal — export zelf is al gelukt

    def _last_export_dir(self) -> str:
        """Laatst gebruikte exportmap (leeg indien nog nooit geëxporteerd)."""
        val = self._settings.value("duepayment/last_export_dir", "")
        return val or ""

    def _remember_export_dir(self, path: str):
        """Onthoudt de map van 'path' als laatst gebruikte exportmap."""
        try:
            folder = os.path.dirname(os.path.abspath(path))
            self._settings.setValue("duepayment/last_export_dir", folder)
        except Exception:
            pass

    def _export_tab(self, tab_key: str):
        table = self.detail_table if tab_key == "detail" else self.overview_table
        columns = DETAIL_COLUMNS if tab_key == "detail" else OVERVIEW_COLUMNS
        sheet_name = "Klanten" if tab_key == "detail" else "Facturen"

        rows = self._visible_rows_as_dicts(table, columns)
        if not rows:
            QMessageBox.information(self, "Geen data", "Er is niets om te exporteren — klik eerst op 'Ophalen'.")
            return

        formats = self._ask_export_format()
        if not formats:
            return

        last_dir = self._last_export_dir()
        default_name = os.path.join(last_dir, sheet_name) if last_dir else sheet_name
        base_path, _ = QFileDialog.getSaveFileName(self, "Exporteren", default_name, "Alle bestanden (*)")
        if not base_path:
            return
        base_path = os.path.splitext(base_path)[0]

        if "csv" in formats:
            self._write_csv(f"{base_path}.csv", columns, rows)
        if "xlsx" in formats:
            self._write_xlsx(f"{base_path}.xlsx", {sheet_name: (columns, rows)})

        self._remember_export_dir(base_path)
        QMessageBox.information(self, "Export voltooid", f"Bestand(en) opgeslagen als:\n{base_path}.[csv/xlsx]")
        self._open_containing_folder(base_path)

    def _export_all(self):
        detail_rows = self._visible_rows_as_dicts(self.detail_table, DETAIL_COLUMNS)
        overview_rows = self._visible_rows_as_dicts(self.overview_table, OVERVIEW_COLUMNS)

        if not detail_rows and not overview_rows:
            QMessageBox.information(self, "Geen data", "Er is niets om te exporteren — klik eerst op 'Ophalen' in minstens 1 tab.")
            return

        formats = self._ask_export_format()
        if not formats:
            return

        last_dir = self._last_export_dir()
        default_name = os.path.join(last_dir, "Betalingsgedrag") if last_dir else "Betalingsgedrag"
        base_path, _ = QFileDialog.getSaveFileName(self, "Exporteer alles", default_name, "Alle bestanden (*)")
        if not base_path:
            return
        base_path = os.path.splitext(base_path)[0]

        if "csv" in formats:
            if detail_rows:
                self._write_csv(f"{base_path}_klanten.csv", DETAIL_COLUMNS, detail_rows)
            if overview_rows:
                self._write_csv(f"{base_path}_facturen.csv", OVERVIEW_COLUMNS, overview_rows)
        if "xlsx" in formats:
            sheets = {}
            if detail_rows:
                sheets["Klanten"] = (DETAIL_COLUMNS, detail_rows)
            if overview_rows:
                sheets["Facturen"] = (OVERVIEW_COLUMNS, overview_rows)
            self._write_xlsx(f"{base_path}.xlsx", sheets)

        self._remember_export_dir(base_path)
        QMessageBox.information(self, "Export voltooid", f"Bestand(en) opgeslagen met basisnaam:\n{base_path}")
        self._open_containing_folder(base_path)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = DuePaymentWindow()
    w.showMaximized()
    sys.exit(app.exec())