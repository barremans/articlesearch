# ui_bp.py
import sys
import requests
from typing import Any, Optional
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTabWidget, QMessageBox
)
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtCore import Qt, Signal, Slot

from bp_token import get_auth_header
from config import API_ENVIRONMENTS, ENVIRONMENT

from ui_bp_header_panel import HeaderPanel
from ui_bp_addresses_tab import AddressesTab
from ui_bp_contacts_tab import ContactsTab

from cc_service import fetch_cc_data  # ongewijzigd laten

# SSL warnings onderdrukken omdat verify=False gebruikt wordt bij requests
requests.packages.urllib3.disable_warnings()  # type: ignore


class BpWindow(QWidget):
    # Signals om worker-resultaten veilig naar de UI-thread te brengen
    bp_success = Signal(object, int)     # (data_dict, req_id)
    bp_error = Signal(str, int)          # (error_message, req_id)
    cc_success = Signal(object, str)     # (cc_dict_of_None, card_code)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Business Partner")
        self.setContentsMargins(6, 6, 6, 6)

        self.results: list[dict] = []
        self.current_card_code: str = ""

        # Async state
        self._exec = ThreadPoolExecutor(max_workers=4)
        self._req_counter: int = 0  # om races te vermijden bij snelle opeenvolgingen

        # UI layout
        root = QVBoxLayout(self)
        root.setSpacing(6)

        # ---------- Zoek-regel 1 ----------
        row1 = QHBoxLayout(); row1.setSpacing(8)
        self.zoekterm_input = QLineEdit("K05036")
        self.zoekterm_input.setPlaceholderText("bv. K05036")
        row1.addWidget(QLabel("Zoekterm (@zoekterm):"))
        row1.addWidget(self.zoekterm_input, 1)
        root.addLayout(row1)

        # ---------- Zoek-regel 2 ----------
        row2 = QHBoxLayout(); row2.setSpacing(8)
        self.mode_input = QLineEdit(); self.mode_input.setPlaceholderText("leeg laten"); self.mode_input.setFixedWidth(140)
        self.type_input = QLineEdit(); self.type_input.setPlaceholderText("leeg laten"); self.type_input.setFixedWidth(140)
        self.btn_fetch = QPushButton("Ophalen"); self.btn_fetch.setFixedWidth(110); self.btn_fetch.clicked.connect(self.load_data)
        row2.addWidget(QLabel("Mode (@mode):")); row2.addWidget(self.mode_input)
        row2.addSpacing(12)
        row2.addWidget(QLabel("Type (@type):")); row2.addWidget(self.type_input)
        row2.addSpacing(12)
        row2.addWidget(self.btn_fetch)
        row2.addStretch(1)
        root.addLayout(row2)

        # ---------- Resultaatkeuze ----------
        row_pick = QHBoxLayout(); row_pick.setSpacing(8)
        row_pick.addWidget(QLabel("Gevonden partners:"))
        self.result_picker = QComboBox()
        self.result_picker.currentIndexChanged.connect(self._on_pick_changed)
        row_pick.addWidget(self.result_picker, 1)
        root.addLayout(row_pick)

        # ---------- Header panel ----------
        self.header_panel = HeaderPanel(self)
        root.addWidget(self.header_panel)

        # ---------- Tabs ----------
        self.tabs = QTabWidget()
        self.addr_tab = AddressesTab(self)
        self.contacts_tab = ContactsTab(self)
        self.tabs.addTab(self.addr_tab, "Adressen")
        self.tabs.addTab(self.contacts_tab, "Contacten")
        self.tabs.addTab(QWidget(), "Overzicht")
        root.addWidget(self.tabs, 1)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+Return"), self).activated.connect(self.load_data)
        QShortcut(QKeySequence("Esc"), self).activated.connect(self.close)

        # Signals koppelen
        self.bp_success.connect(self._on_bp_success)
        self.bp_error.connect(self._on_bp_error)
        self.cc_success.connect(self._on_cc_success)

    # ------- preset vanuit ui_main -------
    def preset_and_fetch(self, zoekterm: str, auto_fetch: bool = True):
        self.zoekterm_input.setText(zoekterm or "")
        if auto_fetch:
            self.load_data()

    # ===================== ASYNC BP FETCH =====================

    @staticmethod
    def _do_bp_request(url: str, headers: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
        """
        Draait in threadpool. Doet POST, raise't bij fout, en retourneert JSON dict.
        """
        resp = requests.post(url, headers=headers, json=payload, verify=False, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("IsError"):
            raise RuntimeError(data.get("ErrorMessage") or "Onbekende API fout.")
        return data

    def load_data(self):
        """
        Start BP API-call in background, UI blijft responsief.
        """
        # UI hint: knop uit en cursor in 'busy'
        self.btn_fetch.setEnabled(False)
        self.setCursor(Qt.WaitCursor)

        # Nieuwe request-versie
        self._req_counter += 1
        req_id = self._req_counter

        config_id = API_ENVIRONMENTS.get(ENVIRONMENT, {}).get("so_configP_Bp", "OMW5IN")
        url = API_ENVIRONMENTS[ENVIRONMENT]["base_url"].rstrip("/") + "/api/datarequest"
        payload = {
            "ConfigurationID": config_id,
            "MultiKey": {
                "@zoekterm": self.zoekterm_input.text().strip(),
                "@mode": self.mode_input.text().strip(),
                "@type": self.type_input.text().strip(),
            }
        }
        headers = get_auth_header()

        # Worker-functie die in thread draait en via signals terugmeldt
        def _worker_bp():
            try:
                data = BpWindow._do_bp_request(url, headers, payload)
                self.bp_success.emit(data, req_id)
            except Exception as e:
                self.bp_error.emit(str(e), req_id)

        self._exec.submit(_worker_bp)

    # ===================== UI helpers =====================

    def _clear_all(self):
        self.header_panel.clear()
        self.addr_tab.clear()
        self.contacts_tab.clear()

    def _on_pick_changed(self, idx: int):
        if 0 <= idx < len(self.results):
            self._use_record(self.results[idx])

    def _use_record(self, rec: dict):
        """
        Toon onmiddellijk BP-data + placeholder financiële velden (uit BP),
        start CC-call parallel en overschrijf financiële sectie zodra CC er is.
        """
        # Linker kolom & midden vullen met BP
        self.header_panel.fill_left_and_middle(rec)

        # Adressen & contacten
        self.addr_tab.set_addresses(rec.get("BPAddresses", []) or [])
        self.contacts_tab.set_contacts(rec.get("ContactEmployees", []) or [])

        # Rechterkolom – eerst BP-velden (placeholder)
        self.header_panel.fill_financial_bp(rec)

        # CC async: bij afronding overschrijft dit het financiële blok
        card_code = str(rec.get("CardCode") or "")
        self.current_card_code = card_code
        self._fetch_cc_async(card_code)

    # ===================== ASYNC CC FETCH =====================

    def _fetch_cc_async(self, card_code: str):
        def _worker_cc():
            try:
                cc = fetch_cc_data(card_code)
            except Exception:
                cc = None
            self.cc_success.emit(cc, card_code)

        self._exec.submit(_worker_cc)

    # ===================== Slots (UI-thread) =====================

    @Slot(object, int)
    def _on_bp_success(self, data: object, req_id: int):
        # Alleen verwerken als dit de meest recente request is
        if req_id != self._req_counter:
            return

        # UI reset
        self.btn_fetch.setEnabled(True)
        self.unsetCursor()

        # Data[] verwerken
        data_dict = data if isinstance(data, dict) else {}
        root = data_dict.get("Data") if isinstance(data_dict, dict) else None

        self.results = []
        if isinstance(root, list):
            self.results = [r for r in root if isinstance(r, dict)]
        elif isinstance(root, dict):
            self.results = [root]

        # Picker vullen
        self.result_picker.blockSignals(True)
        self.result_picker.clear()
        for r in self.results:
            code = r.get("CardCode", "-"); name = r.get("CardName", "-")
            self.result_picker.addItem(f"{code} — {name}")
        self.result_picker.blockSignals(False)

        if not self.results:
            QMessageBox.information(self, "Geen resultaten", "Geen partners gevonden.")
            self._clear_all()
            return

        # eerste record tonen
        self._use_record(self.results[0])

    @Slot(str, int)
    def _on_bp_error(self, msg: str, req_id: int):
        # Alleen tonen als dit de actuele request is
        if req_id != self._req_counter:
            return
        self.btn_fetch.setEnabled(True)
        self.unsetCursor()
        QMessageBox.critical(self, "BP ophalen mislukt", msg)
        self._clear_all()

    @Slot(object, str)
    def _on_cc_success(self, cc: object, card_code: str):
        # Alleen updaten indien nog steeds het actuele record
        if not cc or card_code != self.current_card_code:
            return
        self.header_panel.fill_financial_cc(cc)

    # ===================== Proper afsluiten =====================

    def closeEvent(self, event):
        try:
            self._exec.shutdown(wait=False, cancel_futures=True)  # Python 3.9+: cancel_futures
        except TypeError:
            # Oudere Python zonder cancel_futures
            self._exec.shutdown(wait=False)
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = BpWindow()
    w.showMaximized()
    sys.exit(app.exec())
