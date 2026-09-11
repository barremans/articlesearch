# =============================================================================
# ArticleSearch
# File:    oeoverview_info.py
# Role:    "Open Elements overview" — bedrijfslogica (geen API/token nodig):
#          kandidaat-bronbestanden (CSV én/of Excel) zoeken in een inputmap,
#          twee SAP B1-exports (openstaande orders/leveringen) inlezen en
#          valideren, groeperen per verkoopmedewerker (SalesOwner met
#          DocOwner-fallback), filteren op leeftijd (MaandenOud) en
#          wegschrijven naar xlsx/csv per medewerker. Overgenomen uit het
#          losstaande, reeds geteste "OpenElements2Csv"-prototype
#          (csv_loader.py/processor.py/exporter.py) en samengevoegd tot 1
#          bestand volgens het `*_info.py`-patroon van ArticleSearch —
#          bewust GEEN `*_token.py`, er is geen authenticatie/live SAP-
#          koppeling voor dit onderdeel.
# Version: 1.3.0
# Author:  Bart Bossuyt
# Changes: 1.3.0 — UX-verbetering na een reële vergissing (orders-/
#                   leveringen-bestand omgewisseld via "Bladeren...", 2
#                   bijna-identieke bestandsnamen naast elkaar):
#                   _validate_header() geeft nu, wanneer de gekozen header
#                   net wél alle kolommen van het ANDERE brontype bevat, een
#                   gerichte melding ("X lijkt een <ander>-bestand te zijn,
#                   maar is gekozen als <huidig>-bestand — wissel de 2
#                   bestandskeuzes om.") i.p.v. enkel de kale
#                   "ontbrekende kolommen"-lijst. Nieuwe constanten
#                   _OTHER_SOURCE_TYPE/_SOURCE_TYPE_LABEL; _validate_header()
#                   krijgt een nieuwe optionele parameter source_type (beide
#                   aanroepen, in load_csv() en load_xlsx(), geven die nu
#                   mee). Zelf getest met de 2 aangeleverde reële bestanden
#                   (OpenVKOorders_1.csv/OpenVKOleveringen_1.csv) — correct
#                   toegewezen verwerken ze foutloos tot 31 medewerkers
#                   (183 orders-/50 leveringenrijen).
# Changes: 1.2.0 — BUGFIX (bevestigd door gebruiker: "Ongeldige datum in
#                   kolom DocDate: 'Thierry Bourse'"): een reële SAP B1-
#                   Excel-export bleek na de eigenlijke tabel nog een
#                   niet-tabelrij te bevatten (vermoedelijk een voettekst-/
#                   notitieregel, bv. "Afgedrukt door: <naam>") die toevallig
#                   onder de kolom "DocDate" terechtkwam — load_xlsx() liet
#                   daardoor de volledige import falen op die ene randrij.
#                   Nieuwe helper _is_data_row(): een Excel-rij telt enkel
#                   als echte gegevensrij wanneer de ankerkolom (de eerste
#                   vereiste kolom, "DocNum" voor beide brontypes) een
#                   geldig, numeriek documentnummer bevat — andere rijen
#                   worden overgeslagen i.p.v. de hele import te laten
#                   crashen op een niet-interpreteerbare waarde in een
#                   willekeurige kolom. Aantal overgeslagen rijen wordt
#                   gelogd (nieuwe module-logger "ArticleSearch.OeOverview",
#                   zelfde patroon als prod_info.py). load_csv() blijft
#                   bewust ongewijzigd (strikte validatie) — dit type
#                   voettekst-rij is een Excel/print-exportfenomeen, niet
#                   waargenomen in de al langer geteste CSV-variant.
# Changes: 1.1.0 — Bronbestanden bleken in de praktijk .xlsx te zijn (niet
#                   .csv, de aanname uit het oorspronkelijke prototype) —
#                   nu kunnen beide: nieuwe load_xlsx() (openpyxl,
#                   read_only/data_only) naast de bestaande load_csv(), en
#                   een nieuwe dispatcher load_source_file() die op basis
#                   van de bestandsextensie de juiste kiest (voorkeurs-
#                   ingang voor ui_oeoverview.py). find_candidate_files()
#                   zoekt nu ook op .xlsx/.xls naast .csv
#                   (_SUPPORTED_EXTENSIONS). _to_int()/_to_float()/_to_date()
#                   zijn bron-onafhankelijk gemaakt (tolereren zowel
#                   CSV-strings als al-getypte Excel-celwaarden int/float/
#                   datetime) zodat _convert_row() door beide loaders
#                   herbruikt kan worden.
# Changes: 1.0.0 — Initiële opzet: overgezet uit het OpenElements2Csv-
#                   prototype. Business-regels ongewijzigd overgenomen
#                   (bevestigd, zie OpenElements2Csv_ArticleSearch_
#                   integratie.md): groeperen op SalesOwner met DocOwner-
#                   fallback, leeftijdsfilter orders <= -6 MaandenOud,
#                   leeftijdsfilter leveringen <= -1 MaandenOud, extra
#                   kolom "Openstaand" = DocTotal - PaidSum. De eigen
#                   CSV-parser (handmatige regel-/veldsplitsing i.p.v. de
#                   standaard csv-module) is bewust behouden: reële SAP-
#                   exports bevatten soms niet-geëscapte aanhalingstekens
#                   in het vrije-tekst Comments-veld, wat de RFC4180-quote-
#                   parsing laat ontsporen. Enige functionele aanpassing
#                   t.o.v. het prototype: `CsvLoadError` geeft nu een kant-
#                   en-klare Nederlandstalige boodschap terug (`.message`)
#                   i.p.v. een i18n-sleutel + parameters — ArticleSearch
#                   heeft geen i18n-laag, in tegenstelling tot het
#                   prototype (zie integratiedocument §6).
# =============================================================================

from __future__ import annotations

import csv
import logging
import re
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font
from openpyxl.worksheet.worksheet import Worksheet

logger = logging.getLogger("ArticleSearch.OeOverview")
if not logger.handlers:
    h = logging.StreamHandler()
    f = logging.Formatter("[%(levelname)s] %(asctime)s - [ArticleSearch.OeOverview] %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
logger.setLevel(logging.INFO)

# -----------------------------------------------------------------------
# Constanten — bronbestanden / kolommen
# -----------------------------------------------------------------------

SOURCE_TYPE_ORDERS = "orders"
SOURCE_TYPE_LEVERINGEN = "leveringen"

# Voor de "omgewisselde bestandskeuze"-hint in _validate_header().
_OTHER_SOURCE_TYPE: dict[str, str] = {
    SOURCE_TYPE_ORDERS: SOURCE_TYPE_LEVERINGEN,
    SOURCE_TYPE_LEVERINGEN: SOURCE_TYPE_ORDERS,
}
_SOURCE_TYPE_LABEL: dict[str, str] = {
    SOURCE_TYPE_ORDERS: "orders",
    SOURCE_TYPE_LEVERINGEN: "leveringen",
}

# Bestandsnaam-patroon per brontype (case-insensitive substring-match),
# bv. "OpenVKOorders.xlsx" / "OpenVKOleveringen.xlsx" (of .csv) — bewuste
# aanname i.p.v. detectie op kolomstructuur. Dit patroon bepaalt enkel
# welk bestand in de keuzelijst vooraf geselecteerd staat als "vermoedelijk
# de juiste" — het is nooit een harde vereiste: elk bestand kan ook altijd
# manueel gekozen worden via "Bladeren...", ongeacht naam of locatie (zie
# find_candidate_files()/1.2.0).
_FILENAME_PATTERNS: dict[str, str] = {
    SOURCE_TYPE_ORDERS: "orders",
    SOURCE_TYPE_LEVERINGEN: "leveringen",
}

# Ondersteunde bestandsextensies voor bronbestanden — de reële SAP B1-
# export bleek .xlsx te zijn (niet .csv, de aanname uit het oorspronkelijke
# OpenElements2Csv-prototype); .csv blijft ook ondersteund voor wie dat
# formaat wel exporteert. Bepaalt zowel welke bestanden find_candidate_files()
# oppikt als welke loader load_source_file() kiest (op basis van suffix).
_SUPPORTED_EXTENSIONS = (".xlsx", ".xls", ".csv")

# Verwachte kolomvolgorde per brontype.
REQUIRED_COLUMNS: dict[str, list[str]] = {
    SOURCE_TYPE_ORDERS: [
        "DocNum", "CardCode", "Partner", "VATNbr", "DocDate", "DocDueDate",
        "DocTotal", "PaidSum", "Comments", "OrderCount", "MaandenOud",
        "DocOwner", "SalesOwner", "DocEntry", "Project", "ProjectBased",
    ],
    SOURCE_TYPE_LEVERINGEN: [
        "DocNum", "CardCode", "Partner", "VATNbr", "DocDate", "DocDueDate",
        "DocTotal", "PaidSum", "Comments", "DeliveryCount", "MaandenOud",
        "DocOwner", "SalesOwner", "DocEntry",
    ],
}

_CSV_DELIMITER = ";"
_CSV_ENCODING = "utf-8-sig"  # UTF-8 met BOM
_ROW_SEPARATOR = "\r\n"  # betrouwbare rijscheiding in deze SAP-exports
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

_INT_COLUMNS = ("DocNum", "MaandenOud", "DocEntry", "OrderCount", "DeliveryCount", "ProjectBased")
_FLOAT_COLUMNS = ("DocTotal", "PaidSum")
_DATE_COLUMNS = ("DocDate", "DocDueDate")

# -----------------------------------------------------------------------
# Constanten — verwerkingsregels (bevestigd, zie integratiedocument §3)
# -----------------------------------------------------------------------

# Leeftijdsgrenzen (MaandenOud is een negatief getal: hoe kleiner, hoe
# ouder) — inclusief de grenswaarde zelf.
ORDERS_MAX_MAANDENOUD = -6
LEVERINGEN_MAX_MAANDENOUD = -1

# Waarden die aangeven dat SalesOwner niet bruikbaar is als groeperingsveld
# — dan wordt teruggevallen op DocOwner.
_LEGE_SALESOWNER_WAARDEN = {"", "-Geen verkoopmedewerker-"}

# -----------------------------------------------------------------------
# Constanten — export
# -----------------------------------------------------------------------

FORMAT_XLSX = "xlsx"
FORMAT_CSV = "csv"

SHEET_NAME_ORDERS = "VKOrders"
SHEET_NAME_LEVERINGEN = "VKLeveringen"

# Extra kolom (niet aanwezig in de brondata) met het openstaand saldo per
# rij en in de totaalrij.
_OPENSTAAND_KOLOM = "Openstaand"
_TOTAALRIJ_LABEL = "TOTAAL"

_INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|]')


# =========================================================================
# Fouten
# =========================================================================

class CsvLoadError(Exception):
    """Fout bij het zoeken naar of inlezen/valideren van een bron-CSV.

    ``message`` is een kant-en-klare Nederlandstalige boodschap, rechtstreeks
    te tonen in de GUI (geen i18n-laag in ArticleSearch, in tegenstelling
    tot het OpenElements2Csv-prototype).
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


# =========================================================================
# Kandidaat-bestanden zoeken
# =========================================================================

@dataclass(frozen=True)
class CandidateFile:
    """Eén kandidaat-bronbestand voor de bestandskeuzelijst in de GUI."""

    path: Path
    modified_at: datetime

    @property
    def display_name(self) -> str:
        return self.path.name


def find_candidate_files(input_folder: Path, source_type: str) -> list[CandidateFile]:
    """Zoek kandidaat-CSV's voor het gegeven brontype in ``input_folder``.

    Matcht op bestandsnaam-patroon (case-insensitive substring), zie
    ``_FILENAME_PATTERNS``. Resultaat is gesorteerd op bestandsdatum
    (mtime), nieuwste eerst — de GUI selecteert standaard het eerste
    element, de gebruiker kan zelf een ander bestand kiezen.

    Raises:
        CsvLoadError: als ``source_type`` onbekend is, of als de inputmap
            niet bestaat.
    """
    if source_type not in _FILENAME_PATTERNS:
        raise CsvLoadError(f"Onbekend brontype: {source_type}")

    if not input_folder.is_dir():
        raise CsvLoadError("Selecteer eerst een geldige inputmap.")

    pattern = _FILENAME_PATTERNS[source_type]
    candidates = [
        CandidateFile(path=p, modified_at=datetime.fromtimestamp(p.stat().st_mtime))
        for ext in _SUPPORTED_EXTENSIONS
        for p in input_folder.glob(f"*{ext}")
        if pattern in p.stem.lower()
    ]
    candidates.sort(key=lambda c: c.modified_at, reverse=True)
    return candidates


# =========================================================================
# CSV inlezen/valideren
# =========================================================================

def load_csv(file_path: Path, source_type: str) -> list[dict[str, Any]]:
    """Lees en valideer een orders- of leveringen-CSV.

    Elke rij wordt teruggegeven als dict met de originele kolomnamen als
    key; numerieke/datumkolommen worden geconverteerd naar hun Python-type.
    Overige kolommen (o.a. ``Comments``, die interne regelafbrekingen kan
    bevatten) blijven str.

    Rijen worden gesplitst op de letterlijke rijscheiding ``\\r\\n`` i.p.v.
    RFC4180-quote-parsing: robuuster tegen niet-geëscapte aanhalingstekens
    in het vrije-tekst Comments-veld van echte SAP-exports (bevestigde
    datakwaliteitsval, zie integratiedocument §2) — een standaard CSV-
    parser (Python's ``csv``-module) breekt hierop en corrumpeert
    daaropvolgende rijen.

    Raises:
        CsvLoadError: als ``source_type`` onbekend is, het bestand niet
            gevonden/leesbaar is, of de header/rijen niet overeenkomen met
            het verwachte aantal kolommen voor dat brontype.
    """
    if source_type not in REQUIRED_COLUMNS:
        raise CsvLoadError(f"Onbekend brontype: {source_type}")

    if not file_path.is_file():
        raise CsvLoadError(f"Kan bestand niet inlezen: {file_path.name} (bestand niet gevonden).")

    expected_columns = REQUIRED_COLUMNS[source_type]

    try:
        with file_path.open("r", encoding=_CSV_ENCODING, newline="") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError) as exc:
        raise CsvLoadError(f"Kan bestand niet inlezen: {file_path.name} ({exc}).") from exc

    records = content.split(_ROW_SEPARATOR)
    if records and records[-1] == "":
        records = records[:-1]
    if not records:
        raise CsvLoadError(f"Kan bestand niet inlezen: {file_path.name} (leeg bestand).")

    header = _split_fields(records[0])
    _validate_header(header, expected_columns, file_path, source_type)

    rows: list[dict[str, Any]] = []
    for line_no, record in enumerate(records[1:], start=2):
        fields = _split_fields(record)
        if len(fields) != len(header):
            raise CsvLoadError(
                f"Kan bestand niet inlezen: {file_path.name} "
                f"(rij {line_no}: {len(fields)} velden gevonden, {len(header)} verwacht)."
            )
        raw_row = dict(zip(header, fields))
        rows.append(_convert_row(raw_row))

    return rows


# =========================================================================
# Excel (.xlsx/.xls) inlezen/valideren
# =========================================================================

def _is_data_row(raw_row: dict, anchor_column: str) -> bool:
    """Bepaalt of een Excel-rij een echte gegevensrij is, op basis van de
    ankerkolom (typisch 'DocNum'): enkel als die een geldig, numeriek
    documentnummer bevat. Filtert voettekst-/notitieregels die soms na de
    eigenlijke tabel in een SAP B1-Excel-export blijven staan (bv.
    "Afgedrukt door: <naam>") — die hebben geen bruikbaar documentnummer en
    zouden anders de hele import laten falen op een niet-interpreteerbare
    waarde in een willekeurige andere kolom.
    """
    value = raw_row.get(anchor_column)
    if value is None:
        return False
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return False
    try:
        float(value)
    except (TypeError, ValueError):
        return False
    return True


def load_xlsx(file_path: Path, source_type: str) -> list[dict[str, Any]]:
    """Lees en valideer een orders- of leveringen-Excel-export (.xlsx/.xls).

    Verwacht de kolomnamen in de eerste rij van het eerste (actieve)
    tabblad — zelfde vereiste kolommen als bij de CSV-variant
    (REQUIRED_COLUMNS). Cijfer-/datumcellen komen via openpyxl al als
    Python int/float/datetime binnen (geen tekst-parsing nodig, zie
    _to_int()/_to_float()/_to_date()).

    Raises:
        CsvLoadError: als ``source_type`` onbekend is, het bestand niet
            gevonden/leesbaar is, of de header niet de verwachte kolommen
            bevat.
    """
    if source_type not in REQUIRED_COLUMNS:
        raise CsvLoadError(f"Onbekend brontype: {source_type}")

    if not file_path.is_file():
        raise CsvLoadError(f"Kan bestand niet inlezen: {file_path.name} (bestand niet gevonden).")

    expected_columns = REQUIRED_COLUMNS[source_type]

    try:
        wb = load_workbook(file_path, read_only=True, data_only=True)
    except Exception as exc:
        raise CsvLoadError(f"Kan bestand niet inlezen: {file_path.name} ({exc}).") from exc

    try:
        ws = wb.active
        rows_iter = ws.iter_rows(values_only=True)
        try:
            header_row = next(rows_iter)
        except StopIteration:
            raise CsvLoadError(f"Kan bestand niet inlezen: {file_path.name} (leeg bestand).")

        header = [str(h).strip() if h is not None else "" for h in header_row]
        _validate_header(header, expected_columns, file_path, source_type)

        # Ankerkolom om een echte gegevensrij te herkennen (zie 1.2.0) —
        # de eerste vereiste kolom, "DocNum" voor beide brontypes.
        anchor_column = expected_columns[0]

        rows: list[dict[str, Any]] = []
        skipped = 0
        for values in rows_iter:
            if values is None or all(v is None for v in values):
                continue  # lege rij overslaan (komt vaak voor onderaan een export)
            # openpyxl's rijlengte volgt de sheetbreedte (ws.max_column) en
            # kan daardoor in randgevallen net iets afwijken van de
            # headerlengte — aanvullen/afknotten i.p.v. hard te falen, in
            # tegenstelling tot de striktere CSV-validatie (waar een
            # lengteverschil wél op een echt datakwaliteitsprobleem wijst).
            if len(values) < len(header):
                values = values + (None,) * (len(header) - len(values))
            elif len(values) > len(header):
                values = values[:len(header)]
            raw_row = dict(zip(header, values))
            if not _is_data_row(raw_row, anchor_column):
                # Vermoedelijk een voettekst-/notitieregel na de eigenlijke
                # tabel (bv. "Afgedrukt door: <naam>") — geen bruikbaar
                # documentnummer, dus overslaan i.p.v. de hele import te
                # laten falen op een niet-interpreteerbare waarde in een
                # willekeurige andere kolom.
                skipped += 1
                continue
            rows.append(_convert_row(raw_row))

        if skipped:
            logger.info(
                f"{file_path.name}: {skipped} rij(en) overgeslagen zonder geldige "
                f"'{anchor_column}' (vermoedelijk voettekst/notitie na de tabel)."
            )

        return rows
    finally:
        wb.close()


# =========================================================================
# Dispatcher — kiest CSV- of Excel-loader op basis van de bestandsextensie
# =========================================================================

def load_source_file(file_path: Path, source_type: str) -> list[dict[str, Any]]:
    """Lees en valideer een orders- of leveringen-bronbestand — CSV of
    Excel (.xlsx/.xls), automatisch herkend aan de bestandsextensie van
    ``file_path``. Voorkeursfunctie voor de GUI (ui_oeoverview.py); de
    afzonderlijke load_csv()/load_xlsx() blijven ook rechtstreeks bruikbaar.
    """
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        return load_csv(file_path, source_type)
    if suffix in (".xlsx", ".xls"):
        return load_xlsx(file_path, source_type)
    raise CsvLoadError(
        f"Niet-ondersteund bestandstype: {file_path.name} "
        f"(enkel .xlsx, .xls of .csv worden ondersteund)."
    )


def _split_fields(record: str) -> list[str]:
    """Splits één logische regel in velden en werk quoting/interne regelafbrekingen bij.

    Een veld dat begint én eindigt met een dubbel aanhalingsteken wordt
    ontdaan van die omhullende quotes; verdubbelde aanhalingstekens (``""``)
    worden ontsnapt naar één letterlijk aanhalingsteken. Losse, interne
    ``\\r``-tekens (regelafbrekingen binnen bv. Comments) worden omgezet naar
    ``\\n``.
    """
    fields = record.split(_CSV_DELIMITER)
    cleaned = []
    for field in fields:
        if len(field) >= 2 and field.startswith('"') and field.endswith('"'):
            field = field[1:-1].replace('""', '"')
        cleaned.append(field.replace("\r", "\n"))
    return cleaned


def _validate_header(header: list[str], expected_columns: list[str], file_path: Path,
                      source_type: str | None = None) -> None:
    missing = [c for c in expected_columns if c not in header]
    if not missing:
        return

    # Slimme hint: bevat de header net wél alle kolommen van het ANDERE
    # brontype? Dan is dit vermoedelijk een omgewisselde bestandskeuze
    # (orders-bestand in het leveringen-vak, of omgekeerd) — een
    # veelvoorkomende vergissing met 2 bijna-identieke bestandsnamen naast
    # elkaar, zeker sinds "Bladeren..." elk bestand toelaat. Geef dan een
    # gerichte melding i.p.v. een kale kolommenlijst.
    other_type = _OTHER_SOURCE_TYPE.get(source_type) if source_type else None
    if other_type:
        other_columns = REQUIRED_COLUMNS[other_type]
        if all(c in header for c in other_columns):
            huidig = _SOURCE_TYPE_LABEL.get(source_type, source_type)
            ander = _SOURCE_TYPE_LABEL.get(other_type, other_type)
            raise CsvLoadError(
                f"'{file_path.name}' lijkt een {ander}-bestand te zijn, maar is "
                f"gekozen als {huidig}-bestand — wissel de 2 bestandskeuzes om."
            )

    raise CsvLoadError(
        f"Kan bestand niet inlezen: {file_path.name} "
        f"(ontbrekende kolommen: {', '.join(missing)})."
    )


def _convert_row(row: dict[str, str | None]) -> dict[str, Any]:
    converted: dict[str, Any] = dict(row)

    for col in _INT_COLUMNS:
        if col in converted:
            converted[col] = _to_int(converted[col])

    for col in _FLOAT_COLUMNS:
        if col in converted:
            converted[col] = _to_float(converted[col])

    for col in _DATE_COLUMNS:
        if col in converted:
            converted[col] = _to_date(converted[col], col)

    return converted


def _to_int(value) -> int | None:
    """Bron-onafhankelijk: ``value`` kan een CSV-string zijn óf een al
    getypte Excel-celwaarde (int/float)."""
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    try:
        return int(float(value))  # float() vangt evt. "1.0"-achtige waarden op
    except (TypeError, ValueError):
        return None


def _to_float(value) -> float | None:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_date(value, column: str) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        # Excel geeft een datumcel al als datetime terug (openpyxl,
        # data_only=True) — niets meer te parsen.
        return value
    if isinstance(value, str):
        value = value.strip()
        if value == "":
            return None
        for fmt in (_DATE_FORMAT, "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        raise CsvLoadError(f"Ongeldige datum in kolom {column}: {value!r}.")
    # Onverwacht type (bv. een datum die als kaal getal/serienummer
    # binnenkomt, niet als datumcel geformatteerd) — niet betrouwbaar te
    # onderscheiden van een gewoon getal, dus ongewijzigd doorgeven i.p.v.
    # te gokken.
    return value


# =========================================================================
# Verwerking — filteren, groeperen, totalen
# =========================================================================

@dataclass(frozen=True)
class Totals:
    """Som-totalen voor een set rijen (totaalrij per tab)."""

    total_doctotal: float
    total_paidsum: float
    total_openstaand: float


@dataclass
class EmployeeData:
    """Gefilterde orders- en leveringenrijen + totalen voor één medewerker."""

    employee_name: str
    orders: list[dict[str, Any]] = field(default_factory=list)
    orders_totals: Totals = field(default_factory=lambda: Totals(0.0, 0.0, 0.0))
    leveringen: list[dict[str, Any]] = field(default_factory=list)
    leveringen_totals: Totals = field(default_factory=lambda: Totals(0.0, 0.0, 0.0))


def determine_employee(row: dict[str, Any]) -> str | None:
    """Bepaal de medewerker om op te groeperen voor één rij.

    Gebruikt ``SalesOwner``, met fallback naar ``DocOwner`` wanneer
    ``SalesOwner`` leeg is of gelijk aan ``-Geen verkoopmedewerker-``.
    Geeft ``None`` terug als ook ``DocOwner`` ontbreekt.
    """
    sales_owner = (row.get("SalesOwner") or "").strip()
    if sales_owner not in _LEGE_SALESOWNER_WAARDEN:
        return sales_owner

    doc_owner = (row.get("DocOwner") or "").strip()
    return doc_owner or None


def filter_orders(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter openstaande orders ouder dan (of gelijk aan) 6 maanden."""
    return [r for r in rows if _is_old_enough(r, ORDERS_MAX_MAANDENOUD)]


def filter_leveringen(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Filter openstaande leveringen ouder dan (of gelijk aan) 1 maand."""
    return [r for r in rows if _is_old_enough(r, LEVERINGEN_MAX_MAANDENOUD)]


def _is_old_enough(row: dict[str, Any], max_maandenoud: int) -> bool:
    maandenoud = row.get("MaandenOud")
    if maandenoud is None:
        return False  # leeftijd onbekend -> niet meetellen (veilige default)
    return maandenoud <= max_maandenoud


def group_by_employee(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Groepeer rijen per medewerker (zie ``determine_employee``).

    Rijen zonder bruikbare medewerker (geen ``SalesOwner`` én geen
    ``DocOwner``) worden overgeslagen.
    """
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        employee = determine_employee(row)
        if employee is None:
            continue
        grouped.setdefault(employee, []).append(row)
    return grouped


def compute_totals(rows: list[dict[str, Any]]) -> Totals:
    """Bereken de totaalrij voor een set rijen: totaal DocTotal, totaal
    PaidSum en totaal openstaand saldo (DocTotal - PaidSum, per rij
    berekend en dan gesommeerd)."""
    total_doctotal = 0.0
    total_paidsum = 0.0
    total_openstaand = 0.0
    for row in rows:
        doctotal = row.get("DocTotal") or 0.0
        paidsum = row.get("PaidSum") or 0.0
        total_doctotal += doctotal
        total_paidsum += paidsum
        total_openstaand += doctotal - paidsum
    return Totals(
        total_doctotal=total_doctotal,
        total_paidsum=total_paidsum,
        total_openstaand=total_openstaand,
    )


def process(
    orders_rows: list[dict[str, Any]], leveringen_rows: list[dict[str, Any]]
) -> dict[str, EmployeeData]:
    """Volledige verwerking: filteren, groeperen per medewerker en totalen
    berekenen voor beide brontypes.

    Geeft een dict terug van medewerkernaam -> :class:`EmployeeData`, met
    per medewerker enkel een gevulde ``orders``- of ``leveringen``-lijst als
    er na filtering rijen voor die medewerker overblijven (de andere lijst
    is dan leeg met totalen op 0).
    """
    filtered_orders = filter_orders(orders_rows)
    filtered_leveringen = filter_leveringen(leveringen_rows)

    orders_by_employee = group_by_employee(filtered_orders)
    leveringen_by_employee = group_by_employee(filtered_leveringen)

    employee_names = set(orders_by_employee) | set(leveringen_by_employee)

    result: dict[str, EmployeeData] = {}
    for name in sorted(employee_names):
        orders = orders_by_employee.get(name, [])
        leveringen = leveringen_by_employee.get(name, [])
        result[name] = EmployeeData(
            employee_name=name,
            orders=orders,
            orders_totals=compute_totals(orders),
            leveringen=leveringen,
            leveringen_totals=compute_totals(leveringen),
        )

    return result


# =========================================================================
# Export — xlsx / csv per medewerker
# =========================================================================

def sanitize_filename(name: str) -> str:
    """Maak een medewerkernaam veilig voor gebruik als (deel van een) bestandsnaam."""
    cleaned = _INVALID_FILENAME_CHARS.sub("_", name)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or "Onbekend"


def _columns_for(source_type: str) -> list[str]:
    return [*REQUIRED_COLUMNS[source_type], _OPENSTAAND_KOLOM]


def _row_values(row: dict, columns: list[str]) -> list:
    values = []
    for col in columns:
        if col == _OPENSTAAND_KOLOM:
            values.append((row.get("DocTotal") or 0.0) - (row.get("PaidSum") or 0.0))
        else:
            values.append(row.get(col))
    return values


def _totals_row(columns: list[str], totals: Totals) -> list:
    row = [None] * len(columns)
    row[0] = _TOTAALRIJ_LABEL
    if "DocTotal" in columns:
        row[columns.index("DocTotal")] = totals.total_doctotal
    if "PaidSum" in columns:
        row[columns.index("PaidSum")] = totals.total_paidsum
    row[columns.index(_OPENSTAAND_KOLOM)] = totals.total_openstaand
    return row


def _write_xlsx_sheet(
    ws: Worksheet, source_type: str, rows: list[dict], totals: Totals
) -> None:
    columns = _columns_for(source_type)
    ws.append(columns)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    ws.freeze_panes = "A2"

    for row in rows:
        ws.append(_row_values(row, columns))

    ws.append(_totals_row(columns, totals))
    for cell in ws[ws.max_row]:
        cell.font = Font(bold=True)


def _write_xlsx(employee: EmployeeData, path: Path) -> None:
    wb = Workbook()
    ws_orders = wb.active
    ws_orders.title = SHEET_NAME_ORDERS
    _write_xlsx_sheet(ws_orders, SOURCE_TYPE_ORDERS, employee.orders, employee.orders_totals)

    ws_leveringen = wb.create_sheet(SHEET_NAME_LEVERINGEN)
    _write_xlsx_sheet(
        ws_leveringen, SOURCE_TYPE_LEVERINGEN, employee.leveringen, employee.leveringen_totals
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    wb.save(path)


def _format_csv_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime(_DATE_FORMAT)[:-3]  # milliseconden i.p.v. microseconden
    return str(value)


def _write_csv(
    source_type: str, rows: list[dict], totals: Totals, path: Path
) -> None:
    columns = _columns_for(source_type)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding=_CSV_ENCODING, newline="") as f:
        writer = csv.writer(f, delimiter=_CSV_DELIMITER)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(_format_csv_value(v) for v in _row_values(row, columns))
        writer.writerow(_format_csv_value(v) for v in _totals_row(columns, totals))


def write_employee_output(
    employee: EmployeeData, output_folder: Path, formats: set[str], epoch: int
) -> list[Path]:
    """Schrijf de output voor één medewerker weg in de gevraagde formaten.

    Bestandsnaam krijgt een epoch-timestamp-suffix (gedeeld over de hele
    run) zodat bestaande output nooit overschreven wordt.
    """
    safe_name = sanitize_filename(employee.employee_name)
    written: list[Path] = []

    if FORMAT_XLSX in formats:
        xlsx_path = output_folder / f"{safe_name}_{epoch}.xlsx"
        _write_xlsx(employee, xlsx_path)
        written.append(xlsx_path)

    if FORMAT_CSV in formats:
        orders_path = output_folder / f"{safe_name}_VKOrders_{epoch}.csv"
        _write_csv(SOURCE_TYPE_ORDERS, employee.orders, employee.orders_totals, orders_path)
        written.append(orders_path)

        leveringen_path = output_folder / f"{safe_name}_VKLeveringen_{epoch}.csv"
        _write_csv(
            SOURCE_TYPE_LEVERINGEN, employee.leveringen, employee.leveringen_totals, leveringen_path
        )
        written.append(leveringen_path)

    return written


def export_all(
    results: dict[str, EmployeeData], output_folder: Path, formats: set[str]
) -> list[Path]:
    """Schrijf de output voor alle medewerkers weg, met één gedeelde
    epoch-timestamp voor deze volledige run."""
    epoch = int(time.time())
    written: list[Path] = []
    for employee in results.values():
        written.extend(write_employee_output(employee, output_folder, formats, epoch))
    return written