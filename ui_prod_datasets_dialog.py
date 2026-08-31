# =============================================================================
# ArticleSearch
# File:    ui_prod_datasets_dialog.py
# Role:    Beheerscherm voor Prod Stock Overview-datasets — lijst opvragen,
#          nieuw aanmaken, bestaande bewerken. Gebruikt prod_info.py
#          (client "Datasetprod"). Opgeroepen vanuit settings_dialog.py
#          ("Datasets beheren...")-knop.
#          Geen "verwijderen": de API biedt enkel een upsert-endpoint (CODE);
#          een dataset "deactiveren" gebeurt via de Lock-checkbox (DS_Lock),
#          waardoor hij niet meer verschijnt in de dataset-keuzelijst in
#          ui_main.py (search-type "Prod"). ⚠️ Aanname, nog te bevestigen.
# Version: 1.2.0
# Author:  Bart Bossuyt
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
import os
import logging

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QMessageBox, QLineEdit, QTextEdit, QCheckBox,
    QApplication
)

from prod_info import list_datasets, save_dataset, next_dataset_code, parse_artnbr, normalize_pasted_items

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

    def __init__(self, dataset, existing_datasets: list, parent=None):
        super().__init__(parent)
        self.existing_datasets = existing_datasets or []
        self.dataset = dataset or {}
        is_new = dataset is None

        self.setWindowTitle("Nieuwe dataset" if is_new else f"Dataset bewerken — {self.dataset.get('DS_Name', '')}")
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
        self.owner_input = QLineEdit(self.dataset.get("DS_Owner", ""))
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
        # normalize_pasted_items() is delimiter-agnostic, dus zelfs zonder
        # de "Normaliseren"-knop expliciet te gebruiken wordt hier alsnog
        # correct genormaliseerd (spaties/tabs/regeleindes/puntkomma's).
        items = parse_artnbr(normalize_pasted_items(self.artnbr_input.toPlainText()))

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
        dialog = ProdDatasetEditDialog(ds, self._datasets, parent=self)
        if dialog.exec():
            self.load_datasets()