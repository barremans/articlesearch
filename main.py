# main.py
import os, sys
from PySide6.QtWidgets import QApplication
from ui_main import MainWindow
from auth import preload_token as preload_article_token
from stock_token import preload_token as preload_stock_token

def app_root() -> str:
    """Betrouwbare basis voor resources (werkt in dev, dist en na installatie)."""
    if getattr(sys, 'frozen', False):
        # onedir: bestanden staan naast de exe
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def res(*parts: str) -> str:
    return os.path.join(app_root(), *parts)

def load_stylesheet(app: QApplication) -> None:
    qss = res("assets", "css", "style.qss")
    try:
        if os.path.exists(qss):
            with open(qss, "r", encoding="utf-8") as f:
                app.setStyleSheet(f.read())
        else:
            # geen modal dialoog; stille waarschuwing
            print(f"[warn] stylesheet niet gevonden: {qss}", file=sys.stderr)
    except Exception as e:
        print(f"[warn] stylesheet laden faalde: {e}", file=sys.stderr)

def main():
    # tokens vooraf laden
    try:
        preload_article_token()
    except Exception as e:
        print(f"[warn] preload_article_token: {e}", file=sys.stderr)
    try:
        preload_stock_token()
    except Exception as e:
        print(f"[warn] preload_stock_token: {e}", file=sys.stderr)

    app = QApplication(sys.argv)
    load_stylesheet(app)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
