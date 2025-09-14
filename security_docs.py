# security_docs.py
# Sessie-lock voor ui_docs, met hetzelfde wachtwoord als BP (security_cc.password)

from __future__ import annotations
import os

# Interne sessiestatus voor dit venster (alleen zolang ui_docs open is)
_UNLOCKED: bool = False

def password() -> str:
    """
    Wachtwoordbron:
    1) DOCS_PASSWORD (optioneel override)
    2) security_cc.password()  ← zelfde als BP
    3) anders: leeg
    """
    pw = os.environ.get("DOCS_PASSWORD", "").strip()
    if pw:
        return pw
    try:
        import security_cc
        return (security_cc.password() or "").strip()
    except Exception:
        return ""

def lock_disabled() -> bool:
    """
    Dev-bypass via env var DOCS_LOCK_DISABLED=1 (optioneel).
    """
    v = os.environ.get("DOCS_LOCK_DISABLED", "").strip().lower()
    return v in {"1", "true", "yes", "y"}

def is_unlocked() -> bool:
    return _UNLOCKED or lock_disabled()

def unlock():
    global _UNLOCKED
    _UNLOCKED = True

def relock():
    global _UNLOCKED
    _UNLOCKED = False
