
# label_generator.py
import os
import sys
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm as unit_mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO
from barcode import Code128
from barcode.writer import ImageWriter
from PIL import Image
import traceback

from settings import load_label_settings

# Logging pad
LOGFILE = os.path.join(tempfile.gettempdir(), "label_log.txt")

def log(msg):
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

def generate_label(article_number, description, supplier_article, inbound_number):
    try:
        log(f"Start label genereren voor artikel: {article_number}")
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Instellingen laden
        s = load_label_settings()

        # Genereer barcode
        barcode_buffer = BytesIO()
        options = {
            "write_text": False,  # Zet de tekst onder de barcode uit
             "dpi": 1200  # Verhoogd voor scherpte
        }
        code128 = Code128(article_number, writer=ImageWriter())
        code128.write(barcode_buffer, options)
        barcode_img = Image.open(barcode_buffer)

        # Bepaal gewenste barcodegrootte in mm
        barcode_target_width_mm = s["LABEL_WIDTH"] * s.get("BARCODE_WIDTH_SCALE", 0.45)
        barcode_target_height_mm = s["LABEL_HEIGHT"] * s.get("BARCODE_HEIGHT_SCALE", 0.15)

        # Zet om naar pixels (300 dpi = ≈ 12 px per mm)
        mm_to_px = 12
        barcode_target_size = (
            int(barcode_target_width_mm * mm_to_px),
            int(barcode_target_height_mm * mm_to_px)
        )

        barcode_img = barcode_img.resize(barcode_target_size)

        barcode_io = BytesIO()
        barcode_img.save(barcode_io, format='PNG')
        barcode_reader = ImageReader(barcode_io)

        # PDF aanmaken
        pdf_path = os.path.join(tempfile.gettempdir(), "label_output.pdf")
        c = canvas.Canvas(pdf_path, pagesize=(s["LABEL_WIDTH"] * unit_mm, s["LABEL_HEIGHT"] * unit_mm))

        # Font
        fallback_font_path = os.path.join(os.path.dirname(__file__), "arial.ttf")
        if os.path.exists(fallback_font_path):
            pdfmetrics.registerFont(TTFont("Arial", fallback_font_path))
            font_name = "Arial"
            log("Arial.ttf gebruikt")
        else:
            font_name = "Helvetica"
            log("Fallback naar Helvetica")

        c.setFillColorRGB(0, 0, 0)

        # Barcode tekenen
        x = s.get("BARCODE_LEFT", 0) * unit_mm
        y = s.get("BARCODE_TOP", 0) * unit_mm
        barcode_width = barcode_img.width * 0.264583 * unit_mm
        log(f"PDF grootte: {s['LABEL_WIDTH']}x{s['LABEL_HEIGHT']}, barcode top={s['BARCODE_TOP']}, left={s['BARCODE_LEFT']}")
        c.drawImage(barcode_reader, x, y, width=barcode_width, preserveAspectRatio=True)
        log(f"Barcode getekend op x={x}, y={y}, breedte={barcode_width}")

        # Artikel
        c.setFont(font_name, s.get("FONT_SIZE_ART", 10))
        c.drawString(s["ART_LEFT"] * unit_mm, s["ART_TOP"] * unit_mm, f"Art: {article_number}")

        
        # Beschrijving
        c.setFont(font_name, s.get("FONT_SIZE_DESCRIPTION", 10))
        c.drawString(s["DESCRIPTION_LEFT"] * unit_mm, s["DESCRIPTION_TOP"] * unit_mm, description)

        # Leverancier
        c.setFont(font_name, s.get("FONT_SIZE_SUPPLIER", 9))
        c.drawString(s["SUPPLIER_LEFT"] * unit_mm, s["SUPPLIER_TOP"] * unit_mm, f"Suppl.Art: {supplier_article}")

        # Inbound
        #c.setFont(font_name, s.get("FONT_SIZE_INBOUND", 9))
        #c.drawString(s["INBOUND_LEFT"] * unit_mm, s["INBOUND_TOP"] * unit_mm, f"Inbound: {inbound_number}")

        # Datum
        c.setFont(font_name, s.get("FONT_SIZE_DATE", 8))
        c.drawString(s["DATE_LEFT"] * unit_mm, s["DATE_TOP"] * unit_mm, f"Date: {current_date}")

        c.showPage()
        c.save()

        if not os.path.exists(pdf_path):
            raise RuntimeError("PDF werd niet opgeslagen")

        log(f"PDF gegenereerd: {pdf_path}")

        if sys.platform.startswith("win"):
            os.system(f'start "" "{pdf_path}"')
        elif sys.platform == "darwin":
            os.system(f"open {pdf_path}")
        else:
            os.system(f"xdg-open {pdf_path}")

    except Exception as e:
        log("FOUT tijdens generate_label():")
        log(traceback.format_exc())
        raise RuntimeError(f"Fout bij labelgeneratie: {e}")