# =============================================================================
# ArticleSearch
# File:    ui_peppol_v2.py
# Role:    TESTBESTAND — herontwerp van het Peppol-controlescherm
#          (cf. peppol_ontwerpbrief_v1.md). Draait naast het bestaande,
#          ongewijzigde ui_peppol.py (dat de eindgebruiker voorlopig nog
#          gebruikt) en gebruikt dezelfde live API-connectie (pep_token.py/
#          config.py) — geen mock-/sample-data.
# Version: 0.8.0
# Author:  Bart Bossuyt
# Changes: 0.8.0 — Onbekende foutcodes worden nu duidelijk gemarkeerd
#                   (cf. ontwerpbrief "Statuslijst": ⚠️ Onbekende fout):
#                   gele achtergrond + prefix in de statustabel. Nieuwe
#                   helper _is_recognized(). Pop-up krijgt bij een
#                   onbekende code twee knoppen: "Kopieer ruwe boodschap"
#                   (klembord, met korte visuele bevestiging) en "Meld via
#                   GitHub (Feature)" — opent het bestaande BugDialog
#                   (bug_report_dialog.py, nu uitgebreid met
#                   initial_type/initial_description) vooraf ingevuld met
#                   type "Feature-aanvraag" en de volledige ruwe boodschap
#                   + factuurnummer. Bewuste keuze op vraag van gebruiker:
#                   hergebruik van het bestaande GitHub-rapportagekanaal,
#                   geen nieuw/parallel meldingsmechanisme.
# Changes: 0.7.0 — UI-opkuis op vraag van gebruiker:
#                   - Kolom "Line" (U_LineNum) verwijderd uit de status-
#                     tabel — geen nut voor de eindgebruiker.
#                   - Zoekveld ("Zoek in statusregels") + bijhorende
#                     filter_status_table()-logica volledig verwijderd:
#                     door de dedupe (v0.4.0) blijft er doorgaans nog maar
#                     1 rij per fout over, waardoor zoeken geen meerwaarde
#                     meer heeft. self.status_cache (enkel gebruikt door
#                     de verwijderde filterlogica) is hierdoor ook
#                     overbodig geworden en verwijderd.
# Changes: 0.6.0 — Header-icoon houdt nu rekening met de severity van
#                   herkende foutcodes, niet enkel met U_TaskStatus. Nieuwe
#                   helper _highest_recognized_severity(): bepaalt de
#                   hoogste severity ("error" > "warning" > geen herkende
#                   code) onder de (gededupliceerde) statusregels via
#                   pep_errors.json. _interpret_task_status() krijgt een
#                   nieuw optioneel argument recognized_severity, dat
#                   voorrang krijgt op de U_TaskStatus/U_ActionPerformed-
#                   heuristiek: een herkende "warning"-code (bv. "reeds
#                   verstuurd/in wachtrij") toont nu ⚠️ i.p.v. onterecht
#                   🔴 Fout, ook al meldt de API zelf U_TaskStatus=FAILED.
#                   Zonder herkende code valt de functie terug op de
#                   bestaande, voorlopige U_TaskStatus-heuristiek.
#                   load_data() herschikt: statusregels worden nu vóór
#                   show_header_info() opgehaald/gededupliceerd, zodat de
#                   severity al gekend is wanneer de header getekend wordt.
# Changes: 0.5.0 — BUGFIX (aanwezig sinds ui_peppol.py v1.0.3, nu pas
#                   opgemerkt bij het eerste geslaagde live-testgeval):
#                   pep_errors.json is genamespaced per leverancier
#                   ({"GF": {"<code>": {...}}}, cf. ontwerpbrief), maar
#                   translate_status_message()/translate_api_error()
#                   deden self.error_map.get(code) — dat zoekt op het
#                   TOP-LEVEL (waar enkel "GF" als key staat), niet in de
#                   "GF"-sub-dict waar de codes werkelijk zitten. Hierdoor
#                   werd een herkende code nooit gematcht, ook niet nadat
#                   v0.4.0 de code-extractie zelf al correct kreeg
#                   (bevestigd: dedupe met dezelfde extractie werkte al
#                   wél, want die viel toevallig terug op identieke ruwe
#                   tekst als sleutel — de code-match zelf werd nooit
#                   verondersteld). Nieuwe helper _lookup_error(code):
#                   doorzoekt alle leverancier-namespaces in de registry
#                   (momenteel enkel "GF" — cf. ontwerpbrief, bewust
#                   hardcoded tot er een 2e leverancier + een manier om
#                   die te identificeren in de API-respons bijkomt).
# Changes: 0.4.0 — Regex-fallback + dedupe van retries + bugfix filter:
#                   - Nieuwe helper _extract_code_description_from_text():
#                     probeert eerst nette json.loads(), valt bij falen
#                     terug op regex-extractie van "Code"/"code" en
#                     "Description"/"detail" — nodig omdat U_Message soms
#                     structureel afgekapt is (geen sluithaakjes, cf.
#                     ontwerpbrief punt 1) waardoor json.loads() faalt en
#                     een herkende foutcode (bevestigd met live data:
#                     This_0_WasAlreadySentLessThen_1_MinutesAgoTo_2_
#                     OrIsStillInTheQueue) voorheen ONVERTAALD bleef.
#                     translate_status_message() gebruikt deze helper nu
#                     i.p.v. rechtstreeks json.loads().
#                   - Nieuwe _dedupe_status_rows(): dedupliceert opeen-
#                     volgende retries met dezelfde herkende code (of,
#                     zonder herkende code, identieke ruwe boodschap) tot
#                     1 rij + pogingenteller (cf. ontwerpbrief punt 4;
#                     bevestigd met live data: 3 identieke regels voor
#                     dezelfde fout). Sorteert eerst op U_CreateDateTime
#                     (U_LineNum is niet betrouwbaar oplopend). Nieuwe
#                     kolom "Pogingen" in de statustabel; pop-up toont het
#                     aantal pogingen wanneer > 1.
#                   - BUGFIX: self.status_cache (volledige, ongefilterde
#                     rijenset — gebruikt door filter_status_table()) werd
#                     sinds v0.2.0 nergens meer gezet (enkel
#                     self._displayed_rows), waardoor het zoekveld altijd
#                     op een lege lijst filterde. load_data() zet nu
#                     status_cache expliciet na het dedupliceren;
#                     show_status_table() blijft enkel _displayed_rows
#                     bijhouden (voor de pop-up-rij-mapping).
# Changes: 0.3.0 — Code-/beschrijving-extractie uit U_Message nu case-
#                   insensitief: de "technische" foutvorm uit de API
#                   gebruikt een kleine letter "code" (+ "detail") i.p.v.
#                   "Code"/"Description" bij de "business"-foutvorm (cf.
#                   peppol_ontwerpbrief_v1.md, vaststelling 2) — de parser
#                   herkende deze technische vorm voorheen nooit. Nieuwe
#                   gedeelde helper _extract_code_description(), gebruikt
#                   door zowel translate_status_message() als
#                   translate_api_error(). pep_errors.json overgezet naar
#                   het meertalige schema (title/user_message als
#                   {"nl": "..."} i.p.v. platte string) — inhoud ongewijzigd,
#                   enkel structuur, klaar om later "fr"/"en" toe te voegen.
# Changes: 0.2.0 — Dubbelklik op een statusregel toont nu een pop-up met
#                   (1) de volledige RUWE boodschap zoals ontvangen van de
#                   API en (2) de vertaalde/weergegeven boodschap ernaast.
#                   Doel: de tabelcel toonde de boodschap afgekapt (Qt-
#                   eliding bij smalle kolom), waardoor niet duidelijk was
#                   of de brontekst zelf ook afgekapt is (cf. ontwerpbrief
#                   punt 1) — deze pop-up geeft altijd de volledige
#                   beschikbare tekst, nodig als basis voor de parser-
#                   herbouw in een volgende stap. Nieuwe helper
#                   self._displayed_rows onthoudt de op dit moment getoonde
#                   (evt. gefilterde) rijen, zodat een tabel-rij-index
#                   correct terugverwijst naar de bijhorende ruwe dict.
# Changes: 0.1.0 — Initieel testbestand, kopie van ui_peppol.py v1.0.3.
#                   Stap 1 van het herontwerp:
#                   - self.lang komt nu uit settings.load_language()
#                     (lowercased + gevalideerd), i.p.v. hardgecodeerd "nl".
#                     Nodig vóór pep_errors.json meertalig gevuld wordt.
#                   - Header-blok herontworpen o.b.v. het nieuwe INFO-blok
#                     in de API-respons: documenttype (NL-label afgeleid
#                     van DocumentType/SourceTable) + documentnummer,
#                     klant naam+code, klant-referentie (NumAtCard),
#                     taakstatus-indicator (✅/🔴/⏳).
#                   - Taakstatus-interpretatie (_interpret_task_status) is
#                     BEWUST voorlopig/behoudend: exacte betekenis van
#                     U_ActionPerformed per SourceTable is nog niet
#                     bevestigd (zie ontwerpbrief, open punt 3) — onbekende
#                     combinaties tonen ⏳ i.p.v. te crashen of foutief als
#                     fout/succes te classificeren.
#                   Nog NIET aangepast in deze stap (volgt later):
#                   statuslijst-herontwerp (dedup van retries, markering
#                   onbekende codes, "Meld aan IT"-knop, detail-pop-up voor
#                   volledige omschrijving).
# =============================================================================

import sys
import json
import re
from pathlib import Path

import requests
from PySide6.QtWidgets import (
    QApplication, QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout,
    QTextEdit, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QTabWidget, QHBoxLayout, QDialog
)
from PySide6.QtGui import QKeySequence, QShortcut, QColor
from PySide6.QtCore import Qt, QTimer

from pep_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT
from settings import load_language
from bug_report_dialog import BugDialog


# -----------------------------
# Error mapping (external JSON)
# -----------------------------
ERROR_MAP_PATH = Path("pep_errors.json")

# NL-labels per SourceTable — cf. ontwerpbrief §"Schermontwerp".
# Onbekende SourceTable-waarden vallen terug op de rauwe DocumentType/
# SourceTable-tekst (tolerant, niet crashen — cf. ontwerpbrief punt 7).
DOCUMENT_TYPE_LABELS = {
    "OINV": "Verkoopfactuur",
    "ORIN": "Creditnota",
    "ODPI": "Downpayment",
    "OPOR": "Aankooporder",
}

VALID_LANGS = {"nl", "fr", "en"}


def load_error_map() -> dict:
    """
    Laadt error mapping uit pep_errors.json.
    Als bestand ontbreekt/kapot is: return {} (fallback blijft werken).
    """
    if not ERROR_MAP_PATH.exists():
        return {}

    try:
        with open(ERROR_MAP_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def format_datetime_for_header(dt_str: str) -> tuple[str, str]:
    if not dt_str:
        return "-", "-"
    s = str(dt_str).strip()

    if len(s) < 10 or s[4] != "-" or s[7] != "-":
        return "-", "-"

    date_part = f"{s[8:10]}-{s[5:7]}-{s[0:4]}"

    time_part = "-"
    if len(s) >= 16 and s[10] == " ":
        hh = s[11:13]
        mm = s[14:16]
        if hh.isdigit() and mm.isdigit():
            time_part = f"{hh}:{mm}"

    return date_part, time_part


def format_datetime_ddmmyyyy_hhmm(dt_str: str) -> str:
    d, t = format_datetime_for_header(dt_str)
    if d == "-" and t == "-":
        return "-"
    return f"{d} {t}"


def _interpret_task_status(
    source_table: str,
    task_status: str,
    action_performed: str,
    recognized_severity: str | None = None,
) -> tuple[str, str]:
    """
    Bepaalt icoon + korte NL-tekst voor de taakstatus-indicator in de header.

    recognized_severity (optioneel) = de hoogste severity ("error"/
    "warning") onder de herkende foutcodes in de statusregels (cf.
    _highest_recognized_severity()). Krijgt VOORRANG op de onderstaande
    U_TaskStatus-heuristiek: een herkende "warning"-code (bv. "reeds
    verstuurd/in wachtrij") toont ⚠️ i.p.v. onterecht 🔴 Fout, ook al meldt
    de API zelf U_TaskStatus=FAILED — bevestigd met live data (factuur
    260700195: FAILED + herkende warning-code "reeds in wachtrij").
    Zonder herkende code valt terug op onderstaande, BEWUST VOORLOPIGE
    heuristiek (cf. ontwerpbrief, open punt 3 + vaststelling 6/7):
    - U_ActionPerformed betekent niet overal hetzelfde per SourceTable
      (bv. bij OPOR is "N" soms een normale uitkomst i.p.v. een probleem).
    - U_TaskType kan waarden bevatten die nog niet allemaal in kaart zijn
      gebracht (o.a. een vermoede "in queue/wachtend"-status).
    Onbekende/onduidelijke combinaties krijgen daarom een neutrale ⏳-status
    i.p.v. foutief als succes/fout geclassificeerd te worden. Deze functie
    is een geïsoleerd aanknopingspunt om later per SourceTable te verfijnen,
    zonder de rest van de UI te moeten aanpassen.
    """
    if recognized_severity == "error":
        return "🔴", "Fout"
    if recognized_severity == "warning":
        return "⚠️", "Waarschuwing"

    ts = (task_status or "").strip().upper()
    ap = (action_performed or "").strip().upper()

    if ts == "FAILED":
        return "🔴", "Fout"

    if ts in ("COMPLETED", "SUCCESS", "DONE", "OK"):
        if ap == "Y":
            return "✅", "Voltooid"
        # Geen actie uitgevoerd — bij OPOR mogelijk normaal, bij andere
        # types nog te bevestigen. Neutraal tonen i.p.v. als fout.
        return "⏳", "Voltooid (geen actie)"

    # Onbekende/wachtende status (bv. NOT_QUEUE of een nog-onbevestigde
    # "in queue"-waarde) — tolerant afhandelen, niet crashen.
    return "⏳", task_status or "Onbekend"


def _extract_code_description(first_error: dict) -> tuple[str | None, str]:
    """
    Haalt code + omschrijving uit één element van de "errors"-lijst,
    tolerant voor beide vastgestelde vormen (cf. peppol_ontwerpbrief_v1.md):
      - business-fouten:  {"Code": "...", "Description": "..."}
      - technische fouten: {"code": "...", "meta": {...}, "detail": "..."}
    """
    code = first_error.get("Code", first_error.get("code"))
    description = first_error.get("Description", first_error.get("detail", ""))
    return code, description


def _extract_code_description_from_text(raw_message: str) -> tuple[str | None, str]:
    """
    Haalt Code/Description uit een ruwe U_Message-string, ROBUUST tegen
    structureel afgekapte/onvolledige JSON (cf. ontwerpbrief punt 1 — de
    brontekst zelf kan al onvolledig zijn, zonder sluithaakjes, bevestigd
    met live data op 2026-08-06).

    Volgorde:
      1) Nette json.loads() vanaf het eerste '{' — werkt voor korte/niet-
         afgekapte boodschappen.
      2) Bij falen: regex-extractie die ook op onvolledige tekst werkt
         (pakt alles na "Description"/"detail" tot het einde van de
         string, zonder een sluitende aanhalingsteken te vereisen).
    """
    if not raw_message or "{" not in raw_message:
        return None, ""

    json_part = raw_message[raw_message.index("{"):]

    # 1) Nette JSON
    try:
        parsed = json.loads(json_part)
        errors = parsed.get("errors")
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            return _extract_code_description(errors[0])
    except Exception:
        pass

    # 2) Regex-fallback voor afgekapte/onvolledige JSON
    code_match = re.search(r'"[Cc]ode"\s*:\s*"([^"]*)"', json_part)
    code = code_match.group(1) if code_match else None

    desc_match = re.search(r'"(?:Description|detail)"\s*:\s*"(.*)', json_part, re.DOTALL)
    description = desc_match.group(1) if desc_match else ""
    # Als de JSON toch nette afsluiters bevat, die niet als tekst meenemen
    description = re.sub(r'"\s*\}\s*\]\s*\}\s*\Z', '', description).strip()

    return code, description


class PepWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Peppol Invoice status (TEST — herontwerp)")
        self.resize(1200, 800)

        # Load external error map once
        self.error_map = load_error_map()

        # Taal uit gebruikersinstellingen (settings.json), niet meer
        # hardgecodeerd. Fallback naar "nl" bij onbekende/lege waarde.
        lang = (load_language() or "nl").strip().lower()
        self.lang = lang if lang in VALID_LANGS else "nl"

        layout = QVBoxLayout(self)

        # --- Invoice input ---
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Geef factuur nummer in")
        layout.addWidget(QLabel("Invoice Nbr:"))
        layout.addWidget(self.key_input)

        # --- Buttons ---
        btn_row = QHBoxLayout()
        self.fetch_button = QPushButton("Ophalen")
        self.fetch_button.clicked.connect(self.load_data)
        btn_row.addWidget(self.fetch_button)

        self.clear_button = QPushButton("Wissen")
        self.clear_button.clicked.connect(self.clear_input)
        btn_row.addWidget(self.clear_button)
        btn_row.addStretch(1)
        layout.addLayout(btn_row)

        # --- Header info (herontworpen) ---
        self.header_text = QTextEdit()
        self.header_text.setReadOnly(True)
        self.header_text.setFixedHeight(110)
        layout.addWidget(QLabel("Documentinfo:"))
        layout.addWidget(self.header_text)

        # --- Tabs ---
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.info_tab = QWidget()
        info_layout = QVBoxLayout(self.info_tab)

        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        self.table.cellDoubleClicked.connect(self._show_message_popup)
        info_layout.addWidget(self.table)

        self.tabs.addTab(self.info_tab, "Info")

        self._displayed_rows = []

        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.load_data)
        QShortcut(QKeySequence(Qt.Key_Escape), self).activated.connect(self.close)

    # -----------------------------
    # Helper: string OR dict -> string
    # -----------------------------
    def _pick_text(self, value, fallback: str = "") -> str:
        """
        Ondersteunt:
          - "tekst" (string)
          - {"nl": "tekst", "fr": "texte", "en": "text"} (dict)
        """
        if isinstance(value, str):
            return value
        if isinstance(value, dict) and value:
            # voorkeurstaal, anders eerste waarde
            if self.lang in value and isinstance(value[self.lang], str):
                return value[self.lang]
            for v in value.values():
                if isinstance(v, str):
                    return v
        return fallback

    def _lookup_error(self, code: str | None):
        """
        Zoekt een foutcode op in de per-leverancier genamespaced registry
        (pep_errors.json: {"GF": {"<code>": {...}}, ...}).
        Momenteel is er slechts één leverancier ("GF") — deze functie
        doorzoekt sowieso alle top-level leverancier-namespaces, zodat ze
        blijft werken zodra er een 2e leverancier bijkomt, zonder dat we
        vandaag al hoeven te bepalen welke leverancier bij een gegeven
        document hoort (dat onderscheid bestaat nog niet in de API-
        respons — zie ontwerpbrief, open punten).
        """
        if not code:
            return None
        for supplier_map in self.error_map.values():
            if isinstance(supplier_map, dict) and code in supplier_map:
                return supplier_map[code]
        return None

    def _is_recognized(self, raw_message: str) -> bool:
        """
        True als de foutcode in raw_message herkend wordt in
        pep_errors.json (via _lookup_error). Gebruikt om onbekende codes
        visueel te markeren in de statustabel/pop-up (cf. ontwerpbrief).
        """
        code, _ = _extract_code_description_from_text(raw_message)
        return self._lookup_error(code) is not None

    def _highest_recognized_severity(self, rows: list[dict]) -> str | None:
        """
        Bepaalt de hoogste severity ("error" > "warning") onder de
        HERKENDE foutcodes in de gegeven statusregels, via pep_errors.json.
        Geeft None terug als geen enkele regel een herkende code heeft —
        in dat geval valt _interpret_task_status() terug op de
        U_TaskStatus-heuristiek. Gebruikt om te vermijden dat een herkende,
        onschuldige "warning"-code (bv. "reeds verstuurd/in wachtrij") de
        header onterecht als 🔴 Fout toont enkel omdat U_TaskStatus=FAILED.
        """
        priority = {"error": 2, "warning": 1}
        best_severity = None
        best_rank = 0
        for r in rows:
            raw = str(r.get("U_Message", ""))
            code, _ = _extract_code_description_from_text(raw)
            mapped = self._lookup_error(code)
            if isinstance(mapped, dict):
                sev = mapped.get("severity")
                rank = priority.get(sev, 0)
                if rank > best_rank:
                    best_rank = rank
                    best_severity = sev
        return best_severity

    def clear_input(self):
        self.key_input.clear()
        self.key_input.setFocus()

    def clear_table(self):
        self._displayed_rows = []
        self.table.clear()
        self.table.setRowCount(0)
        self.table.setColumnCount(0)

    # -----------------------------
    # Header-blok (herontworpen — INFO-blok + taakstatus-indicator)
    # -----------------------------
    def _extract_info(self, api_json: dict) -> dict:
        """
        INFO bevat altijd exact 1 element voor de opgevraagde documentsleutel
        (bevestigd in de ontwerpbrief) — geen array-filtering nodig.
        Tolerant: geeft {} terug als INFO ontbreekt/leeg is.
        """
        data_field = api_json.get("Data", {})
        if not isinstance(data_field, dict):
            return {}
        info_list = data_field.get("INFO", [])
        if isinstance(info_list, list) and info_list and isinstance(info_list[0], dict):
            return info_list[0]
        return {}

    def show_header_info(self, api_json: dict, recognized_severity: str | None = None):
        data_field = api_json.get("Data", {})
        info = self._extract_info(api_json)

        task_status = "-"
        action_performed = ""
        datum, tijd = "-", "-"

        if isinstance(data_field, dict):
            task = data_field.get("TASK", {})
            if isinstance(task, dict):
                task_status = task.get("U_TaskStatus", "-")
                action_performed = task.get("U_ActionPerformed", "")
                datum, tijd = format_datetime_for_header(task.get("U_CreateDateTime", ""))

        source_table = info.get("SourceTable", "")
        doc_type_raw = info.get("DocumentType", "")
        doc_label = DOCUMENT_TYPE_LABELS.get(source_table, doc_type_raw or source_table or "-")
        doc_num = info.get("DocNum", "-")

        card_name = info.get("CardName", "-")
        card_code = info.get("CardCode", "-")
        num_at_card = info.get("NumAtCard", "-")

        icon, status_label = _interpret_task_status(source_table, task_status, action_performed, recognized_severity)

        self.header_text.setPlainText(
            f"{doc_label}  —  Nr. {doc_num}\n"
            f"Klant/leverancier: {card_name} ({card_code})\n"
            f"Referentie klant: {num_at_card}\n"
            f"Status: {icon} {status_label}   |   Datum: {datum} {tijd}"
        )

    def extract_status_rows(self, api_json: dict) -> list[dict]:
        task = api_json.get("Data", {}).get("TASK", {})
        rows = task.get("STATUS", [])
        return [r for r in rows if isinstance(r, dict)]

    def _dedupe_status_rows(self, rows: list[dict]) -> list[dict]:
        """
        Dedupliceert opeenvolgende retries tot 1 rij + pogingenteller —
        cf. ontwerpbrief punt 4 ("2-3 identieke STATUS-regels na elkaar",
        bevestigd met live data: 3x dezelfde fout voor factuur 260700195).

        Sleutel = herkende foutcode indien beschikbaar, anders de ruwe
        boodschap zelf (tolerant voor niet-herkende/technische fouten).
        Rijen worden eerst gesorteerd op U_CreateDateTime, want U_LineNum
        loopt niet betrouwbaar op (cf. ontwerpbrief punt 4). De getoonde
        rij bevat telkens de MEEST RECENTE poging (laatste timestamp).
        """
        sorted_rows = sorted(rows, key=lambda r: str(r.get("U_CreateDateTime", "")))

        deduped: list[dict] = []
        for r in sorted_rows:
            raw = str(r.get("U_Message", ""))
            code, _ = _extract_code_description_from_text(raw)
            dedupe_key = code or raw

            if deduped and deduped[-1].get("_dedupe_key") == dedupe_key:
                last = deduped[-1]
                last["_attempt_count"] += 1
                # Nieuwste poging tonen (meest recente timestamp/regel)
                last["U_CreateDateTime"] = r.get("U_CreateDateTime", last.get("U_CreateDateTime"))
                last["U_LineNum"] = r.get("U_LineNum", last.get("U_LineNum"))
                last["U_Message"] = raw
            else:
                merged = dict(r)
                merged["_dedupe_key"] = dedupe_key
                merged["_attempt_count"] = 1
                deduped.append(merged)

        return deduped

    # -----------------------------
    # Status message translation
    # -----------------------------
    def translate_status_message(self, raw_message: str) -> str:
        """
        Vertaalt statusregel fouten via pep_errors.json — robuust tegen
        afgekapte/onvolledige JSON in raw_message (zie
        _extract_code_description_from_text()).
        Fallback = exact originele tekst.
        """
        code, description = _extract_code_description_from_text(raw_message)

        mapped = self._lookup_error(code)
        if isinstance(mapped, dict):
            return self._pick_text(mapped.get("user_message"), fallback=str(description) or raw_message)

        return raw_message

    def show_status_table(self, rows: list[dict]):
        # Onthoud exact welke (evt. gefilterde) rijen nu getoond worden, in
        # dezelfde volgorde als de tabel — nodig om een dubbelklikte
        # tabel-rij-index terug te koppelen aan de juiste ruwe dict.
        self._displayed_rows = rows

        columns = [
            ("U_CreateDateTime", "Datum"),
            ("_attempt_count", "Pogingen"),
            ("U_Message", "Message"),
        ]

        self.table.setSortingEnabled(False)
        self.table.clear()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels([c[1] for c in columns])
        self.table.setRowCount(len(rows))

        for r_idx, r in enumerate(rows):
            raw_msg_for_row = str(r.get("U_Message", ""))
            recognized = self._is_recognized(raw_msg_for_row)

            for c_idx, (key, _) in enumerate(columns):
                val = r.get(key, "" if key != "_attempt_count" else 1)

                if key == "U_CreateDateTime":
                    val = format_datetime_ddmmyyyy_hhmm(val)

                if key == "U_Message":
                    val = self.translate_status_message(str(val))
                    if not recognized:
                        val = f"⚠️ Onbekende fout — {val}"

                item = QTableWidgetItem(str(val))
                if not recognized:
                    item.setBackground(QColor("#fff3cd"))
                self.table.setItem(r_idx, c_idx, item)

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)

    def _show_message_popup(self, row_idx: int, _column: int = 0):
        """
        Toont de volledige ruwe boodschap + de vertaalde/weergegeven
        boodschap van de dubbelgeklikte statusregel in een pop-up.
        """
        if not (0 <= row_idx < len(self._displayed_rows)):
            return

        row = self._displayed_rows[row_idx]
        raw_message = str(row.get("U_Message", ""))
        translated = self.translate_status_message(raw_message)
        attempt_count = row.get("_attempt_count", 1)
        recognized = self._is_recognized(raw_message)

        dlg = QDialog(self)
        dlg.setWindowTitle("Statusdetail")
        dlg.resize(720, 420)
        dlg_layout = QVBoxLayout(dlg)

        if attempt_count > 1:
            dlg_layout.addWidget(QLabel(f"⚠️ Deze fout deed zich {attempt_count}x na elkaar voor (gededupliceerd tot 1 rij)."))

        if not recognized:
            dlg_layout.addWidget(QLabel("⚠️ Deze foutcode is niet herkend in pep_errors.json."))

        dlg_layout.addWidget(QLabel("Weergegeven boodschap (vertaald indien code herkend):"))
        translated_box = QTextEdit()
        translated_box.setReadOnly(True)
        translated_box.setPlainText(translated)
        translated_box.setFixedHeight(80)
        dlg_layout.addWidget(translated_box)

        dlg_layout.addWidget(QLabel("Volledige ruwe boodschap (zoals ontvangen van de API):"))
        raw_box = QTextEdit()
        raw_box.setReadOnly(True)
        raw_box.setPlainText(raw_message)
        dlg_layout.addWidget(raw_box)

        if not recognized:
            action_row = QHBoxLayout()

            copy_btn = QPushButton("Kopieer ruwe boodschap")
            copy_btn.clicked.connect(lambda: self._copy_to_clipboard_with_feedback(raw_message, copy_btn))
            action_row.addWidget(copy_btn)

            report_btn = QPushButton("Meld via GitHub (Feature)")
            report_btn.clicked.connect(lambda: self._report_unknown_error(raw_message, dlg))
            action_row.addWidget(report_btn)

            dlg_layout.addLayout(action_row)

        close_btn = QPushButton("Sluiten")
        close_btn.clicked.connect(dlg.close)
        dlg_layout.addWidget(close_btn)

        dlg.exec()

    def _copy_to_clipboard_with_feedback(self, text: str, button: QPushButton):
        QApplication.clipboard().setText(text)
        original_text = button.text()
        button.setText("Gekopieerd ✅")
        button.setEnabled(False)
        QTimer.singleShot(1200, lambda: (button.setText(original_text), button.setEnabled(True)))

    def _report_unknown_error(self, raw_message: str, parent_dialog: QDialog):
        invoice_nbr = self.key_input.text().strip()
        description = (
            "Onbekende Peppol-foutcode (nog niet in pep_errors.json).\n\n"
            f"Factuurnummer: {invoice_nbr or '-'}\n\n"
            "Ruwe boodschap zoals ontvangen van de API:\n"
            f"{raw_message}"
        )
        report_dlg = BugDialog(
            parent=parent_dialog,
            initial_type="Feature-aanvraag",
            initial_description=description,
        )
        report_dlg.exec()

    def translate_api_error(self, api_json: dict) -> tuple[str, str]:
        errors = api_json.get("errors", [])
        if isinstance(errors, list) and errors and isinstance(errors[0], dict):
            first = errors[0]
            code, description = _extract_code_description(first)

            mapped = self._lookup_error(code)
            if isinstance(mapped, dict):
                title = self._pick_text(mapped.get("title"), fallback="API Fout")
                user_msg = self._pick_text(mapped.get("user_message"), fallback=str(description))
                return title, user_msg

            return "API Fout", str(description)

        return "API Fout", str(api_json.get("ErrorMessage") or "Onbekende fout")

    def load_data(self):
        invoice_nbr = self.key_input.text().strip()
        if not invoice_nbr:
            QMessageBox.warning(self, "Fout", "Geef een geldig factuurnummer in.")
            return

        env = API_ENVIRONMENTS[ENVIRONMENT]
        url = f"{env.get('base_url')}/api/datarequest"

        payload = {"ConfigurationID": env["pep_config_id"], "Key": invoice_nbr}
        headers = get_auth_header()
        headers.setdefault("Content-Type", "application/json")

        try:
            resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            # Statusregels + severity eerst bepalen, zodat het header-
            # icoon rekening kan houden met een herkende warning-code
            # i.p.v. blind op U_TaskStatus af te gaan.
            deduped_rows = self._dedupe_status_rows(self.extract_status_rows(data))
            recognized_severity = self._highest_recognized_severity(deduped_rows)

            self.show_header_info(data, recognized_severity=recognized_severity)

            if data.get("IsError"):
                title, msg = self.translate_api_error(data)
                QMessageBox.critical(self, title, msg)
                self.clear_table()
                return

            self.show_status_table(deduped_rows)
            self.tabs.setCurrentWidget(self.info_tab)

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "Fout", f"Request error: {e}")
        except ValueError:
            QMessageBox.critical(self, "Fout", "Response was geen geldige JSON.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = PepWidget()
    w.show()
    sys.exit(app.exec())