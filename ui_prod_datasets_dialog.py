# =============================================================================
# ArticleSearch
# File:    ui_prod_datasets_dialog.py
# Role:    Beheerscherm voor Prod Stock Overview-datasets — lijst opvragen,
#          nieuw aanmaken, bestaande bekijken/bewerken. Bewerken is enkel
#          toegestaan voor de (bij benadering) eigenaar van de dataset, of
#          voor leden van de AD-groep "CGK-APP-L6" (volledige beheer-
#          rechten, zie 1.5.0); bekijken (alleen-lezen) blijft voor
#          iedereen mogelijk (zie 1.4.0). Gebruikt prod_info.py (client
#          "Datasetprod"). Opgeroepen vanuit settings_dialog.py
#          ("Datasets beheren...")-knop.
#          Geen "verwijderen": de API biedt enkel een upsert-endpoint (CODE);
#          een dataset "deactiveren" gebeurt via de Lock-checkbox (DS_Lock),
#          waardoor hij niet meer verschijnt in de dataset-keuzelijst in
#          ui_main.py (search-type "Prod"). ⚠️ Aanname, nog te bevestigen.
# Version: 1.5.0
# Author:  Bart Bossuyt
# Changes: 1.5.0 — Beheerdersoverride: leden van de Azure AD-groep
#                   "CGK-APP-L6" (_ADMIN_GROUP) kunnen voortaan élke
#                   dataset volledig bewerken, ongeacht eigenaar — de
#                   eigenaar-matchcontrole (_owner_match_level) wordt voor
#                   hen overschreven naar een nieuw niveau 'admin' in
#                   ProdDatasetsDialog._edit_selected() (groepscontrole via
#                   permissions_azure.user_in_azure_group(), fail-safe: een
#                   falende controle levert stilzwijgend geen beheerrechten
#                   op, blokkeert bekijken/de normale flow niet). Nieuwe
#                   parameter is_admin op ProdDatasetEditDialog.__init__():
#                   Eigenaar-veld blijft in die modus bewerkbaar maar toont
#                   de bestaande waarde ongewijzigd (geen automatische
#                   overschrijving met de beheerder's eigen naam, in
#                   tegenstelling tot de 'approx'-modus uit 1.4.0) —
#                   venstertitel krijgt de toevoeging "(beheerdersmodus)".
# Changes: 1.4.0 — Verfijning op 1.3.0's eigenaarschap-controle, na
#                   terugkoppeling: (1) een dataset zonder bewerkrechten kan
#                   nu altijd nog BEKEKEN worden — i.p.v. de bewerk-dialoog
#                   te weigeren met een melding, opent
#                   ProdDatasetsDialog._edit_selected() ze voortaan altijd,
#                   in de gepaste modus. (2) Nieuwe helper
#                   _owner_match_level() vergelijkt DS_Owner niet langer
#                   enkel exact met de AD-displaynaam, maar herkent ook een
#                   'approx'-match (substring in beide richtingen, of een
#                   difflib-gelijkenis >= 0.6) — nodig omdat bestaande
#                   datasets hun eigenaar vóór 1.3.0 vrij ingetypt kregen
#                   (afgekort, andere volgorde, kleine tikfout, ...) en
#                   anders door niemand meer bewerkt zouden kunnen worden.
#                   ProdDatasetEditDialog kent nu 3 modi i.p.v. 2: 'exact'
#                   -> volledig bewerkbaar (Eigenaar blijft read-only,
#                   ongewijzigd), 'approx' -> volledig bewerkbaar mét een
#                   terug bewerkbaar Eigenaar-veld, voorgesteld met de
#                   exacte AD-naam zodat 1 klik op "Opslaan" de legacy-
#                   waarde corrigeert, 'none' -> volledig alleen-lezen
#                   (readonly=True: alle velden non-editable, "Opslaan"
#                   verborgen, "Annuleren" wordt "Sluiten"). Nieuwe
#                   parameters readonly/owner_editable op
#                   ProdDatasetEditDialog.__init__().
# Changes: 1.3.0 — Eigenaarschap gekoppeld aan de echte, ingelogde AD-
#                   identiteit i.p.v. een vrij ingetypt veld:
#                   (1) Bij een NIEUWE dataset wordt "Eigenaar" automatisch
#                   ingevuld met permissions_azure.get_current_user_display_name()
#                   (fallback: Windows-gebruikersnaam indien geen AD-naam
#                   gecached is) en is het veld voortaan read-only — zelfde
#                   principe als het bestaande "Gewijzigd door"-veld.
#                   (2) BEWERKEN is voortaan enkel toegestaan wanneer de
#                   ingelogde gebruiker exact overeenkomt met DS_Owner van
#                   de geselecteerde dataset (ProdDatasetsDialog._edit_selected(),
#                   case-insensitieve vergelijking) — anders een duidelijke
#                   "Geen toegang"-melding i.p.v. de bewerk-dialoog te
#                   openen. Geldt zowel bij "Bewerken..." als bij dubbel-
#                   klik. ⚠️ Aanname/open punt: bestaande datasets zonder
#                   DS_Owner (leeg) of met een owner-waarde die niet exact
#                   (case-insensitief) overeenkomt met de AD-displayname
#                   kunnen hierdoor door niemand meer bewerkt worden via de
#                   UI — nog te bevestigen of dat gewenst is, of dat er een
#                   uitzondering/beheerdersoverride nodig is.
#                   (3) _on_save() normaliseert het artikelnummers-veld nu
#                   altijd expliciet (_normalize_artnbr_field(), zichtbaar
#                   bijgewerkt in het veld zelf) vóór save_dataset()
#                   aangeroepen wordt — voorheen gebeurde de normalisatie
#                   enkel "onzichtbaar" inline bij het uitlezen van de
#                   veldinhoud, het getoonde veld zelf bleef ongewijzigd tot
#                   de gebruiker manueel op "Normaliseren" klikte.
# Changes: 1.2.0 — "Gewijzigd door"-veld (ProdDatasetEditDialog) is nu
#                   read-only: toont altijd de huidige Windows-gebruiker
#                   (degene die de opslag-actie uitvoert) i.p.v. manueel
#                   aanpasbaar of de vorige DS_ChangeBy-waarde over te
#                   nemen bij bewerken.
# Changes: 1.1.0 — Artikelnummers-veld (ProdDatasetEditDialog) normaliseert
#                   nu een geplakte lijst automatisch: nieuwe interne class
#                   "_ArtNbrTextEdit" (QTextEdit-subklasse, override
#                   insertFromMimeData) zet elk scheidingsteken (spatie,
#                   tab, puntkomma, regeleinde, of een mix) om naar komma en
#                   verwijdert alle witruimte/enters — het geplakte
#                   resultaat is telkens één lange, komma-gescheiden string
#                   (prod_info.normalize_pasted_items()). Extra knop
#                   "Normaliseren" laat toe om ook reeds getypte/geladen
#                   inhoud (bv. bij het bewerken van een bestaande dataset)
#                   alsnog manueel op te schonen. Initiële weergave van
#                   bestaande artikelnummers (bij bewerken) toont nu ook
#                   direct de genormaliseerde, komma-gescheiden vorm
#                   i.p.v. één artikel per regel — consistent met het
#                   nieuwe plak-gedrag.
# Changes: 1.0.0 — Initiële versie.
# =============================================================================
import difflib
import os
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit, QTextEdit, QCheckBox,
    QApplication
)

from prod_info import list_datasets, save_dataset, next_dataset_code, parse_artnbr, normalize_pasted_items
from permissions_azure import get_current_user_display_name, user_in_azure_group

# AD-groep met volledige beheerrechten over alle datasets, ongeacht
# eigenaar — overschrijft de eigenaar-matchcontrole volledig (zie 1.5.0).
_ADMIN_GROUP = "CGK-APP-L6"

logger = logging.getLogger("ArticleSearch.ProdDatasetsUI")
if not logger.handlers:
    h = logging.StreamHandler()
    f = logging.Formatter("[%(levelname)s] %(asctime)s - [ArticleSearch.ProdDatasetsUI] %(message)s")
    h.setFormatter(f)
    logger.addHandler(h)
logger.setLevel(logging.INFO)


def _current_username() -> str:
    """Windows-gebruikersnaam als standaard 'gewijzigd door' (geen aparte
    AD-displayname-lookup nodig — veld blijft door de gebruiker aanpasbaar)."""
    return os.environ.get("USERNAME") or os.environ.get("USER") or "Onbekend"


def _owner_match_level(owner: str, current_user: str) -> str:
    """Vergelijkt de (mogelijk ooit handmatig ingevulde) DS_Owner-waarde met
    de ingelogde AD-displaynaam. Retourneert 'exact', 'approx' of 'none'.

    'approx' dekt de bestaande datasets waarvan de eigenaar vóór 1.3.0
    vrij ingetypt werd (afgekort, andere volgorde, kleine tikfout, ...) —
    die zouden bij een exacte vergelijking door niemand meer bewerkt
    kunnen worden. Bij 'approx' blijft het scherm bewerkbaar en wordt het
    Eigenaar-veld voorgesteld met de exacte AD-naam, zodat de effectieve
    eigenaar de legacy-waarde in 1 klik kan corrigeren. Bij 'none' wordt
    het scherm enkel getoond in alleen-lezen modus — bekijken blijft altijd
    mogelijk, ook zonder bewerkrechten.
    """
    o = (owner or "").strip().lower()
    u = (current_user or "").strip().lower()
    if not o or not u:
        return "none"
    if o == u:
        return "exact"
    if o in u or u in o:
        return "approx"
    if difflib.SequenceMatcher(None, o, u).ratio() >= 0.6:
        return "approx"
    return "none"


class _ArtNbrTextEdit(QTextEdit):
    """
    QTextEdit die geplakte tekst automatisch normaliseert: ongeacht het
    originele scheidingsteken (spatie, tab, puntkomma, regeleinde, of een
    mix) wordt het geplakte resultaat altijd één lange, komma-gescheiden
    string zonder witruimte/enters (prod_info.normalize_pasted_items()).
    """

    def insertFromMimeData(self, source):
        if source.hasText():
            normalized = normalize_pasted_items(source.text())
            self.insertPlainText(normalized)
        else:
            super().insertFromMimeData(source)


class ProdDatasetEditDialog(QDialog):
    """Sub-dialoog: één dataset aanmaken of bewerken."""

    def __init__(self, dataset, existing_datasets: list, parent=None,
                 readonly: bool = False, owner_editable: bool = False, is_admin: bool = False):
        super().__init__(parent)
        self.existing_datasets = existing_datasets or []
        self.dataset = dataset or {}
        is_new = dataset is None
        # readonly is enkel relevant bij het bekijken van een bestaande
        # dataset waarvan de ingelogde gebruiker (ook niet bij benadering,
        # en geen CGK-APP-L6-lid) geen eigenaar is — een nieuwe dataset is
        # per definitie altijd volledig bewerkbaar door wie ze aanmaakt.
        self.readonly = readonly and not is_new

        if self.readonly:
            title = f"Dataset bekijken (alleen-lezen) — {self.dataset.get('DS_Name', '')}"
        elif is_new:
            title = "Nieuwe dataset"
        elif is_admin:
            title = f"Dataset bewerken (beheerdersmodus) — {self.dataset.get('DS_Name', '')}"
        else:
            title = f"Dataset bewerken — {self.dataset.get('DS_Name', '')}"
        self.setWindowTitle(title)
        self.resize(540, 520)

        layout = QVBoxLayout(self)

        if is_new:
            self.code = str(next_dataset_code(self.existing_datasets))
        else:
            self.code = str(self.dataset.get("DS_Code", ""))

        code_label = QLabel(f"Code: <b>{self.code}</b>" + ("  (nieuw, automatisch bepaald)" if is_new else ""))
        layout.addWidget(code_label)

        layout.addWidget(QLabel("Naam:"))
        self.name_input = QLineEdit(self.dataset.get("DS_Name", ""))
        layout.addWidget(self.name_input)

        layout.addWidget(QLabel("Eigenaar:"))
        if is_new:
            # Eigenaar wordt automatisch bepaald bij aanmaken — niet manueel
            # instelbaar, zodat de bewerk-rechten-check (enkel de eigenaar
            # zelf mag bewerken) altijd op een betrouwbare, echte identiteit
            # steunt i.p.v. een vrij ingetypte naam.
            eigenaar_default = get_current_user_display_name() or _current_username()
            owner_readonly = True
        elif is_admin:
            # CGK-APP-L6: volledige beheerrechten, ongeacht eigenaar. Veld
            # blijft bewerkbaar (bv. om eigenaarschap correct toe te wijzen)
            # maar toont de bestaande waarde ongewijzigd — geen automatische
            # overschrijving met de beheerder's eigen naam.
            eigenaar_default = self.dataset.get("DS_Owner", "")
            owner_readonly = False
        elif owner_editable:
            # 'approx'-match (zie _owner_match_level): waarschijnlijk de
            # eigenaar, maar de opgeslagen naam komt niet exact overeen met
            # de AD-displaynaam (legacy, handmatig ingevuld vóór 1.3.0).
            # Veld blijft bewerkbaar en wordt meteen voorgesteld met de
            # exacte AD-naam, zodat 1 klik op "Opslaan" de legacy-waarde
            # corrigeert.
            eigenaar_default = get_current_user_display_name() or self.dataset.get("DS_Owner", "")
            owner_readonly = False
        else:
            eigenaar_default = self.dataset.get("DS_Owner", "")
            owner_readonly = True
        self.owner_input = QLineEdit(eigenaar_default)
        self.owner_input.setReadOnly(owner_readonly)
        layout.addWidget(self.owner_input)

        layout.addWidget(QLabel(
            "Artikelnummers — plak een lijst (spatie/tab/puntkomma/regeleinde-"
            "gescheiden, of een mix); wordt automatisch omgezet naar één "
            "lange, komma-gescheiden lijst:"
        ))
        self.artnbr_input = _ArtNbrTextEdit()
        existing_items = parse_artnbr(self.dataset.get("DS_ArtNbr", ""))
        self.artnbr_input.setPlainText(",".join(existing_items))
        layout.addWidget(self.artnbr_input)

        normalize_row = QHBoxLayout()
        normalize_row.addStretch()
        self.normalize_button = QPushButton("Normaliseren")
        self.normalize_button.setToolTip(
            "Zet de huidige inhoud van het artikelnummers-veld om naar één "
            "lange, komma-gescheiden string (verwijdert witruimte/enters, "
            "andere scheidingstekens -> komma)."
        )
        self.normalize_button.clicked.connect(self._normalize_artnbr_field)
        normalize_row.addWidget(self.normalize_button)
        layout.addLayout(normalize_row)

        self.lock_checkbox = QCheckBox("Gedeactiveerd (niet tonen in de dataset-keuzelijst)")
        self.lock_checkbox.setChecked(str(self.dataset.get("DS_Lock") or "0") in ("1", "true", "True"))
        layout.addWidget(self.lock_checkbox)

        layout.addWidget(QLabel("Gewijzigd door:"))
        # Read-only: toont altijd de huidige Windows-gebruiker (degene die
        # deze opslag-actie uitvoert), niet manueel aanpasbaar.
        self.changeby_input = QLineEdit(_current_username())
        self.changeby_input.setReadOnly(True)
        layout.addWidget(self.changeby_input)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.save_button = QPushButton("Opslaan")
        self.cancel_button = QPushButton("Annuleren")
        btn_row.addWidget(self.save_button)
        btn_row.addWidget(self.cancel_button)
        layout.addLayout(btn_row)

        self.save_button.clicked.connect(self._on_save)
        self.cancel_button.clicked.connect(self.reject)

        if self.readonly:
            # Bekijken blijft altijd mogelijk, ook zonder (bij benadering)
            # eigenaarschap — enkel effectief wijzigen wordt hier
            # tegengehouden: alle velden op niet-bewerkbaar, "Opslaan"
            # verborgen, "Annuleren" wordt de facto een sluitknop.
            self.name_input.setReadOnly(True)
            self.artnbr_input.setReadOnly(True)
            self.normalize_button.setEnabled(False)
            self.lock_checkbox.setEnabled(False)
            self.save_button.setVisible(False)
            self.cancel_button.setText("Sluiten")

    def _normalize_artnbr_field(self):
        """Schoont de huidige veldinhoud manueel op (bv. na typen of het
        laden van een bestaande dataset met een ander scheidingsteken)."""
        current = self.artnbr_input.toPlainText()
        normalized = normalize_pasted_items(current)
        self.artnbr_input.setPlainText(normalized)

    def _on_save(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Naam ontbreekt", "Geef de dataset een naam.")
            return

        owner = self.owner_input.text().strip()
        # Altijd eerst normaliseren (zichtbaar bijgewerkt in het veld zelf)
        # en pas dan de genormaliseerde inhoud gebruiken om op te slaan —
        # ongeacht of de gebruiker zelf al op "Normaliseren" geklikt heeft.
        self._normalize_artnbr_field()
        items = parse_artnbr(self.artnbr_input.toPlainText())

        if not items:
            reply = QMessageBox.question(
                self, "Geen artikelen",
                "Deze dataset bevat geen artikelnummers. Toch opslaan?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        self.save_button.setEnabled(False)
        QApplication.processEvents()
        try:
            save_dataset(
                code=self.code,
                name=name,
                artnbr_list=items,
                changeby=self.changeby_input.text().strip() or _current_username(),
                owner=owner,
                lock="1" if self.lock_checkbox.isChecked() else "0",
            )
        except Exception as e:
            logger.error(f"Fout bij opslaan dataset: {e}")
            QMessageBox.critical(self, "Fout bij opslaan", str(e))
            self.save_button.setEnabled(True)
            return

        QMessageBox.information(self, "Opgeslagen", f"Dataset '{name}' is opgeslagen.")
        self.accept()


class ProdDatasetsDialog(QDialog):
    """Overzicht van alle Prod Stock Overview-datasets, met Nieuw/Bewerken."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Productie-datasets beheren")
        self.resize(720, 460)
        self._datasets = []

        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self.refresh_button = QPushButton("Ophalen")
        self.new_button = QPushButton("Nieuw...")
        self.edit_button = QPushButton("Bewerken...")
        btn_row.addWidget(self.refresh_button)
        btn_row.addWidget(self.new_button)
        btn_row.addWidget(self.edit_button)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Code", "Naam", "Eigenaar", "Aantal artikelen", "Status"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.itemDoubleClicked.connect(lambda _item: self._edit_selected())
        layout.addWidget(self.table)

        close_row = QHBoxLayout()
        close_row.addStretch()
        self.close_button = QPushButton("Sluiten")
        close_row.addWidget(self.close_button)
        layout.addLayout(close_row)

        self.status_label = QLabel("Klik op 'Ophalen' om de datasets te laden.")
        layout.addWidget(self.status_label)

        self.refresh_button.clicked.connect(self.load_datasets)
        self.new_button.clicked.connect(self._create_new)
        self.edit_button.clicked.connect(self._edit_selected)
        self.close_button.clicked.connect(self.accept)

    def load_datasets(self):
        self.refresh_button.setEnabled(False)
        self.status_label.setText("Bezig met ophalen…")
        QApplication.processEvents()
        try:
            self._datasets = list_datasets()
        except Exception as e:
            logger.error(f"Kon datasets niet ophalen: {e}")
            QMessageBox.critical(self, "Fout", f"Kon datasets niet ophalen:\n{e}")
            self._datasets = []
        finally:
            self.refresh_button.setEnabled(True)
        self._populate_table()

    def _populate_table(self):
        self.table.setRowCount(len(self._datasets))
        for row, ds in enumerate(self._datasets):
            items = parse_artnbr(ds.get("DS_ArtNbr", ""))
            locked = str(ds.get("DS_Lock") or "0") in ("1", "true", "True")
            values = [
                str(ds.get("DS_Code", "")),
                ds.get("DS_Name", "") or "",
                ds.get("DS_Owner", "") or "",
                str(len(items)),
                "🔒 Gedeactiveerd" if locked else "✅ Actief",
            ]
            for col, val in enumerate(values):
                self.table.setItem(row, col, QTableWidgetItem(val))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)
        self.status_label.setText(f"Aantal datasets: {len(self._datasets)}")

    def _selected_dataset(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._datasets):
            return None
        return self._datasets[row]

    def _create_new(self):
        dialog = ProdDatasetEditDialog(None, self._datasets, parent=self)
        if dialog.exec():
            self.load_datasets()

    def _edit_selected(self):
        ds = self._selected_dataset()
        if not ds:
            QMessageBox.information(self, "Geen selectie", "Selecteer eerst een dataset in de lijst.")
            return

        owner = (ds.get("DS_Owner") or "").strip()
        current_user = (get_current_user_display_name() or "").strip()

        is_admin = False
        try:
            is_admin = user_in_azure_group(_ADMIN_GROUP)
        except Exception as e:
            # Fail-safe: een falende groepscontrole mag bekijken/de normale
            # eigenaar-flow niet blokkeren — enkel het beheerdersvoordeel
            # vervalt dan stilzwijgend.
            logger.error(f"Kon AD-groepslidmaatschap ({_ADMIN_GROUP}) niet controleren: {e}")

        match_level = "admin" if is_admin else _owner_match_level(owner, current_user)

        # Bekijken is altijd toegestaan — enkel de bewerkbaarheid hangt af
        # van de eigenaar-match: 'admin' (CGK-APP-L6) of 'exact' -> volledig
        # bewerkbaar, 'approx' -> bewerkbaar + Eigenaar corrigeerbaar,
        # 'none' -> alleen-lezen.
        dialog = ProdDatasetEditDialog(
            ds, self._datasets, parent=self,
            readonly=(match_level == "none"),
            owner_editable=(match_level in ("approx", "admin")),
            is_admin=is_admin,
        )
        if dialog.exec():
            self.load_datasets()