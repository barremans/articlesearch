# =============================================================================
# ArticleSearch
# File:    main.py
# Role:    Entry point — hard security gate (offline-check, Azure AD-login
#          met timeout, basis-groepscontrole), preload van API-tokens, start
#          MainWindow (of NoAccessWindow bij geen toegang).
# Version: 1.1.0
# Author:  Bart Bossuyt
# Changes: 1.1.0 — CC-ACCESS-1 vervolg: "CGK-APP-L6" toegevoegd aan
#                   BASE_ACCESS_GROUPS. Ontbrak eerder — een gebruiker die
#                   enkel lid is van CGK-APP-L6 kwam daardoor nooit door de
#                   basis-toegangscontrole (has_base_access()) heen en
#                   bereikte het BP-venster / de Credit Control-tab dus
#                   nooit, ondanks dat CGK-APP-L6 wel is toegestaan in de
#                   CC_ACCESS_GROUPS-check van ui_bp_cc_detail_tab.py
#                   (v1.1.0). Zonder deze fix was die groep effectief dode
#                   toegang.
# Changes: 1.0.3 — Baseline (was al voorzien van informele versiecode
#                   "V1.0.3" bovenaan) — vóór introductie van het
#                   gestructureerde versiebeheer in commentaar.
# =============================================================================
import os
import sys
import threading
from PySide6.QtWidgets import QApplication

from ui_main import MainWindow
from ui_no_access import NoAccessWindow
from permissions_azure import connect_to_azure_ad, user_in_azure_group
from auth import preload_token as preload_article_token
from stock_token import preload_token as preload_stock_token
import config


# -----------------------------
# Basis Azure AD toegangsgroepen
# -----------------------------
BASE_ACCESS_GROUPS = {
    "Alle gebruikers",
    "CGK-APP-L1",
    "CGK-APP-L2",
    "CGK-APP-L3",
    "CGK-APP-L4",
    "CGK-APP-L5",
    "CGK-APP-L6",  # ✅ NIEUW (CC-ACCESS-1-fix): anders geen basistoegang mogelijk voor L6-leden
}


def has_base_access() -> bool:
    """
    Gebruiker heeft toegang als hij in minstens één
    van de basisgroepen zit.
    """
    return any(user_in_azure_group(g) for g in BASE_ACCESS_GROUPS)


# -----------------------------
# Azure AD login met timeout
# -----------------------------
def try_azure_login(timeout_sec: int = 30) -> bool:
    """
    Probeert Azure AD login.
    Breekt af na timeout (bv. browser gesloten).
    """
    result = {"ok": False}

    def worker():
        try:
            result["ok"] = connect_to_azure_ad()
        except Exception:
            result["ok"] = False

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    t.join(timeout=timeout_sec)

    if t.is_alive():
        print("[SECURITY] ❌ Azure AD login timeout / afgebroken")
        return False

    return result["ok"]


# -----------------------------
# Tokens vooraf laden
# -----------------------------
def preload_tokens():
    try:
        preload_article_token()
        preload_stock_token()
    except Exception as e:
        print(f"[warn] preload tokens: {e}", file=sys.stderr)


# -----------------------------
# App start
# -----------------------------
def main():
    print("[APP] 🚀 Start applicatie...")

    app = QApplication(sys.argv)

    # 🔒 HARD SECURITY GATE
    try:
        if config.OFFLINE_MODE:
            raise RuntimeError("OFFLINE_MODE actief")

        if not try_azure_login(timeout_sec=30):
            raise RuntimeError("Azure AD login mislukt of afgebroken")

        if not has_base_access():
            raise RuntimeError("Gebruiker heeft geen basisrechten")

    except Exception as e:
        print(f"[SECURITY] ❌ Geen toegang: {e}")
        win = NoAccessWindow()
        win.show()
        sys.exit(app.exec())

    # ✅ BASIS TOEGANG OK
    print("[SECURITY] ✅ Basis toegang verleend")

    preload_tokens()

    window = MainWindow()
    window.show()

    print("[APP] ✅ Applicatie klaar — GUI actief.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
