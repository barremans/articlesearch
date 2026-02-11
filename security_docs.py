"""
security_docs.py
Volledige AD-only beveiliging voor ui_docs.
Geen wachtwoord, geen unlock prompt.
Alleen bruikbaar als een geldige AD-verbinding actief is.
"""

from __future__ import annotations
from auth import can_connect_to_ad


# ========================
#  CORE FUNCTIONS
# ========================

def is_unlocked() -> bool:
    """
    Geeft True als AD-verbinding actief is.
    Anders False (offline of geen AD).
    """
    try:
        return bool(can_connect_to_ad())
    except Exception:
        return False


def lock_disabled() -> bool:
    """
    Locking is alleen uitgeschakeld wanneer AD actief is.
    Dus niet zomaar altijd True zoals in de stub.
    """
    return is_unlocked()


def password() -> str:
    """
    ui_docs gebruikt geen wachtwoord meer.
    """
    return ""


def unlock():
    """
    Geen actie nodig (compatibiliteit met oude code).
    """
    pass


def relock():
    """
    Geen actie nodig.
    """
    pass
