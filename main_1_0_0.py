import os
import sys
import threading
from PySide6.QtWidgets import QApplication
from ui_main import MainWindow
from auth import preload_token as preload_article_token
from stock_token import preload_token as preload_stock_token
#from permissions_azure import connect_to_azure_ad as can_connect_to_ad
from permissions_azure import connect_to_azure_ad, list_user_groups

import config


def app_root() -> str:
    """Betrouwbare basis voor resources (werkt in dev, dist en na installatie)."""
    if getattr(sys, "frozen", False):
        # onedir: bestanden staan naast de exe
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def res(*parts: str) -> str:
    """Bouw een pad op relatief aan de applicatie-root."""
    return os.path.join(app_root(), *parts)


def load_stylesheet(app: QApplication) -> None:
    """Laad een optionele QSS-stylesheet als die bestaat."""
    qss = res("assets", "css", "style.qss")
    try:
        if os.path.exists(qss):
            with open(qss, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        else:
            print(f"[warn] stylesheet niet gevonden: {qss}", file=sys.stderr)
    except Exception as e:
        print(f"[warn] stylesheet laden faalde: {e}", file=sys.stderr)


def preload_tokens():
    """Probeer tokens vooraf te laden, maar faal stil als het niet lukt."""
    try:
        preload_article_token()
    except Exception as e:
        print(f"[warn] preload_article_token: {e}", file=sys.stderr)
    try:
        preload_stock_token()
    except Exception as e:
        print(f"[warn] preload_stock_token: {e}", file=sys.stderr)


def async_fetch_azure_groups():
    """Haalt Azure AD-groepen op in een achtergrondthread, zonder de GUI te blokkeren."""

    import threading

    def fetch():
        try:
            # Log in en haal groepen op
            if connect_to_azure_ad():
                groups = list_user_groups()
                if groups:
                    print(f"[AD] ✅ {len(groups)} groepen opgehaald:")
                    for g in groups:
                        print(f" - {g}")
                else:
                    print("[AD] ⚠️ Geen groepen gevonden (lege lijst).")
            else:
                print("[AD] ❌ Verbinding met Azure AD mislukt.")
        except Exception as e:
            print(f"[AD] ❌ Fout bij ophalen Azure-groepen: {e}")

    threading.Thread(target=fetch, daemon=True).start()



def main():
    """Startpunt van de applicatie."""
    print("[APP] 🚀 Start applicatie...")

    app = QApplication(sys.argv)
    load_stylesheet(app)

    window = MainWindow()
    window.show()

    # tokens vooraf laden
    preload_tokens()

    # Azure AD login + groepen ophalen in achtergrond
    async_fetch_azure_groups()

    print("[APP] ✅ Applicatie klaar — GUI actief.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
