# =============================================================================
# ArticleSearch
# File:    ui_main.py
# Role:    Hoofdvenster (QMainWindow) — zoekscherm, resultatentabel, menu-
#          balk, en het openen van alle submodules (Detail, BP, Project,
#          VTA, Peppol, Timings, Elements, Credit Control, Prod Stock
#          Overview).
# Version: 1.13.0
# Author:  Bart Bossuyt
# Changes: 1.13.0 — BUGFIX (Prod Stock Overview): "LISA Qty" bleef breed
#                    ondanks PROD_COLUMN_WIDTHS (70px). Oorzaak: de
#                    hoofdtabel had `header.setStretchLastSection(True)`
#                    staan voor de Prod-weergave (overgenomen van de
#                    Artikel-tabel), waardoor Qt de laatst zichtbare kolom
#                    — toevallig altijd "LISA Qty" — sowieso alle
#                    overblijvende breedte laat opvullen, ongeacht een
#                    nadien expliciet ingestelde `setColumnWidth()`.
#                    `_populate_prod_rows()` zet nu `setStretchLastSection
#                    (False)`, zodat "LISA Qty" gewoon zijn ingestelde
#                    breedte (header-tekst) behoudt.
# Changes: 1.12.0 — Prod Stock Overview:
#                    - Kolombreedtes: "LISA_Qty" veel smaller (70px, staat
#                      vaak leeg/kort), "U_customText"/"Opmerking" breder
#                      (260px, is een vrije-tekstveld NVARCHAR 255).
#                      PROD_NARROW_COLUMNS hernoemd/uitgebreid naar
#                      PROD_COLUMN_WIDTHS (expliciete breedte per kolom,
#                      niet enkel "smaller").
#                    - Standaard sortering op Art.Nr. (oplopend) bij elke
#                      laad-/filteractie in _render_prod_table(), i.p.v. de
#                      ruwe, ongesorteerde API-volgorde. Gebruikt dezelfde
#                      sorteersleutel als _sort_prod_column(), zodat een
#                      volgende dubbelklik op de kolomkop "Art.Nr."
#                      consistent verder bouwt op deze basis (eerste
#                      dubbelklik keert dan om naar aflopend).
# Changes: 1.11.0 — Prod Stock Overview: nieuw API-veld "U_customText"
#                    toegevoegd aan PROD_STOCK_COLUMNS, als kolom
#                    "Opmerking" tussen "Niet CGK" en "Stock Algemeen"
#                    (volgorde uit de API-respons). Nieuwe
#                    PROD_NARROW_COLUMNS-map: deze kolom wordt na
#                    resizeColumnsToContents() expliciet smaller gezet
#                    (90px) i.p.v. de standaard auto-fit-breedte — op
#                    vraag van gebruiker.
# Changes: 1.10.0 — Prod Stock Overview: kolomklik-sortering (SORT-PROD-1)
#                    toegevoegd, analoog aan SORT-1 bij Artikel — dubbelklik
#                    op de kolomkop "Art.Nr." of "Omschrijving" sorteert de
#                    (reeds gefilterde) tabel, tweede dubbelklik op dezelfde
#                    kolom keert de richting om. `_on_table_header_double_
#                    clicked()` routeert nu per search-type naar
#                    `_sort_article_column()` (hernoemd, was inline) of de
#                    nieuwe `_sort_prod_column()`. `_render_prod_table()`
#                    opgesplitst in filterstap + nieuwe `_populate_prod_
#                    rows()` (tabelopbouw), zodat sorteren de tabel kan
#                    herbouwen zonder de tekst-/magazijnfilter opnieuw toe
#                    te passen. Nieuwe sorteerstatus `self._prod_sort_state`
#                    (analoog `_article_sort_state`), reset bij elke nieuwe
#                    filter-/laadactie.
# Changes: 1.9.0 — Prod Stock Overview: nieuwe kleurregel — "Stock vandaag"
#                   (StockHeden) krijgt een gele celachtergrond wanneer de
#                   waarde lager is dan "Min. SAP" (MinSAP) op diezelfde
#                   rij. Toegevoegd in _render_prod_table(), naast de
#                   bestaande regels (Min. SAP > 0 => groen, Stock
#                   Algemeen < 1 => rood).
# Changes: 1.8.0 — Prod Stock Overview: sneltoetsen toegevoegd, consistent
#                   met de andere vensters. Nieuw: Ctrl+E exporteert het
#                   huidige overzicht naar Excel (enkel actief bij
#                   search-type "Prod", zelfde toets als bij PaymentsDue).
#                   "Delete" wist voortaan de Prod-resultaatfilter
#                   (self.prod_filter_input) i.p.v. het verborgen
#                   zoekterm-veld wanneer search-type "Prod" actief is
#                   (analoog aan "Ctrl+D = Filters wissen" bij CC BP).
#                   Ctrl+Enter (bestaand, globaal) werkte al voor Prod
#                   ("Zoeken"/data ophalen) — geen wijziging nodig.
# Changes: 1.7.0 — Prod Stock Overview: GEEN apart ProdStockWindow-popup
#                   meer (op vraag van gebruiker: "alles in het zelfde
#                   scherm, geen pop-up"). Resultaten verschijnen nu
#                   rechtstreeks in de bestaande hoofdtabel (self.table),
#                   zelfde tabel als Artikel/BP, incl. "Selectie"-checkbox-
#                   kolom (herbruikbaar met "Voeg toe aan lijst"/kopiëren).
#                   3 nieuwe widgets, enkel zichtbaar bij search-type
#                   "Prod" (nieuwe grid-rijen 5 en 6): "Magazijn:"
#                   (self.prod_warehouse_select — wisselt enkel de
#                   zichtbare Stock_*-kolom, geen nieuwe API-call) en
#                   "Filter:" (self.prod_filter_input — client-side
#                   tekstfilter op Art.Nr./Omschrijving op de reeds
#                   geladen data, geen nieuwe API-call). Nieuwe knop
#                   "Exporteer naar Excel" (self.prod_export_button,
#                   naast de bestaande collect-knoppen) enkel zichtbaar bij
#                   "Prod". "Zoeken" haalt de data 1x op
#                   (prod_info.get_prod_stock_overview()) en cachet ze in
#                   self._prod_raw_data; magazijn-/tekstfilter renderen
#                   enkel opnieuw (_render_prod_table()), zonder herhaalde
#                   API-calls. NIEUWE kleurregel: "Stock Algemeen" < 1 =>
#                   lichtrode celachtergrond (naast de bestaande "Min. SAP"
#                   > 0 => lichtgroen). ⚠️ ui_prod_stock.py (het vorige
#                   popup-venster) wordt hierdoor niet langer geïmporteerd/
#                   gebruikt vanuit ui_main.py — mag uit het project
#                   verwijderd worden (zie context-document).
# Changes: 1.6.0 — Prod Stock Overview: nieuwe search-type "Prod" toegevoegd
#                   aan self.search_type_select. Wanneer gekozen: het
#                   zoekterm-veld/Zoekmodus/Toon-voorraad worden verborgen en
#                   een nieuwe "Dataset:"-keuzelijst (self.prod_dataset_select)
#                   verschijnt i.p.v., gevuld via prod_info.list_datasets()
#                   en voorgeselecteerd/gefilterd o.b.v.
#                   settings.load_prod_default_dataset_name()/_owner() (zie
#                   _populate_prod_dataset_combo()). Op "Zoeken" wordt een
#                   onafhankelijk ProdStockWindow-venster geopend voor de
#                   geselecteerde dataset (analoog aan het bestaande
#                   VTA-patroon: setParent(None) + Qt.Window, toegevoegd aan
#                   self.detail_windows). zoekterm_label is nu een self-
#                   attribuut (was lokale variabele) zodat hij mee
#                   verborgen/getoond kan worden. perform_search() se
#                   "if not zoekterm: return"-guard overslaat deze check nu
#                   bewust voor search-type "Prod" (geen zoekterm nodig,
#                   enkel een datasetkeuze).
# Changes: 1.5.0 — BUGFIX (vervolg OITMI-Upload-prefill): VENDORID/
#                   VENDORNAME bleven leeg in de OITMI Upload-dialoog
#                   wanneer een artikel nog geen aankoophistorie (RET) had
#                   — de "Vendor Nr"-kolom uit de zoekresultatentabel zelf
#                   (SuppCatNum/SUPPLIERIDPRODUCT + SUPPLIERNAME) werd
#                   nergens doorgegeven aan DetailWindow. handle_row_
#                   double_click() geeft nu vendor_hint_id/vendor_hint_name
#                   mee vanuit de ruwe rijdata (self._last_article_data,
#                   al aanwezig sinds SORT-1) — geen extra API-call nodig.
#                   Zie ui_detail.py v1.3.0 voor de bijhorende fallback-
#                   volgorde.
# Changes: 1.4.0 — PaymentsDue: nieuw submenu-item "Betalingsgedrag..." onder
#                   Export, naast "Open Elements" en "Open Credit Control
#                   (CC BP)". Opent DuePaymentWindow (ui_duepayment.py) —
#                   zelfde AD-toegangscontrole als "Open Elements"
#                   (GPP_Finance) en zelfde offline-check, via nieuwe
#                   handler _open_duepayment_window() (analoog
#                   _open_docs_window()). Nieuwe import: DuePaymentWindow.
# Changes: 1.3.0 — WHATSNEW-1: "Wat is er nieuw?"-knop toegevoegd op 2
#                   plekken. (1) Opstart-popup bij een beschikbare update:
#                   de kale QMessageBox uit updater.py vervangen door een
#                   eigen dialoog (_show_update_available_dialog) met
#                   knoppen "Update nu" / "Wat is er nieuw?" / "Later" —
#                   check_for_update() wordt nu via callback aangeroepen
#                   (_check_for_update_startup) i.p.v. rechtstreeks.
#                   (2) Help → Over...: naast de bestaande "Update nu"-knop
#                   komt een gelijkaardige "Wat is er nieuw?"-knop, met
#                   dezelfde enable/disable-callback. Beide plekken
#                   hergebruiken één centrale dialoog (_show_whatsnew_dialog)
#                   die de release notes (body) van de laatste GitHub
#                   Release toont via updater.fetch_release_notes() —
#                   remote content, niet te verwarren met de lokale
#                   Changelog-dialoog (geschiedenis van de geïnstalleerde
#                   versie, ongewijzigd). Fallback bij lege/ontbrekende
#                   release notes: knop "Open op GitHub" (html_url).
# Changes: 1.2.0 — MINWHS-KLEUR-1: de "Min.Whs"-kolom (QTYMININV, enkel
#                   zichtbaar bij Toon voorraad = S) kleurt lichtgroen
#                   wanneer de waarde > 0 — dit betekent dat het een
#                   "standaard artikel" is. Tooltip op de cel legt dit
#                   expliciet uit. KOLOMBREEDTE-1: alle kolommen in de
#                   Artikel-resultatentabel zijn nu vrij versleepbaar en
#                   dubbelklik-autofit-baar (QHeaderView.Interactive),
#                   i.p.v. de vorige hardgecodeerde Stretch op kolomindex 2
#                   — analoog aan het patroon in ui_bp_articles_tab.py.
#                   Auto-fit op inhoud bij eerste weergave via
#                   resizeColumnsToContents(); laatste kolom vult de
#                   resterende ruimte (setStretchLastSection). Kolom 0
#                   (checkbox "Selectie") blijft ResizeToContents. Let op:
#                   net als in ui_bp_articles_tab.py gaan handmatige
#                   kolombreedte-aanpassingen van de gebruiker verloren bij
#                   een nieuwe zoekactie of sortering — bestaande, bewuste
#                   beperking, hier niet aangepakt (niet gevraagd).
# Changes: 1.1.1 — BUGFIX: searchtype-vergelijking in de no-stock-popup
#                   (perform_search) gebruikte "Standaard", terwijl de
#                   combobox self.search_type_select als itemtekst
#                   "Artikel" gebruikt (addItems(["Artikel", "Project",
#                   "BP", "VTA"])) — de voorwaarde was hierdoor nooit True
#                   en de "geen voorraad"-melding verscheen nooit. Fix:
#                   "Standaard" -> "Artikel". Popup-tekst tegelijk
#                   uitgebreid met de instructie om "Toon voorraad" op "R"
#                   te zetten en opnieuw te zoeken.
# Changes: 1.1.0 — SORT-1: dubbelklik op kolomheader "Art.Nr.", "Qty",
#                   "Prijs" of "Leverancier" in de Artikel-resultatentabel
#                   sorteert nu op die kolom (numeriek voor Qty/Prijs,
#                   alfabetisch voor Art.Nr./Leverancier). Tweede dubbelklik
#                   op dezelfde kolom keert de richting om. Sorteert op de
#                   ruwe data (vóór weergave-opmaak), niet op de getoonde
#                   tekst. Sorteerstatus wordt gereset bij elke nieuwe
#                   zoekactie. Enkel actief voor search-type "Artikel";
#                   overige kolommen (Omschrijving, Vendor Nr., Magazijn,
#                   Loc., Min.Whs, Max.Whs, Opmerking) blijven bewust
#                   niet-sorteerbaar (op vraag van gebruiker, niet
#                   gevraagd/nodig).
# Changes: 1.0.0 — Baseline: bestaande functionaliteit vóór introductie van
#                   versiebeheer in commentaar (voorheen enkel informele
#                   datumcode "05022026_001" bovenaan). Voorgeschiedenis niet
#                   gedocumenteerd per deelversie — vanaf nu wel.
# =============================================================================
import webbrowser
import os
import sys
import json
import logging
import markdown

from permissions_azure import list_user_groups, user_in_azure_group

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QDialog, QStatusBar, QMenu, QApplication,
    QHeaderView, QInputDialog, QCheckBox, QTextBrowser, QSizePolicy,
    QAbstractItemView, QTextEdit, QFileDialog,
    QGridLayout
)
from PySide6.QtGui import QShortcut, QKeySequence, QMovie, QIcon, QColor
from PySide6.QtCore import QEvent, Qt, QPoint, QTimer, QFileSystemWatcher, QMimeData

from data_request import send_data_request
from ui_detail import DetailWindow
from stock_info import get_item_detail_stockinfo
from settings import (
    load_environment, save_environment,
    load_show_stock, save_show_stock,
    load_detail_modal, save_detail_modal,
    load_default_search_type, save_default_search_type,
    load_language, load_bp_default_type, save_bp_default_type
)
from label.label_generator import generate_label
from label.label_settings_dialog import LabelSettingsDialog
from version import __version__
from updater import check_for_update, download_latest_release, fetch_release_notes, OWNER, REPO
from bug_report_dialog import BugDialog
from github_cases import show_github_cases
from file_editor_dialog import FileEditorDialog
from help_dialogs import show_help_dialog
from settings_dialog import show_settings_dialog
from translations import get_labels
from project_ui import ProjectWindow
from ui_bp import BpWindow
from ui_docs import DocsWindow
from ui_vta import PoWidget
from ui_CcBP import CreditControlWindow
from ui_peppol import PepWidget  # ✅ NIEUW: Peppol check venster
from ui_duepayment import DuePaymentWindow  # ✅ NIEUW: Betalingsgedrag & Openstaande Posten
from config import OFFLINE_MODE
from settings import load_column_headers_s, load_column_headers_default
from settings import load_prod_default_warehouse  # ✅ NIEUW: Prod Stock Overview (inline, geen popup)
from prod_info import get_prod_stock_overview, parse_artnbr  # ✅ NIEUW: Prod Stock Overview


# ---- Logging ----
logger = logging.getLogger("ArticleSearch.UI")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(levelname)s] %(asctime)s - [ArticleSearch.UI] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

COLUMN_HEADERS_S = load_column_headers_s()
COLUMN_HEADERS_DEFAULT = load_column_headers_default()

# SORT-1: kolommen waarop dubbelklik-sortering is toegestaan in de Artikel-
# resultatentabel. Matcht op de *weergegeven* headertekst (afkomstig uit
# settings.load_column_headers_s()/_default()) — pas deze set aan indien de
# labels in settings.py ooit hernoemd worden.
SORTABLE_ARTICLE_HEADER_LABELS = {"Art.Nr.", "Qty", "Prijs", "Leverancier"}
PROD_SORTABLE_HEADER_LABELS = {"Art.Nr.", "Omschrijving"}  # SORT-PROD-1

# --- Prod Stock Overview (search-type "Prod") — kolomdefinities/kleuren ---
# ✅ NIEUW: geen apart ProdStockWindow-venster meer — resultaten worden
# rechtstreeks in de hoofdtabel (self.table) getoond, zelfde tabel als
# Artikel/BP.
PROD_WAREHOUSE_COLUMNS = ["Stock_Algemeen", "Stock_Antwerpen", "Stock_Miami"]

PROD_STOCK_COLUMNS = [
    ("ArtCode", "Art.Nr."),
    ("Omschrijving", "Omschrijving"),
    ("StockHeden", "Stock vandaag"),
    ("MinSAP", "Min. SAP"),
    ("MaxSAP", "Max. SAP"),
    ("MaxRek", "Max. rek"),
    ("TotaalStock", "Totaal stock"),
    ("Gereserveerd", "Gereserveerd"),
    ("InBestelling", "In bestelling"),
    ("Beschikbaar", "Beschikbaar"),
    ("KGOpVoorraad", "Kg op voorraad"),
    ("BENPlatenPerPallet", "Platen/pallet"),
    ("NietCgk", "Niet CGK"),
    ("U_customText", "Opmerking"),
    ("Stock_Algemeen", "Stock Algemeen"),
    ("Stock_Antwerpen", "Stock Antwerpen"),
    ("Stock_Miami", "Stock Miami"),
    ("LISA_Qty", "LISA Qty"),
]

# Vaste kolombreedtes (px) die na resizeColumnsToContents() bewust
# afwijken van de auto-fit-breedte:
# - "U_customText" is een vrije-tekstveld (NVARCHAR 255) -> breder tonen.
# - "LISA_Qty" staat vaak leeg/kort -> veel smaller tonen.
PROD_COLUMN_WIDTHS = {
    "U_customText": 260,
    "LISA_Qty": 70,
}

PROD_NUMERIC_KEYS = {
    "StockHeden", "MinSAP", "MaxSAP", "MaxRek", "TotaalStock", "Gereserveerd",
    "InBestelling", "Beschikbaar", "KGOpVoorraad", "BENPlatenPerPallet",
    "Stock_Algemeen", "Stock_Antwerpen", "Stock_Miami", "LISA_Qty",
}

PROD_MIN_SAP_GREEN = QColor("#d9f2d9")     # Min. SAP > 0 => lichtgroen
PROD_STOCK_ALG_RED = QColor("#f5c6cb")     # Stock Algemeen < 1 => lichtrood
PROD_STOCK_HEDEN_YELLOW = QColor("#fff3b0")  # Stock vandaag < Min. SAP => geel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ✅ voorkomt crash bij moveEvent
        self.detail_windows = []
        self.upload_windows = []
        self.bp_windows = []
        self.docs_windows = []
        self.project_window = None
        self.collected_data = []

        # ✅ NIEUW: Peppol windows bijhouden zodat ze niet verdwijnen
        self.pep_windows = []

        # ✅ NIEUW: PaymentsDue-vensters bijhouden zodat ze niet verdwijnen
        self.duepayment_windows = []

        # SORT-1: state voor dubbelklik-sortering in de Artikel-resultatentabel
        self._last_article_data = []       # ruwe data (list[dict]) van laatste zoekactie
        self._last_article_columns = []    # data-keys in dezelfde volgorde als de kolommen
        self._article_sort_state = {"column_index": None, "ascending": True}

        # SORT-PROD-1: idem voor de Prod-resultatentabel (Art.Nr./Omschrijving)
        self._last_prod_data = []
        self._last_prod_columns = []
        self._prod_sort_state = {"column_index": None, "ascending": True}

        # ✅ Azure AD initialisatie
        try:
            _ = list_user_groups()
            print("[AD] Azure AD module geladen (groepen worden later opgehaald).")
        except Exception as e:
            print(f"[AD] ⚠️ Fout bij initialisatie Azure AD: {e}")

        # -----------------------
        # UI setup
        # -----------------------
        labels = get_labels(load_language())
        self.setStatusBar(QStatusBar(self))

        # WHATSNEW-1: eigen dialoog i.p.v. de kale QMessageBox uit
        # updater.py — via callback zodat wij de UI bepalen (knoppen
        # "Update nu" / "Wat is er nieuw?" / "Later").
        QTimer.singleShot(1000, self._check_for_update_startup)
        self.update_btn = QPushButton(labels["buttons"]["update_now"])
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(lambda: download_latest_release(self))

        self.setWindowTitle("Artikelzoeker")
        icon_path = os.path.join(os.path.dirname(__file__), "assets", "stocks.png")
        self.setWindowIcon(QIcon(icon_path))
        self.resize(1400, 800)

        css_path = os.path.join(os.path.dirname(__file__), "assets", "css", "style.qss")
        if os.path.exists(css_path):
            with open(css_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        base_css = os.path.join(os.path.dirname(__file__), "assets", "css")
        self._style_qss = os.path.join(base_css, "style.qss")
        self._detail_qss = os.path.join(base_css, "detail.qss")
        self._upload_qss = os.path.join(base_css, "upload.qss")

        self._qss_watcher = QFileSystemWatcher(self)
        for path in (self._style_qss, self._detail_qss, self._upload_qss):
            if os.path.exists(path):
                self._qss_watcher.addPath(path)
        self._qss_watcher.fileChanged.connect(self._on_qss_file_changed)

        self._center_window()
        self._create_menu_bar()
        self._create_main_layout()

        if load_environment() == "test":
            self.setStyleSheet(self.styleSheet() + "QMainWindow { background-color: #ffeeee; }")

        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.perform_search)
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self._generate_label)
        QShortcut(QKeySequence("F1"), self).activated.connect(lambda: show_help_dialog(self))
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self._open_selected_row)
        # NIEUW (Prod Stock Overview): Ctrl+E = exporteren, consistent met
        # PaymentsDue/andere vensters ("Ctrl+E = Exporteer..."). Enkel actief
        # bij search-type "Prod" — zie _prod_export_shortcut().
        QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self._prod_export_shortcut)

        self.installEventFilter(self)
        self.input_field.installEventFilter(self)

    # ---------- OVERRIDES ----------
    def moveEvent(self, event):
        super().moveEvent(event)
        for dlg in getattr(self, "detail_windows", []):
            try:
                if dlg.isVisible():
                    self._reposition_detail(dlg)
            except Exception:
                pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for dlg in getattr(self, "detail_windows", []):
            try:
                if dlg.isVisible():
                    self._reposition_detail(dlg)
            except Exception:
                pass

    # ---------- QSS Reload ----------
    def _on_qss_file_changed(self, path: str):
        """Herlaadt gewijzigde QSS-bestanden."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                qss = f.read()
        except Exception:
            QTimer.singleShot(500, lambda: self._retry_reload(path))
            return

        if path == self._style_qss:
            self.setStyleSheet(qss)
        elif path == self._detail_qss:
            for dlg in self.detail_windows:
                dlg.setStyleSheet(qss)
        elif path == self._upload_qss:
            for uw in self.upload_windows:
                uw.setStyleSheet(qss)

    def _retry_reload(self, path: str):
        if os.path.exists(path):
            self._on_qss_file_changed(path)

    # ---------- Basis UI ----------
    def _center_window(self):
        frame = self.frameGeometry()
        center = self.screen().availableGeometry().center()
        frame.moveCenter(center)
        self.move(frame.topLeft())

    def _create_menu_bar(self):
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&Bestand")
        file_menu.addAction("A&fsluiten").triggered.connect(self.close)

        settings_menu = menubar.addMenu("&Instellingen")
        settings_menu.addAction("⚙️ &Kies omgeving (test/live)").triggered.connect(self._choose_environment)
        settings_menu.addAction("🛠️ &Instellingen wijzigen...").triggered.connect(lambda: show_settings_dialog(self))
        settings_menu.addAction("🏷️ &Label-instellingen...").triggered.connect(self._show_label_settings_dialog)
        settings_menu.addSeparator()
        settings_menu.addAction("✏️ Bewerk style.qss").triggered.connect(self._open_style_qss_editor)
        settings_menu.addAction("✏️ Bewerk detail.qss").triggered.connect(self._open_detail_qss_editor)
        settings_menu.addAction("✏️ Bewerk upload.qss").triggered.connect(self._open_upload_qss_editor)

        export_menu = menubar.addMenu("&Export")
        export_menu.addAction("Open &Elements").triggered.connect(self._open_docs_window)
        export_menu.addAction("Open Credit Control (CC BP)").triggered.connect(self._open_ccbp_window)
        export_menu.addAction("Betalingsgedrag...").triggered.connect(self._open_duepayment_window)
        export_menu.addSeparator()

        # --- Tools ---
        tools_menu = menubar.addMenu("&Tools")
        tools_menu.addAction("🕒 Timings (urenregistratie)").triggered.connect(self._open_timings_window)

        # ✅ NIEUW: Peppol check
        tools_menu.addAction("📨 API check").triggered.connect(self._open_peppol_check_window)

        report_menu = menubar.addMenu("&Rapporteren")
        report_menu.addAction("🐞 &Bug of feature melden...").triggered.connect(self._show_bug_report_dialog)
        report_menu.addSeparator()
        report_menu.addAction("Show open cases").triggered.connect(lambda: show_github_cases(self))

        help_menu = menubar.addMenu("&Help")
        help_menu.addAction("&Help").triggered.connect(lambda: show_help_dialog(self))
        help_menu.addAction("&Over...").triggered.connect(self._show_about_dialog)
        help_menu.addAction("📄 &Changelog...").triggered.connect(self._show_changelog_dialog)

        if OFFLINE_MODE:
            offline_label = QLabel(" OFFLINE ")
            offline_label.setStyleSheet(
                "color: white; background-color: #c0392b; font-weight: bold; "
                "border-radius: 4px; padding: 2px 8px; margin-right: 10px;"
            )
            menubar.setCornerWidget(offline_label, Qt.TopRightCorner)

    def _create_main_layout(self):
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(
            "Geef zoekterm in… geen prefix = zoeken op art.nr., * omschrijving, - kernwoorden, / leverancier"
        )

        self.search_type_select = QComboBox()
        self.search_type_select.addItems(["Artikel", "Project", "BP", "VTA", "Prod"])
        self.search_type_select.setCurrentText(load_default_search_type())
        self.search_type_select.currentTextChanged.connect(self._toggle_fields_by_search_type)
        self.search_type_select.currentTextChanged.connect(self._update_input_tooltip)

        self.mode_label = QLabel("Zoekmodus:")
        self.mode_select = QComboBox()
        self.mode_select.addItems(["AND", "OR"])

        # We hergebruiken deze rij:
        # - Standaard: label = "Toon voorraad:", items = ["R","S","B"]
        # - BP      : label = "Type:", items = ["", "C", "S"]
        self.stock_label = QLabel("Toon voorraad:")
        self.show_stock_select = QComboBox()
        # INIT: stock-items + huidige setting
        self._set_combo_items(self.show_stock_select, ["R", "S", "B"], current=load_show_stock())
        # Routeer opslag via centrale handler (afhankelijk van actieve modus)
        self.show_stock_select.currentTextChanged.connect(self._handle_secondary_combo_change)

        # NIEUW (Prod Stock Overview): dataset-keuzelijst, enkel zichtbaar
        # bij search-type "Prod" (i.p.v. het zoekterm-veld).
        self.prod_dataset_label = QLabel("Dataset:")
        self.prod_dataset_select = QComboBox()
        self._prod_datasets_cache = []

        # NIEUW (v1.7.0 — inline, geen popup meer): magazijnfilter + tekstfilter,
        # enkel zichtbaar bij "Prod". Beide wijzigen enkel de weergave van reeds
        # geladen data (self._prod_raw_data) — geen nieuwe API-call.
        self.prod_warehouse_label = QLabel("Magazijn:")
        self.prod_warehouse_select = QComboBox()
        self.prod_warehouse_select.addItem("Alle magazijnen", "")
        for _wh in PROD_WAREHOUSE_COLUMNS:
            self.prod_warehouse_select.addItem(_wh.replace("Stock_", ""), _wh)
        self.prod_warehouse_select.currentIndexChanged.connect(self._render_prod_table)

        self.prod_filter_label = QLabel("Filter:")
        self.prod_filter_input = QLineEdit()
        self.prod_filter_input.setPlaceholderText("Filter op art.nr. of omschrijving…")
        self.prod_filter_input.textChanged.connect(self._render_prod_table)

        self._prod_raw_data = []       # cache van de laatst opgehaalde stock-data
        self._prod_current_dataset = None

        self.search_button = QPushButton("Zoeken")
        self.search_button.clicked.connect(self.perform_search)
        self.table = QTableWidget()
        self.table.itemDoubleClicked.connect(self.handle_row_double_click)
        # ➕ Rechterklik-copy activeren
        self._add_context_menu_to_table()

        # SORT-1: dubbelklik op kolomheader (Art.Nr./Qty/Prijs/Leverancier) sorteert
        self.table.horizontalHeader().setSectionsClickable(True)
        self.table.horizontalHeader().sectionDoubleClicked.connect(self._on_table_header_double_clicked)

        self.collect_button = QPushButton("Voeg toe aan lijst")
        self.clear_collected_button = QPushButton("Leeg lijst")
        self.show_list_button = QPushButton("Toon lijst")
        self.select_all_checkbox = QCheckBox("Selecteer alles")

        # NIEUW (Prod Stock Overview): export-knop, enkel zichtbaar bij "Prod"
        self.prod_export_button = QPushButton("Exporteer naar Excel")
        self.prod_export_button.clicked.connect(self._export_prod_xlsx)
        self.prod_export_button.setVisible(False)

        self.collect_button.clicked.connect(self.collect_selected_rows)
        self.clear_collected_button.clicked.connect(self.clear_collected_list)
        self.show_list_button.clicked.connect(self.show_collected_dialog)
        self.select_all_checkbox.toggled.connect(self._toggle_select_all)

        self.result_count_label = QLabel("Aantal resultaten: 0")

        self.loading_spinner = QLabel()
        spinner_path = os.path.join(os.path.dirname(__file__), "assets", "spinner.gif")
        self.loading_movie = QMovie(spinner_path)
        self.loading_spinner.setMovie(self.loading_movie)
        self.loading_spinner.setAlignment(Qt.AlignCenter)
        self.loading_spinner.hide()

        layout = QVBoxLayout()
        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(6)
        grid.setColumnStretch(0, 0)
        grid.setColumnStretch(1, 0)
        grid.setColumnStretch(2, 1)

        self.zoekterm_label = QLabel("Zoekterm:")
        search_type_label = QLabel("Search-type:")

        grid.addWidget(self.input_field, 0, 1, 1, 2)
        grid.addWidget(self.zoekterm_label, 0, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.input_field, 0, 1, 1, 2)

        grid.addWidget(search_type_label, 1, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.search_type_select, 1, 1)

        grid.addWidget(self.mode_label, 2, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.mode_select, 2, 1)

        grid.addWidget(self.stock_label, 3, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.show_stock_select, 3, 1)

        # NIEUW (Prod Stock Overview): rij 4-6, enkel zichtbaar bij "Prod"
        grid.addWidget(self.prod_dataset_label, 4, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.prod_dataset_select, 4, 1, 1, 2)

        grid.addWidget(self.prod_warehouse_label, 5, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.prod_warehouse_select, 5, 1)

        grid.addWidget(self.prod_filter_label, 6, 0, Qt.AlignRight | Qt.AlignVCenter)
        grid.addWidget(self.prod_filter_input, 6, 1, 1, 2)

        self._update_input_tooltip(self.search_type_select.currentText())
        self._toggle_fields_by_search_type(self.search_type_select.currentText())

        layout.addLayout(grid)
        layout.addWidget(self.search_button, alignment=Qt.AlignHCenter)
        layout.addWidget(QLabel("Resultaten:"))
        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.collect_button)
        btn_layout.addWidget(self.clear_collected_button)
        btn_layout.addWidget(self.show_list_button)
        btn_layout.addWidget(self.select_all_checkbox)
        btn_layout.addStretch()
        btn_layout.addWidget(self.prod_export_button)
        layout.addLayout(btn_layout)

        layout.addWidget(self.result_count_label)
        layout.addWidget(self.loading_spinner)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # --------------- ZOEKACTIE & TABELLEN ----------------
    def perform_search(self):
        zoekterm = self.input_field.text().strip()
        mode = self.mode_select.currentText()
        searchtype = self.search_type_select.currentText()

        is_prod = (searchtype == "Prod")

        self.result_count_label.setText("Aantal resultaten: 0")
        if not zoekterm and not is_prod:
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
            return

        # start spinner
        self.loading_spinner.show()
        self.loading_movie.start()
        QApplication.processEvents()

        # --- Nieuw: VTA ---
        is_vta = (searchtype == "VTA")
        is_project = (searchtype == "Project")
        is_bp = (searchtype == "BP")

        # --- Als Prod: data ophalen en INLINE tonen in self.table (geen popup) ---
        if is_prod:
            try:
                dataset = self.prod_dataset_select.currentData()
                if not dataset:
                    QMessageBox.warning(
                        self, "Geen dataset",
                        "Selecteer eerst een dataset in de keuzelijst (of maak er één aan via "
                        "Instellingen → Datasets beheren...)."
                    )
                    return

                items = parse_artnbr(dataset.get("DS_ArtNbr", ""))
                if not items:
                    QMessageBox.information(self, "Geen artikelen", "Deze dataset bevat geen artikelnummers.")
                    return

                self._prod_raw_data = get_prod_stock_overview(items)
                self._prod_current_dataset = dataset
                self._render_prod_table()

            except Exception as e:
                logger.error(f"Kon Prod-stock-overzicht niet ophalen: {e}")
                QMessageBox.critical(self, "Fout", f"Kon stock-overzicht niet ophalen:\n{e}")
                self._prod_raw_data = []
                self.table.setRowCount(0)
                self.table.setColumnCount(0)
            finally:
                self.loading_movie.stop()
                self.loading_spinner.hide()
            return

        # --- Als VTA, open direct ui_vta ---
        if is_vta:
            try:
                from ui_vta import PoWidget
                vta_window = PoWidget()

                # ✅ Belangrijk: maak het volledig onafhankelijk van het hoofdvenster
                vta_window.setParent(None)
                vta_window.setWindowModality(Qt.NonModal)
                vta_window.setWindowFlag(Qt.Window, True)

                vta_window.show()
                vta_window.activateWindow()
                vta_window.raise_()

                # 🔹 VTA-nummer invullen en automatisch ophalen
                vta_window.po_input.setText(zoekterm)
                vta_window.load_data()

                # 🔹 Toevoegen aan actieve vensterslijst
                self.detail_windows.append(vta_window)

                # 🔹 Zoekveld in hoofdvenster leegmaken + focus terug
                self.input_field.clear()
                self.input_field.setFocus()

            except Exception as e:
                QMessageBox.critical(self, "Fout", f"Kon VTA-venster niet openen:\n{e}")
            finally:
                self.loading_movie.stop()
                self.loading_spinner.hide()
            return

        request_kind = "project" if is_project else ("bp" if is_bp else "data")

        # Voor BP gebruiken we dezelfde combobox voor Type
        bp_type = self.show_stock_select.currentText() if is_bp else ""

        logger.info(
            f"Zoekactie: type={searchtype} | kind={request_kind} | term='{zoekterm}' | mode='{mode}' | bp_type='{bp_type}'"
        )

        try:
            data = send_data_request(
                zoekterm,
                mode,
                project_search=is_project,
                is_closed="",
                kind=request_kind,
                bp_type=bp_type
            )
            # --- ✅ Controle op lege resultaten bij Artikel + Toon voorraad = S ---
            # BUGFIX (v1.1.1): vergeleek voorheen met "Standaard", maar de
            # combobox self.search_type_select gebruikt als itemtekst
            # "Artikel" (zie addItems() hierboven) — hierdoor werd deze
            # voorwaarde nooit True en verscheen de "geen voorraad"-melding
            # nooit.
            show_stock = self.show_stock_select.currentText()
            if searchtype == "Artikel" and show_stock == "S" and (not data or len(data) == 0):
                self.table.setRowCount(0)
                self.table.setColumnCount(1)
                self.table.setHorizontalHeaderLabels(["Geen voorraad"])
                self.table.insertRow(0)

                no_stock_item = QTableWidgetItem("⚠️ Geen voorraad aanwezig voor deze zoekterm.")
                no_stock_item.setTextAlignment(Qt.AlignCenter)
                no_stock_item.setForeground(Qt.darkYellow)
                self.table.setItem(0, 0, no_stock_item)

                self.result_count_label.setText("Aantal resultaten: 0 (geen voorraad)")
                QMessageBox.information(
                    self,
                    "Geen voorraad",
                    "⚠️ Er is geen voorraad aanwezig voor deze zoekterm bij \"Toon voorraad = S\".\n\n"
                    "Dit betekent niet noodzakelijk dat het artikel niet bestaat: "
                    "zet \"Toon voorraad\" op \"R\" en zoek opnieuw om artikelinformatie "
                    "zonder voorraadfilter te bekijken."
                )

                self.loading_movie.stop()
                self.loading_spinner.hide()
                return

        except Exception as e:
            err_msg = str(e)
            self.table.clearSelection()
            self.table.setRowCount(0)
            self.table.setColumnCount(1)
            self.table.setHorizontalHeaderLabels(["Fout"])
            self.table.insertRow(0)
            self.table.setItem(0, 0, QTableWidgetItem(err_msg))
            self.loading_movie.stop()
            self.loading_spinner.hide()
            return

        # Render
        if is_project:
            if isinstance(data, dict) and "error" in data:
                QMessageBox.warning(self, "Projectzoeking mislukt", f"❌ {data['error']}")
            elif isinstance(data, list):
                try:
                    self.project_window = ProjectWindow(data, parent=self)
                    self.project_window.show()
                    self.detail_windows.append(self.project_window)
                except Exception as e:
                    QMessageBox.warning(
                        self,
                        "Fout bij tonen projectgegevens",
                        f"❌ Ongeldige projectdata of formaat:\n{e}"
                    )
            else:
                QMessageBox.warning(self, "Geen data", "❌ Geen geldige projectresultaten ontvangen.")
        elif is_bp:
            self.populate_bp_table(data)
        else:
            # SORT-1: nieuwe zoekactie -> sorteerstatus/-indicator resetten
            self._article_sort_state = {"column_index": None, "ascending": True}
            self.table.horizontalHeader().setSortIndicatorShown(False)
            self.populate_table(data)

        # stop spinner
        self.loading_movie.stop()
        self.loading_spinner.hide()

    def populate_table(self, data: list):
        """Standaard artikelweergave met dynamische kolomdefinities uit settings."""
        show_stock = load_show_stock()

        if show_stock == "S":
            originele_columns = list(COLUMN_HEADERS_S.keys())
            header_labels = ["Selectie"] + list(COLUMN_HEADERS_S.values())
        else:
            originele_columns = list(COLUMN_HEADERS_DEFAULT.keys())
            header_labels = ["Selectie"] + list(COLUMN_HEADERS_DEFAULT.values())

        # SORT-1: onthouden voor _on_table_header_double_clicked (kolomindex -> data-key)
        self._last_article_data = data
        self._last_article_columns = originele_columns

        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(header_labels))
        self.table.setHorizontalHeaderLabels(header_labels)

        # KOLOMBREEDTE-1: alle kolommen (behalve de checkbox-kolom) vrij
        # versleepbaar + dubbelklik-autofit, i.p.v. de vorige hardgecodeerde
        # Stretch op kolomindex 2 — analoog aan ui_bp_articles_tab.py.
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for idx in range(1, len(header_labels)):
            header.setSectionResizeMode(idx, QHeaderView.Interactive)
        header.setStretchLastSection(True)

        # MINWHS-KLEUR-1: kolomindex van "Min.Whs" (QTYMININV) bepalen —
        # enkel aanwezig wanneer show_stock == "S".
        try:
            min_whs_col_offset = originele_columns.index("QTYMININV") + 1
        except ValueError:
            min_whs_col_offset = None
        MIN_WHS_STANDAARD_KLEUR = QColor("#d9f2d9")  # lichtgroen

        for row, item in enumerate(data):
            checkbox = QCheckBox()
            checkbox.setFocusPolicy(Qt.NoFocus)
            self.table.setCellWidget(row, 0, checkbox)
            for col_offset, key in enumerate(originele_columns, start=1):
                val = item.get(key, "")
                val = f"{val:.2f}" if isinstance(val, float) else str(val or "")
                cell = QTableWidgetItem(val)
                cell.setToolTip(val)

                # MINWHS-KLEUR-1: Min.Whs > 0 => "standaard artikel",
                # lichtgroen gemarkeerd + duidelijke tooltip.
                if min_whs_col_offset is not None and col_offset == min_whs_col_offset:
                    try:
                        is_standaard_artikel = float(str(val).replace(",", ".")) > 0
                    except (TypeError, ValueError):
                        is_standaard_artikel = False
                    if is_standaard_artikel:
                        cell.setBackground(MIN_WHS_STANDAARD_KLEUR)
                        cell.setToolTip(f"{val}\n✅ Standaard artikel (Min.Whs > 0)")

                self.table.setItem(row, col_offset, cell)

        # KOLOMBREEDTE-1: eerste weergave auto-fitten op inhoud (Excel-
        # gevoel), blijft nadien manueel aanpasbaar door de gebruiker.
        self.table.resizeColumnsToContents()

        self.result_count_label.setText(f"Aantal resultaten: {len(data)}")
        if data:
            self.table.selectRow(0)

        # SORT-1: sorteerpijltje in header herstellen na herbouw van de tabel
        col_idx = self._article_sort_state.get("column_index")
        if col_idx is not None:
            order = Qt.AscendingOrder if self._article_sort_state["ascending"] else Qt.DescendingOrder
            header = self.table.horizontalHeader()
            header.setSortIndicatorShown(True)
            header.setSortIndicator(col_idx, order)

    def _on_table_header_double_clicked(self, logical_index: int):
        """
        SORT-1 / SORT-PROD-1: sorteert de resultatentabel bij dubbelklik op
        een toegestane kolomheader — routeert per search-type naar de juiste
        sorteerlogica (Artikel: Art.Nr./Qty/Prijs/Leverancier; Prod:
        Art.Nr./Omschrijving). Andere search-types zijn niet sorteerbaar.
        """
        current_type = self.search_type_select.currentText()
        if current_type == "Artikel":
            self._sort_article_column(logical_index)
        elif current_type == "Prod":
            self._sort_prod_column(logical_index)
        # andere search-types (Project/BP/VTA): geen kolomsortering

    def _sort_article_column(self, logical_index: int):
        """
        SORT-1: sorteert de Artikel-resultatentabel bij dubbelklik op een
        toegestane kolomheader (Art.Nr. / Qty / Prijs / Leverancier).
        Sorteert op de ruwe data (vóór weergave-opmaak). Tweede dubbelklik
        op dezelfde kolom keert de richting om.
        """
        if logical_index == 0 or not self._last_article_columns:
            return  # kolom 0 = Selectie-checkbox, niet sorteerbaar

        header_item = self.table.horizontalHeaderItem(logical_index)
        header_label = header_item.text() if header_item else ""
        if header_label not in SORTABLE_ARTICLE_HEADER_LABELS:
            return  # enkel Art.Nr., Qty, Prijs, Leverancier zijn sorteerbaar

        col_key_index = logical_index - 1
        if col_key_index >= len(self._last_article_columns):
            return
        col_key = self._last_article_columns[col_key_index]

        # Richting bepalen: zelfde kolom -> omkeren, andere kolom -> oplopend starten
        if self._article_sort_state.get("column_index") == logical_index:
            ascending = not self._article_sort_state["ascending"]
        else:
            ascending = True
        self._article_sort_state = {"column_index": logical_index, "ascending": ascending}

        def _sort_key(record):
            val = record.get(col_key)
            if val is None:
                return (1, "")  # None's altijd achteraan, ongeacht sorteerrichting
            if isinstance(val, (int, float)):
                return (0, val)
            try:
                return (0, float(val))  # numerieke waarde als tekst opgeslagen
            except (TypeError, ValueError):
                return (0, str(val).lower())

        try:
            self._last_article_data.sort(key=_sort_key, reverse=not ascending)
        except TypeError:
            # Fallback bij gemengde types (numeriek + tekst) in dezelfde kolom
            self._last_article_data.sort(
                key=lambda rec: str(rec.get(col_key, "")).lower(),
                reverse=not ascending
            )

        self.populate_table(self._last_article_data)

    def populate_bp_table(self, data: list):
        """BP-weergave: alleen CardCode, CardName, FederalTaxID, ContactPerson."""
        header_labels = ["Selectie", "CardCode", "Partner Naam", "BTW-Nbr", "Contact Persoon"]

        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(header_labels))
        self.table.setHorizontalHeaderLabels(header_labels)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for idx in range(1, len(header_labels)):
            mode = QHeaderView.Stretch if header_labels[idx] == "CardName" else QHeaderView.ResizeToContents
            header.setSectionResizeMode(idx, mode)

        def extract_contact_person(item: dict) -> str:
            cp = item.get("ContactPerson") or item.get("Contactperson")
            if cp:
                return str(cp)
            emps = item.get("ContactEmployees") or []
            if isinstance(emps, list) and emps:
                for ce in emps:
                    if (ce.get("Active") == "Y") and ce.get("Name"):
                        return str(ce["Name"])
                if emps[0].get("Name"):
                    return str(emps[0]["Name"])
            return ""

        for row, item in enumerate(data):
            checkbox = QCheckBox()
            checkbox.setFocusPolicy(Qt.NoFocus)
            self.table.setCellWidget(row, 0, checkbox)

            card_code = str(item.get("CardCode", "") or "")
            card_name = str(item.get("CardName", "") or "")
            federal_id = str(item.get("FederalTaxID") or item.get("FedralTaxID") or "")
            contact = extract_contact_person(item)

            values = [card_code, card_name, federal_id, contact]
            for col_offset, val in enumerate(values, start=1):
                cell = QTableWidgetItem(val)
                cell.setToolTip(val)
                self.table.setItem(row, col_offset, cell)

        self.result_count_label.setText(f"Aantal resultaten: {len(data)}")
        if data:
            self.table.selectRow(0)

    # --------------- PROD STOCK OVERVIEW (inline, geen popup) ----------------
    def _prod_visible_warehouse_columns(self) -> list:
        """Welke Stock_*-kolommen tonen o.b.v. self.prod_warehouse_select."""
        selected = self.prod_warehouse_select.currentData()
        if not selected:
            return list(PROD_WAREHOUSE_COLUMNS)
        return [selected]

    def _render_prod_table(self):
        """
        Rendert self._prod_raw_data in de hoofdtabel, met magazijn- en
        tekstfilter toegepast (client-side, GEEN nieuwe API-call — enkel
        "Zoeken" haalt effectief nieuwe data op). Standaard gesorteerd op
        Art.Nr. (oplopend) — een nieuwe filter-/laadactie herstelt telkens
        deze standaardsortering (i.p.v. de ruwe, ongesorteerde API-volgorde).
        """
        if self.search_type_select.currentText() != "Prod":
            return  # widgets kunnen nog signalen sturen tijdens het wisselen van search-type

        data = list(self._prod_raw_data or [])

        term = self.prod_filter_input.text().strip().lower()
        if term:
            data = [
                r for r in data
                if term in str(r.get("ArtCode", "") or "").lower()
                or term in str(r.get("Omschrijving", "") or "").lower()
            ]

        # SORT-PROD-1: standaard oplopend sorteren op Art.Nr. (kolom 1, na de
        # Selectie-checkboxkolom — "Art.Nr." staat altijd als eerste kolom,
        # ongeacht de magazijnfilter). Zelfde sorteersleutel als
        # _sort_prod_column(), zodat een volgende dubbelklik op de
        # kolomkop consistent hierop verder bouwt (eerste klik -> aflopend).
        data.sort(key=lambda r: (1, "") if r.get("ArtCode") is None else (0, str(r.get("ArtCode")).lower()))
        self._prod_sort_state = {"column_index": 1, "ascending": True}

        self._populate_prod_rows(data)

    def _populate_prod_rows(self, data: list):
        """
        Bouwt self.table op uit een (reeds gefilterde, eventueel gesorteerde)
        data-lijst. Losstaand van _render_prod_table() zodat
        _sort_prod_column() dezelfde tabel kan herbouwen zonder de
        tekst-/magazijnfilter opnieuw toe te passen.
        """
        hidden_wh = set(PROD_WAREHOUSE_COLUMNS) - set(self._prod_visible_warehouse_columns())
        columns = [(key, label) for key, label in PROD_STOCK_COLUMNS if key not in hidden_wh]
        header_labels = ["Selectie"] + [label for _, label in columns]

        # SORT-PROD-1: onthouden voor _sort_prod_column() (kolomindex -> data-key)
        self._last_prod_data = data  # export gebruikt deze (gefilterde/gesorteerde) set
        self._last_prod_columns = columns

        self.table.setRowCount(len(data))
        self.table.setColumnCount(len(header_labels))
        self.table.setHorizontalHeaderLabels(header_labels)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        for idx in range(1, len(header_labels)):
            header.setSectionResizeMode(idx, QHeaderView.Interactive)
        # GEEN stretch op de laatste kolom ("LISA Qty"): stretchLastSection
        # zou de expliciete PROD_COLUMN_WIDTHS-breedte hieronder overrulen
        # en de kolom alsnog alle overblijvende ruimte laten opvullen.
        header.setStretchLastSection(False)

        for row, rec in enumerate(data):
            checkbox = QCheckBox()
            checkbox.setFocusPolicy(Qt.NoFocus)
            self.table.setCellWidget(row, 0, checkbox)

            for col_offset, (key, _label) in enumerate(columns, start=1):
                val = rec.get(key)
                text = "" if val is None else str(val)
                cell = QTableWidgetItem(text)
                cell.setToolTip(text)

                if key in PROD_NUMERIC_KEYS:
                    cell.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

                # "Min. SAP" > 0 => lichtgroen (standaard artikel)
                if key == "MinSAP":
                    try:
                        if val is not None and float(val) > 0:
                            cell.setBackground(PROD_MIN_SAP_GREEN)
                            cell.setToolTip(f"{text}\nMin. SAP > 0")
                    except (TypeError, ValueError):
                        pass

                # "Stock Algemeen" < 1 => lichtrood
                if key == "Stock_Algemeen":
                    try:
                        if val is not None and float(val) < 1:
                            cell.setBackground(PROD_STOCK_ALG_RED)
                            cell.setToolTip(f"{text}\n⚠️ Stock Algemeen < 1")
                    except (TypeError, ValueError):
                        pass

                # "Stock vandaag" < "Min. SAP" => geel
                if key == "StockHeden":
                    min_sap_val = rec.get("MinSAP")
                    try:
                        if val is not None and min_sap_val is not None and float(val) < float(min_sap_val):
                            cell.setBackground(PROD_STOCK_HEDEN_YELLOW)
                            cell.setToolTip(f"{text}\n⚠️ Stock vandaag < Min. SAP ({min_sap_val})")
                    except (TypeError, ValueError):
                        pass

                self.table.setItem(row, col_offset, cell)

        self.table.resizeColumnsToContents()

        # Enkele kolommen bewust smaller/breder houden dan
        # resizeColumnsToContents() zou toepassen.
        for col_offset, (key, _label) in enumerate(columns, start=1):
            if key in PROD_COLUMN_WIDTHS:
                self.table.setColumnWidth(col_offset, PROD_COLUMN_WIDTHS[key])

        ds = self._prod_current_dataset or {}
        self.result_count_label.setText(
            f"Dataset: {ds.get('DS_Name', '')} | Eigenaar: {ds.get('DS_Owner', '') or '-'} | "
            f"Aantal artikelen: {len(data)}"
        )
        if data:
            self.table.selectRow(0)

        # SORT-PROD-1: sorteerpijltje in header herstellen na herbouw van de tabel
        col_idx = self._prod_sort_state.get("column_index")
        if col_idx is not None:
            order = Qt.AscendingOrder if self._prod_sort_state["ascending"] else Qt.DescendingOrder
            header = self.table.horizontalHeader()
            header.setSortIndicatorShown(True)
            header.setSortIndicator(col_idx, order)

    def _sort_prod_column(self, logical_index: int):
        """
        SORT-PROD-1: sorteert de Prod-resultatentabel bij dubbelklik op een
        toegestane kolomheader (Art.Nr. / Omschrijving). Sorteert op de
        reeds gefilterde data (self._last_prod_data), niet op de volledige
        ruwe set. Tweede dubbelklik op dezelfde kolom keert de richting om.
        """
        if logical_index == 0 or not getattr(self, "_last_prod_columns", None):
            return  # kolom 0 = Selectie-checkbox, niet sorteerbaar

        header_item = self.table.horizontalHeaderItem(logical_index)
        header_label = header_item.text() if header_item else ""
        if header_label not in PROD_SORTABLE_HEADER_LABELS:
            return  # enkel Art.Nr. en Omschrijving zijn sorteerbaar

        col_key_index = logical_index - 1
        if col_key_index >= len(self._last_prod_columns):
            return
        col_key = self._last_prod_columns[col_key_index][0]

        # Richting bepalen: zelfde kolom -> omkeren, andere kolom -> oplopend starten
        if self._prod_sort_state.get("column_index") == logical_index:
            ascending = not self._prod_sort_state["ascending"]
        else:
            ascending = True
        self._prod_sort_state = {"column_index": logical_index, "ascending": ascending}

        def _sort_key(record):
            val = record.get(col_key)
            if val is None:
                return (1, "")  # None's altijd achteraan, ongeacht sorteerrichting
            return (0, str(val).lower())

        self._last_prod_data.sort(key=_sort_key, reverse=not ascending)
        self._populate_prod_rows(self._last_prod_data)

    def _export_prod_xlsx(self):
        """Exporteert de huidige (gefilterde) Prod-tabelweergave naar .xlsx."""
        data = getattr(self, "_last_prod_data", None) or []
        if not data:
            QMessageBox.information(self, "Geen data", "Er is niets om te exporteren.")
            return

        ds = self._prod_current_dataset or {}
        default_name = f"prod_stock_{ds.get('DS_Name', 'dataset')}.xlsx".replace(" ", "_")
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporteer naar Excel", default_name, "Excel-bestand (*.xlsx)"
        )
        if not path:
            return

        try:
            import openpyxl
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "Stock overzicht"

            hidden_wh = set(PROD_WAREHOUSE_COLUMNS) - set(self._prod_visible_warehouse_columns())
            columns = [(key, label) for key, label in PROD_STOCK_COLUMNS if key not in hidden_wh]

            ws.append([label for _, label in columns])
            for rec in data:
                ws.append([rec.get(key) for key, _ in columns])

            wb.save(path)
            QMessageBox.information(self, "Export voltooid", f"Bestand opgeslagen:\n{path}")
        except Exception as e:
            logger.error(f"Fout bij Prod-export: {e}")
            QMessageBox.critical(self, "Fout bij export", str(e))

    # --------------- VERZAMEL / DIALOGEN ----------------
    def collect_selected_rows(self):
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
                    text = item.text() if item is not None else ""
                    row_values.append(text)

                joined = "\t".join(row_values)
                if joined not in self.collected_data:
                    self.collected_data.append(joined)

        if not iets_aangevinkt:
            QMessageBox.information(self, "Niets aangevinkt", "Vink eerst één of meerdere vakjes aan om toe te voegen.")
            return

        self.show_collected_dialog()

    def show_collected_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Verzamelde rijen")
        dialog.resize(800, 400)

        if self.search_type_select.currentText() == "BP":
            headers = ["CardCode", "CardName", "FederalTaxID", "ContactPerson"]
        else:
            show_stock = load_show_stock()
            headers = list(COLUMN_HEADERS_S.values()) if show_stock == "S" else list(COLUMN_HEADERS_DEFAULT.values())

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

    def clear_collected_list(self):
        if not self.collected_data:
            QMessageBox.information(self, "Lijst is al leeg", "Er staan momenteel geen rijen in de lijst.")
            return

        self.collected_data.clear()

        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(False)

        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.blockSignals(True)
            self.select_all_checkbox.setChecked(False)
            self.select_all_checkbox.blockSignals(False)

        QMessageBox.information(self, "Lijst geleegd", "De verzamelde rijen zijn nu verwijderd en alle vakjes zijn uitgevinkt.")

    # --------------- DETAIL / CONTEXTMENU / LABEL ----------------
    def handle_row_double_click(self, item):
        search_type = self.search_type_select.currentText()

        # Nieuw: BP dubbelklik opent ui_bp en zoekt op CardCode
        if search_type == "BP":
            row = item.row()
            # In populate_bp_table is de kolomvolgorde:
            # ["Selectie", "CardCode", "CardName", "FederalTaxID", "ContactPerson"]
            card_code_item = self.table.item(row, 1)  # kolom 1 = CardCode
            card_code = card_code_item.text() if card_code_item else ""
            if not card_code:
                QMessageBox.information(self, "Info", "Geen geldige CardCode gevonden op deze rij.")
                return

            bpw = BpWindow()
            bpw.showMaximized()
            bpw.preset_and_fetch(card_code, auto_fetch=True)

            self.bp_windows.append(bpw)
            return

        # Bestaande flow voor niet-BP (artikels / detail)
        row = item.row()
        # Kolom 1 bevat ItemCode (kolom 0 is checkbox)
        item_code = self.table.item(row, 1).text()
        self.table.clearSelection()

        # Vendor-hints uit de ruwe zoekresultaat-rij (SuppCatNum/SUPPLIERIDPRODUCT
        # = leveranciersartikelnummer, SUPPLIERNAME = leveranciersnaam — enkel
        # aanwezig bij Toon voorraad = S). Deze velden zitten NIET in de
        # ZStockInfoP-detailpayload (get_item_detail_stockinfo), vandaar hier
        # apart meegeven aan DetailWindow t.b.v. de OITMI Upload-prefill.
        raw_rows = getattr(self, "_last_article_data", None) or []
        raw_row = raw_rows[row] if 0 <= row < len(raw_rows) else {}
        vendor_hint_id = str(raw_row.get("SuppCatNum") or raw_row.get("SUPPLIERIDPRODUCT") or "").strip()
        vendor_hint_name = str(raw_row.get("SUPPLIERNAME") or "").strip()

        try:
            raw_detail = get_item_detail_stockinfo(item_code)

            # --- Belangrijk: normaliseer elk type naar dict ---
            detail_data = self._normalize_detail_payload(raw_detail)

            logger.info(
                "Detail payload type=%s keys=%s",
                type(raw_detail).__name__,
                list(detail_data.keys())[:10] if isinstance(detail_data, dict) else "n/a",
            )

            dialog = DetailWindow(
                parent=self,
                item_code=item_code,
                detail_data=detail_data or {},
                vendor_hint_id=vendor_hint_id,
                vendor_hint_name=vendor_hint_name,
            )
            dialog.show()
            self._reposition_detail(dialog)
            self.detail_windows.append(dialog)

        except Exception as e:
            QMessageBox.warning(self, "Detail Fout", f"Kon detail niet openen:\n{e}\n(type: {type(e).__name__})")

    def _open_selected_row(self):
        search_type = self.search_type_select.currentText()
        selected_items = self.table.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Geen selectie", "Selecteer een rij om te openen.")
            return
        first_index = selected_items[0].row()

        if search_type == "BP":
            card_code_item = self.table.item(first_index, 1)  # kolom 1 = CardCode
            card_code = card_code_item.text() if card_code_item else ""
            if not card_code:
                QMessageBox.information(self, "Info", "Geen geldige CardCode gevonden op deze rij.")
                return

            bpw = BpWindow()
            bpw.showMaximized()
            bpw.preset_and_fetch(card_code, auto_fetch=True)
            self.bp_windows.append(bpw)
            return

        # Niet-BP: bestaande artikel-detail flow
        self.handle_row_double_click(self.table.item(first_index, 1))

    def show_table_context_menu(self, position: QPoint):
        index = self.table.indexAt(position)
        if not index.isValid():
            return
        row = index.row()
        menu = QMenu(self)
        copy_action = menu.addAction("📋 Kopieer rij")

        if self.search_type_select.currentText() != "BP":
            detail_action = menu.addAction("🔍 Toon detail")
            label_action = menu.addAction("🏷️ Genereer label")
        action = menu.exec(self.table.viewport().mapToGlobal(position))
        if action == copy_action:
            values = [self.table.item(row, col).text() for col in range(1, self.table.columnCount())]
            QApplication.clipboard().setText("\t".join(values))
        elif self.search_type_select.currentText() != "BP":
            if action and action.text().startswith("🔍"):
                self.handle_row_double_click(self.table.item(row, 1))
            elif action and action.text().startswith("🏷️"):
                self._generate_label()

    # --------------- Contextmenu: Copy cel / rij ---------------
    def _add_context_menu_to_table(self):
        """Activeer rechterklik-copy voor de standaard zoekresultatentabel."""
        self.table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_copy_menu)

    def _show_copy_menu(self, pos):
        index = self.table.indexAt(pos)
        if not index.isValid():
            return

        row, col = index.row(), index.column()
        cell = self.table.item(row, col)
        if not cell:
            return

        menu = QMenu(self)
        copy_cell = menu.addAction("📋 Kopieer cel")
        copy_row = menu.addAction("📋 Kopieer rij")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))

        if action == copy_cell:
            QApplication.clipboard().setText(cell.text())
        elif action == copy_row:
            row_values = []
            for c in range(1, self.table.columnCount()):  # sla checkbox over
                item = self.table.item(row, c)
                row_values.append(item.text() if item else "")
            QApplication.clipboard().setText("\t".join(row_values))

    def _generate_label(self):
        if self.search_type_select.currentText() == "BP":
            QMessageBox.information(self, "Info", "Label genereren is enkel voor artikels.")
            return

        selected = self.table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Geen selectie", "Selecteer een rij om een label te genereren.")
            return
        row = selected[0].row()
        code = self.table.item(row, 1).text()
        desc = self.table.item(row, 2).text()
        supplier = self.table.item(row, 3).text() if self.table.columnCount() > 3 else "-"
        generate_label(code, desc, supplier, "00000000")

    # --------------- DIVERSE HELPERS / DIALOGEN ----------------
    def _show_label_settings_dialog(self):
        dialog = LabelSettingsDialog(self)
        dialog.exec()

    def _clear_search(self):
        self.input_field.clear()
        self.input_field.setFocus()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.result_count_label.setText("Aantal resultaten: 0")

    def _prod_export_shortcut(self):
        """Ctrl+E: exporteert het huidige Prod-stock-overzicht naar Excel
        (analoog aan Ctrl+E in PaymentsDue e.a.). Genegeerd bij een ander
        search-type of wanneer er nog niets geladen is."""
        if self.search_type_select.currentText() != "Prod":
            return
        self._export_prod_xlsx()

    def eventFilter(self, obj, event):
        if event.type() != QEvent.KeyPress:
            return super().eventFilter(obj, event)
        if event.key() == Qt.Key_Delete:
            # Prod: "Delete" wist de resultaatfilter (analoog aan "Ctrl+D =
            # Filters wissen" bij CC BP/andere vensters), niet het verborgen
            # zoekterm-veld.
            if self.search_type_select.currentText() == "Prod":
                self.prod_filter_input.clear()
            else:
                self._clear_search()
            return True
        return super().eventFilter(obj, event)

    def _choose_environment(self):
        current = load_environment()
        options = ["live", "test"]
        selected, ok = QInputDialog.getItem(
            self, "Omgeving kiezen", "Selecteer omgeving:", options, options.index(current), False
        )
        if ok and selected != current:
            save_environment(selected)
            QMessageBox.information(self, "Herstart vereist", f"Omgeving gewijzigd naar '{selected}'. Gelieve te herstarten.")

    def _reposition_detail(self, dlg):
        hoofd_pos = self.pos()
        offset_x = 50
        offset_y = 50
        nieuwe_x = hoofd_pos.x() + offset_x
        nieuwe_y = hoofd_pos.y() + offset_y
        dlg.move(nieuwe_x, nieuwe_y)

    # Editors
    def _open_style_qss_editor(self):
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "style.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_detail_qss_editor(self):
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "detail.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    def _open_upload_qss_editor(self):
        base = os.path.dirname(__file__)
        path = os.path.join(base, "assets", "css", "upload.qss")
        if not os.path.exists(path):
            QMessageBox.warning(self, "Bestand niet gevonden", f"Kan {path} niet vinden.")
            return
        dlg = FileEditorDialog(self, path)
        dlg.exec()

    # QSS live-reload
    def _on_qss_file_changed(self, path: str):
        """Herlaadt het gewijzigde .qss-bestand en past het toe."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                qss = f.read()
        except Exception:
            QTimer.singleShot(500, lambda: self._retry_reload(path))
            return

        if path == self._style_qss:
            self.setStyleSheet(qss)
        elif path == self._detail_qss:
            for dlg in self.detail_windows:
                dlg.setStyleSheet(qss)
        elif path == self._upload_qss:
            for uw in self.upload_windows:
                uw.setStyleSheet(qss)

    def _retry_reload(self, path: str):
        """Herkent na korte vertraging of het bestand dan wél bestaat."""
        if os.path.exists(path):
            self._on_qss_file_changed(path)

    # --------------- WHATSNEW-1: update-popup + "Wat is er nieuw?" ---------------
    def _check_for_update_startup(self):
        """Opstart-check (1s na start) — toont bij een nieuwere versie een
        eigen dialoog i.p.v. de kale QMessageBox uit updater.py."""
        check_for_update(__version__, self, self._on_startup_update_check_result)

    def _on_startup_update_check_result(self, is_newer: bool):
        if is_newer:
            self._show_update_available_dialog()

    def _show_update_available_dialog(self):
        """Dialoog bij opstart wanneer een nieuwere versie beschikbaar is:
        knoppen 'Update nu', 'Wat is er nieuw?' en 'Later'."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Nieuwe versie beschikbaar")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel(
            f"Er is een nieuwe versie van Artikelzoeker beschikbaar.\n"
            f"Je huidige versie: {__version__}"
        ))

        btn_row = QHBoxLayout()
        update_btn = QPushButton("Update nu")
        update_btn.clicked.connect(lambda: download_latest_release(dialog))
        whatsnew_btn = QPushButton("Wat is er nieuw?")
        whatsnew_btn.clicked.connect(lambda: self._show_whatsnew_dialog(parent=dialog))
        later_btn = QPushButton("Later")
        later_btn.clicked.connect(dialog.reject)

        btn_row.addWidget(update_btn)
        btn_row.addWidget(whatsnew_btn)
        btn_row.addStretch()
        btn_row.addWidget(later_btn)
        layout.addLayout(btn_row)

        dialog.setLayout(layout)
        dialog.exec()

    def _show_whatsnew_dialog(self, parent=None):
        """WHATSNEW-1: toont de release notes (body) van de laatste GitHub
        Release — remote content, niet te verwarren met de lokale
        Changelog-dialoog (_show_changelog_dialog) die de geschiedenis van
        de al geïnstalleerde versie toont. Wordt aangeroepen vanuit zowel
        de opstart-popup (_show_update_available_dialog) als Help → Over...
        (_show_about_dialog) — één centrale implementatie."""
        dialog = QDialog(parent or self)
        dialog.setWindowTitle("Wat is er nieuw?")
        dialog.resize(700, 500)
        layout = QVBoxLayout(dialog)

        notes_view = QTextBrowser()
        notes_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(notes_view)

        html_url = f"https://github.com/{OWNER}/{REPO}/releases/latest"
        try:
            info = fetch_release_notes()
            html_url = info.get("html_url", html_url)
            body = info.get("body", "")
            if body:
                notes_view.setHtml(markdown.markdown(body, extensions=['tables']))
            else:
                notes_view.setPlainText(
                    "ℹ️ Geen release notes ingevuld voor deze release.\n\n"
                    "Klik op \"Open op GitHub\" voor meer info."
                )
        except Exception as e:
            notes_view.setPlainText(
                f"❌ Kon release notes niet ophalen:\n{e}\n\n"
                "Klik op \"Open op GitHub\" om de releasepagina te bekijken."
            )

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        open_gh_btn = QPushButton("Open op GitHub")
        open_gh_btn.clicked.connect(lambda: webbrowser.open(html_url))
        close_btn = QPushButton("Sluiten")
        close_btn.clicked.connect(dialog.accept)
        btn_row.addWidget(open_gh_btn)
        btn_row.addWidget(close_btn)
        layout.addLayout(btn_row)

        dialog.setLayout(layout)
        dialog.exec()

    # Changelog & Help & About
    def _show_changelog_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Changelog")
        dialog.resize(900, 650)

        layout = QVBoxLayout(dialog)

        changelog_view = QTextBrowser()
        changelog_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # --- Bepaal paden ---
        if getattr(sys, "frozen", False):
            base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            exe_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(__file__)
            exe_dir = base_dir

        # --- Mogelijke docs-locaties ---
        possible_docs = [
            os.path.join(exe_dir, "docs"),                 # PyInstaller output
            os.path.join(base_dir, "docs"),                # Development
            os.path.join(os.path.dirname(base_dir), "docs") # fallback
        ]

        possible_paths = []
        changelog_file = None

        for folder in possible_docs:
            candidate = os.path.join(folder, "changelog.md")
            possible_paths.append(candidate)
            if os.path.exists(candidate):
                changelog_file = candidate
                break

        # --- Badge folder (voor afbeeldingen) ---
        badges_folder = os.path.join(exe_dir, "assets", "badges")
        changelog_view.setSearchPaths([badges_folder])

        # --- Markdown verwerken ---
        if changelog_file:
            try:
                with open(changelog_file, "r", encoding="utf-8") as f:
                    html = markdown.markdown(f.read(), extensions=['tables'])
                    changelog_view.setHtml(html)
            except Exception as e:
                changelog_view.setPlainText(f"❌ Fout bij laden changelog.md:\n{e}")
        else:
            changelog_view.setPlainText(
                "❌ changelog.md niet gevonden.\n\n"
                "Gezocht in:\n" + "\n".join(possible_paths)
            )

        layout.addWidget(changelog_view)
        dialog.setLayout(layout)
        dialog.exec()

    def _show_about_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Over Artikelzoeker")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Artikelzoeker – zoektool voor artikels"))
        version_label = QLabel(f"Versie: {__version__}")
        version_label.setStyleSheet("color: gray;")
        layout.addWidget(version_label)

        btn_row = QHBoxLayout()
        self.update_btn = QPushButton("Update nu")
        self.update_btn.setEnabled(False)
        self.update_btn.clicked.connect(lambda: download_latest_release(dialog))
        btn_row.addWidget(self.update_btn)

        # WHATSNEW-1: enkel actief zodra check_for_update() een nieuwere
        # versie meldt — zelfde callback als de "Update nu"-knop hierboven.
        whatsnew_btn = QPushButton("Wat is er nieuw?")
        whatsnew_btn.setEnabled(False)
        whatsnew_btn.clicked.connect(lambda: self._show_whatsnew_dialog(parent=dialog))
        btn_row.addWidget(whatsnew_btn)
        layout.addLayout(btn_row)

        def _on_check_result(is_newer: bool):
            self.update_btn.setEnabled(is_newer)
            whatsnew_btn.setEnabled(is_newer)

        check_for_update(__version__, dialog, _on_check_result)

        dialog.setLayout(layout)
        dialog.exec()

    def _show_bug_report_dialog(self):
        dialog = BugDialog(self)
        dialog.exec()

    def _toggle_select_all(self, checked: bool):
        """Vink alle checkboxes in kolom 0 aan of uit."""
        for row in range(self.table.rowCount()):
            widget = self.table.cellWidget(row, 0)
            if isinstance(widget, QCheckBox):
                widget.setChecked(checked)

    def _update_input_tooltip(self, search_type: str):
        if search_type == "Project":
            tip = "Typ projectnummer"
        elif search_type == "BP":
            tip = "Typ BP-nummer of naam"
        elif search_type == "VTA":
            tip = "Typ VTA-nummer"
        elif search_type == "Prod":
            tip = "Kies hierboven een dataset"
        else:
            tip = "Geef zoekterm in… geen prefix = zoeken op art.nr., * omschrijving, - kernwoorden, / leverancier"
        self.input_field.setToolTip(tip)
        self.input_field.setPlaceholderText(tip)

    def _set_combo_items(self, combo: QComboBox, items, current=None):
        combo.blockSignals(True)
        combo.clear()
        combo.addItems(items)
        if current is not None and current in items:
            combo.setCurrentText(current)
        combo.blockSignals(False)

    # NIEUW: centrale opslag van de "tweede" combobox
    def _handle_secondary_combo_change(self, value: str):
        if self.search_type_select.currentText() == "BP":
            # Opslaan als BP default type
            save_bp_default_type(value if value in ("", "C", "S") else "")
        else:
            # Opslaan als show_stock (alleen R/S/B)
            if value in ("R", "S", "B"):
                save_show_stock(value)

    def _toggle_fields_by_search_type(self, search_type: str):
        """
        - Standaard:     Zoekmodus zichtbaar, label='Toon voorraad:', items R/S/B
        - BP:            Zoekmodus zichtbaar, label='Type:', items "", C, S
        - Project:       Beide verbergen
        - Prod:          Beide verbergen; zoekterm-veld vervangen door
                          dataset-keuzelijst + magazijn-/tekstfilter
                          (resultaten inline in self.table, geen popup)
        """
        is_project = (search_type == "Project")
        is_bp = (search_type == "BP")
        is_vta = (search_type == "VTA")
        is_prod = (search_type == "Prod")

        # Zoekmodus verbergen bij Project, VTA en Prod
        hide_mode = is_project or is_vta or is_prod
        self.mode_label.setVisible(not hide_mode)
        self.mode_select.setVisible(not hide_mode)

        # Rij eronder: dynamisch label + items
        if is_project or is_vta or is_prod:
            # 👇 beide velden volledig verbergen
            self.stock_label.setVisible(False)
            self.show_stock_select.setVisible(False)
        elif is_bp:
            self.stock_label.setText("Type:")
            self.stock_label.setVisible(True)
            self.show_stock_select.setVisible(True)
            self._set_combo_items(self.show_stock_select, ["", "C", "S"], current=load_bp_default_type())
        else:
            self.stock_label.setText("Toon voorraad:")
            self.stock_label.setVisible(True)
            self.show_stock_select.setVisible(True)
            self._set_combo_items(self.show_stock_select, ["R", "S", "B"], current=load_show_stock())

        # Prod: zoekterm-veld verbergen, dataset-/magazijn-/filterkeuzelijsten tonen (en vice versa)
        self.zoekterm_label.setVisible(not is_prod)
        self.input_field.setVisible(not is_prod)
        self.prod_dataset_label.setVisible(is_prod)
        self.prod_dataset_select.setVisible(is_prod)
        self.prod_warehouse_label.setVisible(is_prod)
        self.prod_warehouse_select.setVisible(is_prod)
        self.prod_filter_label.setVisible(is_prod)
        self.prod_filter_input.setVisible(is_prod)
        self.prod_export_button.setVisible(is_prod)

        if is_prod:
            default_wh = load_prod_default_warehouse()
            idx = self.prod_warehouse_select.findData(default_wh) if default_wh else 0
            self.prod_warehouse_select.blockSignals(True)
            self.prod_warehouse_select.setCurrentIndex(idx if idx >= 0 else 0)
            self.prod_warehouse_select.blockSignals(False)
            self.prod_filter_input.blockSignals(True)
            self.prod_filter_input.clear()
            self.prod_filter_input.blockSignals(False)
            self._populate_prod_dataset_combo()
        else:
            # Cache leegmaken bij het verlaten van "Prod" (voorkomt verouderde
            # data bij een volgende _render_prod_table()-call door een
            # signaal dat nog "in-flight" was tijdens het wisselen).
            self._prod_raw_data = []
            self._prod_current_dataset = None
            self._last_prod_data = []
            self._last_prod_columns = []
            self._prod_sort_state = {"column_index": None, "ascending": True}

        # UI reset
        self.input_field.clear()
        self.input_field.setFocus()
        self.table.clearSelection()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.result_count_label.setText("Aantal resultaten: 0")
        if hasattr(self, 'select_all_checkbox'):
            self.select_all_checkbox.blockSignals(True)
            self.select_all_checkbox.setChecked(False)

    def _populate_prod_dataset_combo(self):
        """
        Vult self.prod_dataset_select met de beschikbare datasets
        (prod_info.list_datasets()), o.b.v. de standaardwaarden in settings:
        - standaard dataset (naam) ingesteld -> deze wordt voorgeselecteerd
          (uit de volledige lijst, ongeacht eigenaar-filter).
        - enkel standaard eigenaar ingesteld (geen dataset) -> de keuzelijst
          toont enkel datasets van die eigenaar.
        - geen van beide ingesteld -> volledige lijst, geen voorselectie.
        Gedeactiveerde datasets (DS_Lock) worden niet getoond.
        """
        from settings import load_prod_default_dataset_name, load_prod_default_dataset_owner

        default_name = load_prod_default_dataset_name()
        default_owner = load_prod_default_dataset_owner()

        self.prod_dataset_select.blockSignals(True)
        self.prod_dataset_select.clear()
        self._prod_datasets_cache = []

        try:
            from prod_info import list_datasets
            owner_filter = default_owner if (default_owner and not default_name) else ""
            datasets = list_datasets(owner=owner_filter)
            datasets = [d for d in datasets if str(d.get("DS_Lock") or "0") not in ("1", "true", "True")]
            self._prod_datasets_cache = datasets

            if not datasets:
                self.prod_dataset_select.addItem("⚠️ Geen datasets beschikbaar", None)
            else:
                for ds in datasets:
                    label = f"{ds.get('DS_Name', '')} ({ds.get('DS_Owner', '') or '-'})"
                    self.prod_dataset_select.addItem(label, ds)

                if default_name:
                    idx = next((i for i, d in enumerate(datasets) if d.get("DS_Name") == default_name), -1)
                    if idx >= 0:
                        self.prod_dataset_select.setCurrentIndex(idx)

        except Exception as e:
            logger.error(f"Kon Prod-datasets niet ophalen: {e}")
            self.prod_dataset_select.addItem(f"⚠️ Kon datasets niet laden: {e}", None)

        self.prod_dataset_select.blockSignals(False)

    # --------------- Helper: detail-payload normaliseren ---------------
    def _normalize_detail_payload(self, payload):
        """
        Converteer de respons van get_item_detail_stockinfo(*) naar een dictionary.
        Ondersteunt dict, list, str, bytes/bytearray en None.
        """
        if payload is None:
            return {}
        if isinstance(payload, dict):
            return payload
        if isinstance(payload, list):
            if payload and isinstance(payload[0], dict):
                return payload[0]  # vaak 1 record als [ {...} ]
            return {"RAW": payload}
        if isinstance(payload, (bytes, bytearray)):
            try:
                return json.loads(payload.decode("utf-8", errors="ignore"))
            except Exception:
                return {"RAW_TEXT": payload[:2000].decode("utf-8", errors="ignore")}
        if isinstance(payload, str):
            s = payload.strip()
            try:
                return json.loads(s)
            except Exception:
                return {"RAW_TEXT": s[:2000]}
        # laatste redmiddel
        return {"RAW": payload}

    # --------------- NIEUW: Export/Elements openen ---------------
    def _open_docs_window(self):
        """Opent ui_docs (Elements) vanuit het menu Export, alleen online en voor Finance."""
        from config import OFFLINE_MODE
        from permissions_azure import user_in_azure_group  # lokale import voor zekerheid

        # 🔒 Controleer of de applicatie offline draait
        if OFFLINE_MODE:
            QMessageBox.warning(
                self,
                "Offline modus",
                "De Export / Elements-module is niet beschikbaar in offline-modus."
            )
            return

        required_group = "GPP_Finance"

        try:
            if not user_in_azure_group(required_group):
                QMessageBox.warning(
                    self,
                    "Geen toegang",
                    f"U behoort niet tot de vereiste Azure AD-groep:\n\n{required_group}\n\n"
                    "Neem contact op met IT indien u toegang nodig heeft."
                )
                return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Azure AD fout",
                f"Kon groepsrechten niet controleren:\n{e}"
            )
            return

        # ✅ Toegang OK ➜ venster openen
        try:
            w = DocsWindow()
            w.showMaximized()
            self.docs_windows.append(w)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout",
                f"Kon 'Elements' openen:\n{e}"
            )

    def _open_duepayment_window(self):
        """Opent 'Betalingsgedrag & Openstaande Posten' (PaymentsDue) vanuit Export — zelfde AD-rechten als Open Elements."""
        from config import OFFLINE_MODE
        from permissions_azure import user_in_azure_group  # lokale import voor zekerheid

        # 🔒 Offline check
        if OFFLINE_MODE:
            QMessageBox.warning(
                self,
                "Offline modus",
                "De module 'Betalingsgedrag' is niet beschikbaar in offline-modus."
            )
            return

        required_group = "GPP_Finance"  # zelfde vereiste groep als Open Elements

        try:
            if not user_in_azure_group(required_group):
                QMessageBox.warning(
                    self,
                    "Geen toegang",
                    f"U behoort niet tot de vereiste Azure AD-groep:\n\n{required_group}\n\n"
                    "Neem contact op met IT indien u toegang nodig heeft."
                )
                return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Azure AD fout",
                f"Kon groepsrechten niet controleren:\n{e}"
            )
            return

        # ✅ Toegang OK ➜ venster openen
        try:
            w = DuePaymentWindow()
            w.showMaximized()
            self.duepayment_windows.append(w)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout",
                f"Kon 'Betalingsgedrag' openen:\n{e}"
            )

    def _open_ccbp_window(self):
        """Open het Credit Control (BP) venster (met beveiligingscontrole)."""
        from config import OFFLINE_MODE

        # 🔒 Controleer of de applicatie offline draait
        if OFFLINE_MODE:
            QMessageBox.warning(
                self,
                "Offline modus",
                "De Credit Control-module is niet beschikbaar in offline-modus."
            )
            return

        try:
            w = CreditControlWindow()
            w.showMaximized()
            self.docs_windows.append(w)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout bij openen Credit Control (BP)",
                f"Kon Credit Control niet openen:\n{e}"
            )

    def _open_timings_window(self):
        """Open het Timings-venster (Urenregistratie via SharePoint) — alleen voor CGK-APP-L1 leden."""
        from config import OFFLINE_MODE
        from permissions_azure import user_in_azure_group

        # 🔒 Offline check
        if OFFLINE_MODE:
            QMessageBox.warning(
                self,
                "Offline modus",
                "De module 'Timings' is niet beschikbaar in offline-modus."
            )
            return

        required_group = "CGK-APP-L1"

        try:
            # ✅ Controleer Azure AD groepslidmaatschap
            if not user_in_azure_group(required_group):
                QMessageBox.warning(
                    self,
                    "Toegang geweigerd",
                    f"U hebt geen rechten om de module 'Timings' te openen.\n\n"
                    f"Vereiste Azure AD-groep:\n→ {required_group}\n\n"
                    "Neem contact op met IT indien u toegang nodig hebt."
                )
                return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Azure AD fout",
                f"Kon groepsrechten niet controleren:\n{e}"
            )
            return

        # ✅ Toegang OK ➜ venster openen
        try:
            from ui_timings import ExcelApp

            w = ExcelApp()
            w.setParent(None)
            w.setWindowModality(Qt.NonModal)
            w.setWindowFlag(Qt.Window, True)

            # Referentie bijhouden zodat venster niet verdwijnt
            if not hasattr(self, "timings_windows"):
                self.timings_windows = []
            self.timings_windows.append(w)

            w.show()
            w.activateWindow()
            w.raise_()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout bij openen Timings",
                f"Kon 'Timings' niet openen:\n{e}"
            )

    # ✅ NIEUW: Peppol check (CGK-APP-L1 of CGK-APP-L2)
    def _open_peppol_check_window(self):
        """Open 'Peppol check' — alleen voor CGK-APP-L1 en CGK-APP-L2."""
        from config import OFFLINE_MODE
        from permissions_azure import user_in_azure_group

        # 🔒 Offline check
        if OFFLINE_MODE:
            QMessageBox.warning(
                self,
                "Offline modus",
                "De module 'Peppol check' is niet beschikbaar in offline-modus."
            )
            return

        required_groups = ("CGK-APP-L1", "CGK-APP-L2")

        try:
            if not any(user_in_azure_group(g) for g in required_groups):
                QMessageBox.warning(
                    self,
                    "Toegang geweigerd",
                    "U hebt geen rechten om de module 'Peppol check' te openen.\n\n"
                    "Vereiste Azure AD-groep:\n→ CGK-APP-L1 of CGK-APP-L2\n\n"
                    "Neem contact op met IT indien u toegang nodig hebt."
                )
                return
        except Exception as e:
            QMessageBox.critical(
                self,
                "Azure AD fout",
                f"Kon groepsrechten niet controleren:\n{e}"
            )
            return

        # ✅ Toegang OK ➜ venster openen
        try:
            w = PepWidget()
            w.setParent(None)
            w.setWindowModality(Qt.NonModal)
            w.setWindowFlag(Qt.Window, True)

            self.pep_windows.append(w)

            w.show()
            w.activateWindow()
            w.raise_()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Fout bij openen Peppol check",
                f"Kon 'Peppol check' niet openen:\n{e}"
            )