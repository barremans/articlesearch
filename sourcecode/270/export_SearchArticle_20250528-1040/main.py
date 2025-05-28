#main.py
from PySide6.QtWidgets import QApplication
from ui_main import MainWindow
from auth import preload_token as preload_article_token
from stock_token import preload_token as preload_stock_token
import sys

def main():
    # Laad tokens vooraf om vertraging bij eerste API-call te vermijden
    preload_article_token()
    preload_stock_token()

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
