# =============================================================================
# ArticleSearch
# File:    ui_oeoverview.py
# Role:    "Open Elements overview" — venster (Export-menu, Finance-only):
#          laat de gebruiker 2 lokale CSV-exports (openstaande orders/
#          leveringen) kiezen uit een inputmap en genereert daarvan, per
#          verkoopmedewerker, een overzichtsbestand (xlsx en/of csv) in een
#          outputmap. Geen live SAP-koppeling — pure lokale bestands-
#          verwerking via `oeoverview_info.py`. Overgezet uit het reeds
#          geteste, losstaande "OpenElements2Csv"-prototype (PyQt6), hier
#          herbouwd in PySide6 volgens ArticleSearch's eigen conventies
#          (geen i18n-laag, hardcoded Nederlandstalige labels, `Ctrl+Return`/
#          `Esc`-sneltoetsen, QSettings voor laatst gebruikte mappen —
#          analoog `ui_duepayment.py`).
# Version: 1.1.0
# Author:  Bart Bossuyt
# Changes: 1.1.0 — Standaardmap-instelling toegevoegd: bij het openen wordt
#                   nu eerst de vaste standaard input-/outputmap uit
#                   Instellingen gebruikt (settings.py's
#                   oeoverview_default_input_folder/
#                   oeoverview_default_output_folder), en enkel wanneer die
#                   leeg is, valt het scherm terug op de laatst gebruikte map
#                   (QSettings, ongewijzigd). Nieuwe helper
#                   _vul_default_mappen() vervangt
#                   _vul_laatst_gebruikte_mappen().
# Changes: 1.0.0 — Initiële opzet.
# =============================================================================

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

import oeoverview_info as oe
from settings import load_oeoverview_default_input_folder, load_oeoverview_default_output_folder

_ORG_NAME = "CGK Group"
_APP_NAME = "ArticleSearch"
_SETTINGS_KEY_INPUT = "oeoverview/last_input_folder"
_SETTINGS_KEY_OUTPUT = "oeoverview/last_output_folder"


class OeOverviewWindow(QWidget):
    """Compact formulierscherm — geen automatische call bij openen, pas
    verwerkt na klik op "Starten" (zelfde principe als de andere Export-
    modules: niets ophalen/verwerken zonder expliciete actie)."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Open Elements overview")
        self.setMinimumSize(640, 520)
        self.resize(640, 560)
        self.setContentsMargins(8, 8, 8, 8)

        self._qsettings = QSettings(_ORG_NAME, _APP_NAME)
        self._orders_candidates: list[oe.CandidateFile] = []
        self._leveringen_candidates: list[oe.CandidateFile] = []

        self._build_ui()
        self._vul_default_mappen()

        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self._start_verwerking)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)

    # ------------------------------------------------------------------
    # UI-opbouw
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)

        layout.addWidget(self._build_input_group())
        layout.addWidget(self._build_output_group())
        layout.addWidget(self._build_formaat_group())

        self._start_knop = QPushButton("Starten")
        self._start_knop.clicked.connect(self._start_verwerking)
        layout.addWidget(self._start_knop)

        self._log = QPlainTextEdit()
        self._log.setReadOnly(True)
        layout.addWidget(self._log, 1)

    def _build_input_group(self) -> QGroupBox:
        group = QGroupBox("Bronbestanden")
        layout = QVBoxLayout(group)

        map_row = QHBoxLayout()
        self._input_map_edit = QLineEdit()
        self._input_map_edit.setPlaceholderText("Map met de OpenVKOorders/OpenVKOleveringen-CSV's")
        self._input_map_edit.editingFinished.connect(self._vernieuw_kandidaten)
        map_row.addWidget(self._input_map_edit)
        bladeren = QPushButton("Bladeren...")
        bladeren.clicked.connect(self._kies_input_map)
        map_row.addWidget(bladeren)
        layout.addLayout(map_row)

        form = QFormLayout()
        self._orders_combo = QComboBox()
        form.addRow("Orders-bestand:", self._orders_combo)
        self._leveringen_combo = QComboBox()
        form.addRow("Leveringen-bestand:", self._leveringen_combo)
        layout.addLayout(form)

        return group

    def _build_output_group(self) -> QGroupBox:
        group = QGroupBox("Uitvoer")
        layout = QHBoxLayout(group)

        self._output_map_edit = QLineEdit()
        self._output_map_edit.setPlaceholderText("Map waar de overzichten per medewerker terechtkomen")
        layout.addWidget(self._output_map_edit)
        bladeren = QPushButton("Bladeren...")
        bladeren.clicked.connect(self._kies_output_map)
        layout.addWidget(bladeren)

        return group

    def _build_formaat_group(self) -> QGroupBox:
        group = QGroupBox("Uitvoerformaat")
        layout = QHBoxLayout(group)

        self._xlsx_check = QCheckBox("XLSX")
        self._xlsx_check.setChecked(True)
        self._csv_check = QCheckBox("CSV")
        layout.addWidget(self._xlsx_check)
        layout.addWidget(self._csv_check)

        return group

    # ------------------------------------------------------------------
    # Mapkeuze / kandidaten
    # ------------------------------------------------------------------

    def _vul_default_mappen(self) -> None:
        """Vult de input-/outputmap bij het openen: eerst de vaste standaard
        uit Instellingen (indien ingesteld), anders de laatst gebruikte map
        (QSettings)."""
        default_input = load_oeoverview_default_input_folder()
        default_output = load_oeoverview_default_output_folder()
        last_input = self._qsettings.value(_SETTINGS_KEY_INPUT, "", type=str)
        last_output = self._qsettings.value(_SETTINGS_KEY_OUTPUT, "", type=str)

        input_map = default_input or last_input
        output_map = default_output or last_output

        if input_map:
            self._input_map_edit.setText(input_map)
        if output_map:
            self._output_map_edit.setText(output_map)
        self._vernieuw_kandidaten()

    def _kies_input_map(self) -> None:
        gekozen = QFileDialog.getExistingDirectory(self, "Inputmap", self._input_map_edit.text())
        if gekozen:
            self._input_map_edit.setText(gekozen)
            self._qsettings.setValue(_SETTINGS_KEY_INPUT, gekozen)
            self._vernieuw_kandidaten()

    def _kies_output_map(self) -> None:
        gekozen = QFileDialog.getExistingDirectory(self, "Outputmap", self._output_map_edit.text())
        if gekozen:
            self._output_map_edit.setText(gekozen)
            self._qsettings.setValue(_SETTINGS_KEY_OUTPUT, gekozen)

    def _vernieuw_kandidaten(self) -> None:
        tekst = self._input_map_edit.text()
        input_map = Path(tekst) if tekst else None
        self._orders_candidates = []
        self._leveringen_candidates = []
        self._orders_combo.clear()
        self._leveringen_combo.clear()

        if input_map is None or not input_map.is_dir():
            return

        self._qsettings.setValue(_SETTINGS_KEY_INPUT, str(input_map))

        try:
            self._orders_candidates = oe.find_candidate_files(input_map, oe.SOURCE_TYPE_ORDERS)
            self._leveringen_candidates = oe.find_candidate_files(input_map, oe.SOURCE_TYPE_LEVERINGEN)
        except oe.CsvLoadError:
            return

        for c in self._orders_candidates:
            self._orders_combo.addItem(c.display_name, c.path)
        for c in self._leveringen_candidates:
            self._leveringen_combo.addItem(c.display_name, c.path)

    # ------------------------------------------------------------------
    # Verwerking
    # ------------------------------------------------------------------

    def _start_verwerking(self) -> None:
        if not self._input_map_edit.text():
            self._log_fout("Selecteer eerst een inputmap.")
            return
        if not self._output_map_edit.text():
            self._log_fout("Selecteer eerst een outputmap.")
            return

        formaten: set[str] = set()
        if self._xlsx_check.isChecked():
            formaten.add(oe.FORMAT_XLSX)
        if self._csv_check.isChecked():
            formaten.add(oe.FORMAT_CSV)
        if not formaten:
            self._log_fout("Selecteer minstens één uitvoerformaat.")
            return

        if self._orders_combo.currentData() is None:
            self._log_fout("Geen orders-bestand gevonden in de inputmap.")
            return
        if self._leveringen_combo.currentData() is None:
            self._log_fout("Geen leveringen-bestand gevonden in de inputmap.")
            return

        self._log.appendPlainText("Verwerking gestart...")
        self._start_knop.setEnabled(False)
        try:
            orders_rows = oe.load_csv(self._orders_combo.currentData(), oe.SOURCE_TYPE_ORDERS)
            leveringen_rows = oe.load_csv(self._leveringen_combo.currentData(), oe.SOURCE_TYPE_LEVERINGEN)
            resultaten = oe.process(orders_rows, leveringen_rows)
            output_map = Path(self._output_map_edit.text())
            geschreven = oe.export_all(resultaten, output_map, formaten)
        except oe.CsvLoadError as exc:
            self._log_fout(exc.message)
            return
        except OSError as exc:
            self._log_fout(str(exc))
            return
        finally:
            self._start_knop.setEnabled(True)

        self._qsettings.setValue(_SETTINGS_KEY_OUTPUT, str(output_map))

        self._log.appendPlainText(
            f"{len(resultaten)} medewerker(s) verwerkt — {len(geschreven)} bestand(en) "
            f"weggeschreven naar {output_map}."
        )
        self._log.appendPlainText("Verwerking voltooid.")
        self._open_map(output_map)

    def _open_map(self, path: Path) -> None:
        """Open ``path`` in de systeem-bestandsverkenner (best effort — een
        mislukte poging mag de afgeronde verwerking niet laten falen)."""
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except OSError:
            pass

    def _log_fout(self, bericht: str) -> None:
        self._log.appendPlainText(bericht)
        self._log.appendPlainText("Verwerking mislukt.")