
# label_settings.py
"""
label_settings.py

Standaardwaarden voor het genereren van labels.
Worden geladen via settings.py bij het opstarten van de applicatie.
"""

# Labelgrootte (in millimeters)
LABEL_WIDTH = 85
LABEL_HEIGHT = 25

# Schaalfactoren voor barcode
BARCODE_WIDTH_SCALE = 0.45
BARCODE_HEIGHT_SCALE = 0.15

# Lettergroottes
FONT_SIZE_DESCRIPTION = 10
FONT_SIZE_SUPPLIER = 10
FONT_SIZE_INBOUND = 10
FONT_SIZE_DATE = 8

# Kleuren
TEXT_COLOR = "black"
BORDER_COLOR = "#000"

# Padding instellingen (indien nodig later uitbreidbaar)
TEXT_PADDING = {
    "top": 1,
    "right": 10,
    "bottom": 0,
    "left": 100
}

DATE_PADDING = {
    "top": 25,
    "right": 10,
    "bottom": 5,
    "left": 10
}
