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
import importlib.util
import traceback

# Logging pad
LOGFILE = os.path.join(tempfile.gettempdir(), "label_log.txt")

def log(msg):
    with open(LOGFILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {msg}\n")

# Instellingen dynamisch laden
try:
    settings_path = os.path.join(os.path.dirname(__file__), "label_settings.py")
    spec = importlib.util.spec_from_file_location("label_settings", settings_path)
    label_settings = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(label_settings)
except Exception as e:
    log(f"[FOUT] label_settings.py kon niet geladen worden: {e}")
    raise

def generate_label(article_number, description, supplier_article, inbound_number):
    try:
        log(f"Start label genereren voor artikel: {article_number}")
        current_date = datetime.now().strftime("%Y-%m-%d")

        # Genereer barcode
        barcode_buffer = BytesIO()
        font_path = os.path.join(os.path.dirname(__file__), "arial.ttf")

        writer = ImageWriter()
        if os.path.exists(font_path):
            writer.font_path = font_path
            log("Barcode font ingesteld op arial.ttf")
        else:
            log("Geen arial.ttf gevonden, standaard barcode font wordt gebruikt")

        code128 = Code128(article_number, writer=writer)
        code128.write(barcode_buffer)
        barcode_img = Image.open(barcode_buffer)

        barcode_img = barcode_img.resize((
            int(barcode_img.width * label_settings.BARCODE_WIDTH_SCALE),
            int(barcode_img.height * label_settings.BARCODE_HEIGHT_SCALE)
        ))

        barcode_io = BytesIO()
        barcode_img.save(barcode_io, format='PNG')
        barcode_reader = ImageReader(barcode_io)

        # Font register
        if os.path.exists(font_path):
            pdfmetrics.registerFont(TTFont("Arial", font_path))
            font_name = "Arial"
            log("Arial.ttf gebruikt voor PDF")
        else:
            font_name = "Helvetica"
            log("Fallback naar Helvetica voor PDF")

        # PDF pad in tempdir
        pdf_path = os.path.join(tempfile.gettempdir(), "label_output.pdf")
        c = canvas.Canvas(pdf_path, pagesize=(label_settings.LABEL_WIDTH * unit_mm, label_settings.LABEL_HEIGHT * unit_mm))

        barcode_width = barcode_img.width * 0.264583
        x = (label_settings.LABEL_WIDTH - barcode_width) / 2 * unit_mm
        y = label_settings.LABEL_HEIGHT - 12

        c.drawImage(barcode_reader, x, y * unit_mm, width=barcode_width * unit_mm, preserveAspectRatio=True)

        c.setFillColor(label_settings.TEXT_COLOR)
        c.setFont(font_name, label_settings.FONT_SIZE_DESCRIPTION)
        c.drawString(10 * unit_mm, 10 * unit_mm, description)
        c.setFont(font_name, label_settings.FONT_SIZE_SUPPLIER)
        c.drawString(10 * unit_mm, 7 * unit_mm, f"Suppl.Art: {supplier_article}")
        c.setFont(font_name, label_settings.FONT_SIZE_INBOUND)
        c.drawString(10 * unit_mm, 4 * unit_mm, f"Inbound: {inbound_number}")
        c.setFont(font_name, label_settings.FONT_SIZE_DATE)
        c.drawString(10 * unit_mm, 1 * unit_mm, f"Date: {current_date}")

        c.showPage()
        c.save()

        if not os.path.exists(pdf_path):
            raise RuntimeError("PDF werd niet opgeslagen")

        log(f"PDF gegenereerd: {pdf_path}")

        # Openen via standaard PDF-viewer
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
