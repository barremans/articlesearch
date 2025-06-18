#base64_image_utils.py
# base64_image_utils.py
import base64
from PySide6.QtGui import QPixmap


def decode_base64_to_pixmap(b64_string: str) -> QPixmap:
    byte_data = base64.b64decode(b64_string)
    pixmap = QPixmap()
    if not pixmap.loadFromData(byte_data):
        raise ValueError("Kon afbeelding niet laden uit data.")
    return pixmap
