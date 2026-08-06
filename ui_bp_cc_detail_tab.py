# =============================================================================
# ArticleSearch
# File:    ui_bp_cc_detail_tab.py
# Role:    Credit Control-tab binnen BpWindow — wachtwoord/AD-vergrendeld,
#          toont 5 detaillijsten (Orders/Leveringen/Voorschotten/Facturen/
#          Kredietnota's) via CreditControlListsTab.
# Version: 1.3.0
# Author:  Bart Bossuyt
# Changes: 1.3.0 — HERSTEL (CC-ACCESS-1): dit bestand was teruggevallen naar
#                   een versie van vóór de CC-ACCESS-1-fix — twee losse
#                   problemen hersteld:
#                   (1) _ad_unlock_check() en de auto-unlock-poging in
#                       __init__ controleerden enkel generieke AD-login
#                       (get_auth_header() geeft geldige headers), niet de
#                       vereiste groepen. Hersteld: expliciete controle op
#                       CC_ACCESS_GROUPS (CGK-APP-L2, CGK-APP-L3,
#                       CGK-APP-L4, CGK-APP-L6) via user_in_azure_group().
#                   (2) set_from_json() vulde cc_lists.set_all() (de 5
#                       detaillijsten) ONVOORWAARDELIJK, ongeacht
#                       is_unlocked() — het exacte datalek van vóór de
#                       eerdere fix. Hersteld: enkel vullen wanneer
#                       is_unlocked() True is.
#                   Bewust NIET aangepast: het financiële headerpaneel
#                   (buiten dit bestand, in ui_bp_header_panel.py) blijft
#                   voor iedereen zichtbaar — dat viel destijds expliciet
#                   niet onder CC-ACCESS-1.
# Changes: 1.0.0 — Baseline vóór introductie van versiebeheer in commentaar.
# =============================================================================
from typing import Optional, Callable, Any
import os
import datetime as _dt
import requests

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QInputDialog, QLineEdit, QMessageBox, QFrame, QStackedLayout,
    QPlainTextEdit
)

from config import API_ENVIRONMENTS, ENVIRONMENT
from ui_bp_cc_lists_tab import CreditControlListsTab  # bevat de vijf subtabs

from config import OFFLINE_MODE  # ✅ toevoegen
from auth import get_auth_header, can_connect_to_ad  # (je hebt get_auth_header al)
from permissions_azure import user_in_azure_group  # HERSTEL (CC-ACCESS-1)


# Debug is volledig uitgezet (knop + UI verwijderd)
DEBUG_DEFAULT = False

# HERSTEL (CC-ACCESS-1): enkel deze Azure AD-groepen krijgen de 5
# detaillijsten van Credit Control te zien binnen het BP-venster.
CC_ACCESS_GROUPS = {"CGK-APP-L2", "CGK-APP-L3", "CGK-APP-L4", "CGK-APP-L6"}


def _has_cc_access() -> bool:
    """HERSTEL (CC-ACCESS-1): True als de gebruiker lid is van minstens
    één van de CC_ACCESS_GROUPS (niet enkel 'is ingelogd via AD')."""
    try:
        return any(user_in_azure_group(g) for g in CC_ACCESS_GROUPS)
    except Exception:
        return False


class CreditControlDetailTab(QWidget):
    """
    Credit Control met wachtwoordslot en de 5 subtabs:
      - Orders
      - Leveringen
      - Voorschotten
      - Facturen
      - Kredietnota's
    """

    def __init__(self, parent=None, password_provider: Optional[Callable[[], str]] = None, debug: bool = False):
        super().__init__(parent)
        #self._password_provider = password_provider or security_cc.password
        self._unlocked: bool = False
        self._current_card_code: str = ""
        self._debug: bool = False  # debug UI bestaat niet meer

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        # --- Stacked: [0]=Locked, [1]=Content ---
        self.stack = QStackedLayout()
        root.addLayout(self.stack, 1)

        # ===== LOCKED VIEW =====
        locked = QWidget()
        lyt_lock = QVBoxLayout(locked)
        lyt_lock.setAlignment(Qt.AlignCenter)

        lock_icon = QLabel("🔒")
        lock_icon.setAlignment(Qt.AlignCenter)
        lock_icon.setStyleSheet("font-size: 42px;")

        self.lock_msg = QLabel("Deze tab is beveiligd.\nKlik op 'Controleer AD-login' om toegang te krijgen.")
        self.lock_msg.setAlignment(Qt.AlignCenter)
        self.lock_msg.setStyleSheet("color: #555;")

        btn_unlock = QPushButton("Controleer AD-login")
        btn_unlock.setFixedWidth(200)
        btn_unlock.clicked.connect(self._ad_unlock_check)


        lyt_lock.addWidget(lock_icon)
        lyt_lock.addSpacing(8)
        lyt_lock.addWidget(self.lock_msg)
        lyt_lock.addSpacing(12)
        lyt_lock.addWidget(btn_unlock, alignment=Qt.AlignCenter)

        # ===== CONTENT VIEW =====
        content = QWidget()
        lyt_content = QVBoxLayout(content)
        lyt_content.setContentsMargins(0, 0, 0, 0)
        lyt_content.setSpacing(8)

        head = QHBoxLayout()
        self.lbl_title = QLabel("Credit Control")
        self.lbl_title.setStyleSheet("font-weight: 600;")
        head.addWidget(self.lbl_title)
        head.addStretch(1)

        self.btn_lock = QPushButton("Vergrendel opnieuw")
        self.btn_lock.setFixedWidth(160)
        self.btn_lock.clicked.connect(self.lock)
        head.addWidget(self.btn_lock)

        lyt_content.addLayout(head)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        lyt_content.addWidget(line)

        # Subtabs
        self.cc_lists = CreditControlListsTab(self, debug=False)
        lyt_content.addWidget(self.cc_lists, 1)

        # Geen debug-balk/paneel meer

        self.stack.addWidget(locked)   # index 0
        self.stack.addWidget(content)  # index 1

        # Init: probeer automatisch te unlocken via AD-token
        # Init: bepaal toegang (offline = altijd gelockt)
        from config import OFFLINE_MODE

        if OFFLINE_MODE:
            print("[CC] ⚠️ Offline modus — Credit Control blijft vergrendeld.")
            self.lock()
        else:
            try:
                # HERSTEL (CC-ACCESS-1): groepscontrole i.p.v. enkel
                # generieke AD-login (elke ingelogde gebruiker kon anders
                # onterecht meteen door de vergrendeling heen).
                if _has_cc_access():
                    self._show_content()
                else:
                    self.lock()
            except Exception:
                self.lock()



    # ---------- Public API ----------
    def is_unlocked(self) -> bool:
        return self._unlocked


    def lock(self):
        self._unlocked = False
        self._current_card_code = ""
        self.stack.setCurrentIndex(0)

    def clear(self):
        self.cc_lists.clear()

    def set_loading(self, card_code: str):
        self._current_card_code = card_code or ""
        if self.is_unlocked():
            self._show_content()
            self.cc_lists.show_after_unlock(card_code)

    # Doorzetters naar de 5 lijsten
    def set_orders(self, rows):
        self.cc_lists.set_orders(rows)

    def set_deliveries(self, rows):
        self.cc_lists.set_deliveries(rows)

    def set_advances(self, rows):
        self.cc_lists.set_advances(rows)

    def set_invoices(self, rows):
        self.cc_lists.set_invoices(rows)

    def set_credit_notes(self, rows):
        self.cc_lists.set_credit_notes(rows)

    def set_cc_lists(self, **kwargs):
        self.cc_lists.set_all(**kwargs)

    def set_from_json(self, data: dict):
        """
        Ondersteunt:
          - vlakke structuur met keys 'ORDR'/'ODLN'/'ODPI'/'OINV'/'ORIN'
          - geneste structuur: Data -> BP -> '...' (zoals CC-service)
        """
        if not data:
            return

        bp: Any = data
        if isinstance(data, dict) and "Data" in data and isinstance(data["Data"], dict):
            inner = data["Data"].get("BP")
            if isinstance(inner, dict):
                bp = inner

        # Titel + kaartcode
        cc = bp.get("CustomerCode") if isinstance(bp, dict) else None
        if cc:
            self._current_card_code = str(cc)
            if self.is_unlocked():
                self._update_title()

        if self.is_unlocked():
            self._show_content()

        # HERSTEL (CC-ACCESS-1): dit was het eigenlijke datalek — de 5
        # detaillijsten werden hier voorheen ONVOORWAARDELIJK gevuld,
        # ongeacht is_unlocked(). Data zat dus al in de widgets, enkel
        # visueel verborgen achter de vergrendel-stack (QStackedLayout
        # toont enkel index 0, maar de data was al aanwezig in index 1).
        if not self.is_unlocked():
            return

        # Zet lijsten
        self.cc_lists.set_all(
            orders=(bp.get("ORDR") or []) if isinstance(bp, dict) else [],
            deliveries=(bp.get("ODLN") or []) if isinstance(bp, dict) else [],
            advances=(bp.get("ODPI") or []) if isinstance(bp, dict) else [],
            invoices=(bp.get("OINV") or []) if isinstance(bp, dict) else [],
            credit_notes=(bp.get("ORIN") or []) if isinstance(bp, dict) else [],
        )

    # ---------- Intern ----------
    def _show_content(self):
        first_show = not self._unlocked
        self._unlocked = True
        self.stack.setCurrentIndex(1)
        self._update_title()

    def _update_title(self):
        suffix = f" — {self._current_card_code}" if self._current_card_code else ""
        self.lbl_title.setText(f"Credit Control{suffix}")

    def _ad_unlock_check(self):
        """HERSTEL (CC-ACCESS-1): controleert of de gebruiker lid is van
        een toegelaten Azure AD-groep (CC_ACCESS_GROUPS) — niet enkel of
        er een geldige AD-sessie bestaat."""
        from config import OFFLINE_MODE
        if OFFLINE_MODE:
            QMessageBox.warning(self, "Offline modus",
                "De applicatie draait offline.\nCredit Control is niet beschikbaar.")
            return

        try:
            if _has_cc_access():
                self._show_content()
                self.cc_lists.show_after_unlock(self._current_card_code or None)
            else:
                raise RuntimeError(
                    "Geen toegang — vereist lidmaatschap van "
                    f"{', '.join(sorted(CC_ACCESS_GROUPS))}."
                )
        except Exception as e:
            QMessageBox.warning(self, "Geen toegang", f"Toegangscontrole mislukt:\n{e}")