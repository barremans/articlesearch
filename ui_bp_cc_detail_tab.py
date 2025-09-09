# ui_bp_cc_detail_tab.py
from typing import Optional, Callable, Any
import os
import datetime as _dt

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QInputDialog, QLineEdit, QMessageBox, QFrame, QStackedLayout,
    QPlainTextEdit
)

import security_cc
from ui_bp_cc_lists_tab import CreditControlListsTab  # bevat de vijf subtabs

# Debug is volledig uitgezet (knop + UI verwijderd)
DEBUG_DEFAULT = False


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
        self._password_provider = password_provider or security_cc.password
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

        self.lock_msg = QLabel("Deze tab is vergrendeld.\nKlik op 'Ontgrendel' en voer het wachtwoord in.")
        self.lock_msg.setAlignment(Qt.AlignCenter)
        self.lock_msg.setStyleSheet("color: #555;")

        btn_unlock = QPushButton("Ontgrendel")
        btn_unlock.setFixedWidth(160)
        btn_unlock.clicked.connect(self._unlock_prompt)

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

        # Init: toon content als app reeds unlocked of bypass actief
        if security_cc.is_unlocked():
            self._show_content()
        else:
            self.lock()

    # ---------- Public API ----------
    def is_unlocked(self) -> bool:
        return self._unlocked or security_cc.is_unlocked()

    def lock(self):
        self._unlocked = False
        self._current_card_code = ""
        security_cc.relock()
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
        security_cc.unlock()
        self.stack.setCurrentIndex(1)
        self._update_title()

    def _update_title(self):
        suffix = f" — {self._current_card_code}" if self._current_card_code else ""
        self.lbl_title.setText(f"Credit Control{suffix}")

    def _unlock_prompt(self):
        # Dev-bypass: geen prompt
        if security_cc.lock_disabled():
            self._show_content()
            self.cc_lists.show_after_unlock(self._current_card_code or None)
            return

        pw_expected = (self._password_provider() or "").strip()
        if not pw_expected:
            QMessageBox.warning(self, "Configuratie", "Er is geen wachtwoord geconfigureerd.")
            return

        pw, ok = QInputDialog.getText(
            self, "Ontgrendel Credit Control",
            "Wachtwoord:", QLineEdit.EchoMode.Password  # type: ignore[attr-defined]
        )
        if not ok:
            return

        if pw.strip() == pw_expected:
            self._show_content()
            self.cc_lists.show_after_unlock(self._current_card_code or None)
        else:
            QMessageBox.warning(self, "Onjuist wachtwoord", "Het wachtwoord is onjuist.")
