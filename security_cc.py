# security_cc.py
import os
from PySide6.QtWidgets import QApplication

APP_FLAG = "cc_tab_unlocked"


def _app():
    return QApplication.instance()


def password() -> str:
    """
    Voorkeur: config.CC_TAB_PASSWORD -> env var CC_TAB_PASSWORD -> fallback.
    """
    try:
        from config import CC_TAB_PASSWORD  # type: ignore
        if CC_TAB_PASSWORD:
            return str(CC_TAB_PASSWORD)
    except Exception:
        pass
    return os.environ.get("CC_TAB_PASSWORD", "cgk-cc")


def lock_disabled() -> bool:
    """
    Dev-bypass: config.CC_LOCK_DISABLED of env var CC_LOCK_DISABLED in {1,true,yes,y}.
    """
    try:
        from config import CC_LOCK_DISABLED  # type: ignore
        if bool(CC_LOCK_DISABLED):
            return True
    except Exception:
        pass
    envv = os.environ.get("CC_LOCK_DISABLED", "").strip().lower()
    return envv in ("1", "true", "yes", "y")


def is_unlocked() -> bool:
    if lock_disabled():
        return True
    app = _app()
    return bool(app.property(APP_FLAG)) if app else False  # type: ignore


def unlock():
    app = _app()
    if app:
        app.setProperty(APP_FLAG, True)  # type: ignore


def relock():
    app = _app()
    if app:
        app.setProperty(APP_FLAG, False)  # type: ignore
