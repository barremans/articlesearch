# ======================================
# 🕒 ui_timings.py — Urenregistratie Downloader + Verwerker (V17.5)
# ======================================

import sys, os, re, shutil, tempfile, traceback, logging, subprocess
from datetime import datetime, timedelta
import pandas as pd
import msal
from office365.sharepoint.client_context import ClientContext
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QLineEdit,
    QMessageBox, QTextEdit, QProgressBar, QListWidget, QListWidgetItem,
    QHBoxLayout, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal

# ======================================
# 🪵 LOGGING
# ======================================
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler("debug_log.txt", mode="w", encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
logger.addHandler(fh)
logger.addHandler(ch)

def safe_log(msg, level="info"):
    clean = re.sub(r"[^\x00-\x7F]+", "", str(msg))
    getattr(logging, level)(clean)

# ======================================
# 🧩 HULPFUNCTIES
# ======================================
def parse_excel_time(v):
    if pd.isna(v) or str(v).strip() == "":
        return None
    v = str(v).strip()
    for fmt in ("%H:%M:%S", "%H:%M"):
        try:
            t = datetime.strptime(v, fmt)
            return datetime(2000, 1, 1, t.hour, t.minute, t.second)
        except ValueError:
            continue
    return None

def bereken_uren(row):
    try:
        s, e = parse_excel_time(row.get("Starttijd")), parse_excel_time(row.get("Eindtijd"))
        if not s or not e:
            return 0.0
        diff = (e - s).total_seconds() / 3600
        if diff < 0:
            diff += 24
        return round(diff, 2)
    except Exception as ex:
        safe_log(f"bereken_uren fout: {ex}", "debug")
        return 0.0

def maak_overzicht(df, kolom_dag="Dag"):
    dagen = ["Ma", "Di", "Wo", "Do", "Vr", "Za", "Zo"]
    if df.empty or kolom_dag not in df.columns:
        return pd.DataFrame(columns=["Naam", *dagen, "Totaal"])
    g = df.groupby(["Naam", kolom_dag], as_index=False)["Uren_gewerkt"].sum()
    p = (
        g.pivot(index="Naam", columns=kolom_dag, values="Uren_gewerkt")
        .fillna(0)
        .reindex(columns=dagen, fill_value=0)
    )
    p["Totaal"] = p.sum(axis=1).round(2)
    return p.reset_index()

# ======================================
# 📘 WEEKDATA / TIMINGS
# ======================================
class WeekDataProcessor:
    dag_map = {
        "Monday": "Ma", "Tuesday": "Di", "Wednesday": "Wo", "Thursday": "Do",
        "Friday": "Vr", "Saturday": "Za", "Sunday": "Zo"
    }

    def parse_datum(self, v):
        if pd.isna(v) or str(v).strip() == "":
            return pd.NaT
        try:
            if isinstance(v, (int, float)) and v > 30000:
                return datetime(1899, 12, 30) + timedelta(days=float(v))
            return pd.to_datetime(v, errors="coerce", dayfirst=False)
        except Exception:
            return pd.NaT

    def schoon(self, df):
        df = df.copy()
        df.columns = [c.strip() for c in df.columns]
        if "Datum" not in df:
            df["Datum"] = None
        if "Dag" not in df:
            df["Dag"] = ""
        df["Datum"] = df["Datum"].apply(self.parse_datum)
        df["Dag_Origineel"] = df["Dag"].map(self.dag_map).fillna(df["Dag"])
        df["Uren_gewerkt"] = df.apply(bereken_uren, axis=1)
        return df

    def combineer(self, df):
        df = df.copy()
        for c in ["Starttijd", "Eindtijd"]:
            if c not in df:
                df[c] = None

        def minuten(t):
            t = parse_excel_time(t)
            return t.hour * 60 + t.minute if t else None

        df["Start_min"] = df["Starttijd"].apply(minuten)
        df["Eind_min"] = df["Eindtijd"].apply(minuten)
        df = df[df["Start_min"].notna() & df["Eind_min"].notna()]
        if df.empty:
            safe_log("⚠️ Geen geldige regels in combineer()", "warning")
            return pd.DataFrame()

        res = []
        for (naam, datum, dag), grp in df.groupby(["Naam", "Datum", "Dag_Origineel"], dropna=False):
            tijden = sorted(zip(grp["Start_min"], grp["Eind_min"]))
            comb = []
            for s, e in tijden:
                if not comb or s > comb[-1][1]:
                    comb.append([s, e])
                else:
                    comb[-1][1] = max(comb[-1][1], e)
            tot = sum(e - s for s, e in comb)
            res.append(
                {
                    "Naam": naam,
                    "Datum": datum,
                    "Dag": dag,
                    "Uren_gewerkt": round(tot / 60, 2),
                    "Eerste_start": f"{comb[0][0]//60:02}:{comb[0][0]%60:02}",
                    "Laatste_eind": f"{comb[-1][1]//60:02}:{comb[-1][1]%60:02}",
                    "Aantal_regels": len(grp),
                    "Intervallen": ", ".join(
                        f"{s//60:02}:{s%60:02}-{e//60:02}:{e%60:02}" for s, e in comb
                    ),
                }
            )
        return pd.DataFrame(res)

    def verwerk(self, df):
        df = self.schoon(df)
        comb = self.combineer(df)
        if "Dag" not in comb:
            comb["Dag"] = comb.get("Dag_Origineel", "")
        ov = maak_overzicht(comb, "Dag")
        return df, comb, ov

class TimingsProcessor(WeekDataProcessor):
    pass

# ======================================
# 🔄 SHAREPOINT
# ======================================
class SharePointWorker(QThread):
    message = Signal(str)
    done = Signal(bool)
    files_list = Signal(list)
    progress = Signal(int)

    def __init__(self, mode="list", gekozen=None, auto_open=False):
        super().__init__()
        self.mode = mode
        self.gekozen = gekozen
        self.auto_open = auto_open
        self.download_dir = r"C:\temp"
        os.makedirs(self.download_dir, exist_ok=True)
        self.TENANT = "526b32fa-8cb1-4d6a-9e2b-fd48e2a0e296"
        self.CLIENT = "58f55e10-e404-4307-9fa2-7b40431782fe"
        self.SITE = "https://cgkgroupbvba.sharepoint.com/sites/IT-team"
        self.PATH = "Gedeelde documenten/Applicaties/Evac_App/WeekLogs"

    def run(self):
        try:
            self.message.emit("🌐 Verbinden met Microsoft 365...")
            auth = f"https://login.microsoftonline.com/{self.TENANT}"
            scopes = ["https://cgkgroupbvba.sharepoint.com/.default"]
            app = msal.PublicClientApplication(self.CLIENT, authority=auth)
            res = app.acquire_token_interactive(scopes=scopes)

            class Tok:
                def __init__(self, t):
                    self.tokenType = "Bearer"
                    self.accessToken = t

            tok = Tok(res["access_token"])
            ctx = ClientContext(self.SITE).with_access_token(lambda: tok)

            folder = ctx.web.get_folder_by_server_relative_url(self.PATH)
            files = folder.files
            ctx.load(files)
            ctx.execute_query()

            bestanden = []
            for f in files:
                naam = f.properties.get("Name", "")
                if not naam.lower().startswith("aanwezigheden_"):
                    continue
                lengte = f.properties.get("Length", 0)
                try:
                    lengte = float(lengte)
                except:
                    lengte = 0
                datum = f.properties.get("TimeLastModified")
                if datum:
                    try:
                        d = datetime.fromisoformat(str(datum)).strftime("%d-%m-%Y %H:%M")
                        bestanden.append(f"{naam} ({round(lengte/1024,1)} KB, {d})")
                    except Exception:
                        bestanden.append(f"{naam} ({round(lengte/1024,1)} KB)")
                else:
                    bestanden.append(f"{naam} ({round(lengte/1024,1)} KB)")
            bestanden.sort(reverse=True)
            self.files_list.emit(bestanden)

            if self.mode == "list":
                self.message.emit("📂 Lijst opgehaald — geen download.")
                self.done.emit(True)
                return

            clean = self.gekozen.split()[0]
            sel = next((f for f in files if f.properties["Name"].lower() == clean.lower()), None)
            if not sel:
                self.message.emit(f"❌ Bestand '{clean}' niet gevonden.")
                self.done.emit(False)
                return

            path = os.path.join(self.download_dir, clean)
            self.message.emit(f"⬇️ Downloaden naar {path}...")
            with open(path, "wb") as fh:
                sel.download(fh).execute_query()
            self.progress.emit(50)

            self.message.emit("⚙️ Verwerken van Excel...")
            self.verwerk_excel(path)
            self.progress.emit(100)
            self.done.emit(True)

            if self.auto_open:
                try:
                    os.startfile(path)
                    self.message.emit(f"📂 Excel geopend: {path}")
                except Exception as e:
                    self.message.emit(f"⚠️ Kon Excel niet openen: {e}")

        except Exception as ex:
            safe_log(traceback.format_exc(), "error")
            self.message.emit(f"❌ Fout: {ex}")
            self.done.emit(False)

    def verwerk_excel(self, best):
        tmp = os.path.join(tempfile.gettempdir(), "temp_uren.xlsx")
        shutil.copy(best, tmp)
        xls = pd.ExcelFile(tmp)
        week, time = WeekDataProcessor(), TimingsProcessor()
        with pd.ExcelWriter(tmp, engine="openpyxl", mode="a", if_sheet_exists="replace") as w:
            if "WeekData" in xls.sheet_names:
                df = pd.read_excel(xls, "WeekData")
                a, b, c = week.verwerk(df)
                a.to_excel(w, "WeekData_Debug", index=False)
                c.to_excel(w, "WeekOverview", index=False)
            if "Timings" in xls.sheet_names:
                df = pd.read_excel(xls, "Timings")
                a, b, c = time.verwerk(df)
                b.to_excel(w, "TimingsOverview_Debug", index=False)
                c.to_excel(w, "WeekOverviewTimings", index=False)
        shutil.copy2(tmp, best)
        self.message.emit(f"✅ Verwerkt opgeslagen in: {best}")

# ======================================
# 🖥️ GUI
# ======================================
class ExcelApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Urenregistratie Downloader + Verwerker (V17.5)")
        self.setGeometry(400, 200, 850, 600)
        lay = QVBoxLayout(self)

        lay.addWidget(QLabel("📅 Dubbelklik op een bestand om te downloaden of verwerk via knop:"))
        self.list = QListWidget()
        lay.addWidget(self.list)
        self.list.itemDoubleClicked.connect(self.dubbelklik)

        self.auto_open = QCheckBox("📂 Excel automatisch openen na verwerking")
        self.auto_open.setChecked(True)
        lay.addWidget(self.auto_open)

        row = QHBoxLayout()
        self.btn_ref = QPushButton("🔄 Lijst verversen")
        self.btn_dl = QPushButton("⬇️ Download & Verwerk geselecteerd")
        row.addWidget(self.btn_ref)
        row.addWidget(self.btn_dl)
        lay.addLayout(row)

        self.prog = QProgressBar()
        lay.addWidget(self.prog)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        lay.addWidget(self.log)

        self.btn_ref.clicked.connect(self.laad_bestanden)
        self.btn_dl.clicked.connect(self.start_worker)
        self.worker = None

    def append(self, t):
        self.log.append(t)
        self.log.verticalScrollBar().setValue(self.log.verticalScrollBar().maximum())

    def laad_bestanden(self):
        self.append("🌐 Ophalen lijst...")
        self.worker = SharePointWorker(mode="list")
        self.worker.message.connect(self.append)
        self.worker.files_list.connect(self.toon)
        self.worker.done.connect(self.klaar)
        self.worker.start()

    def toon(self, lst):
        self.list.clear()
        [self.list.addItem(QListWidgetItem(x)) for x in lst]
        self.append(f"✅ {len(lst)} bestanden gevonden.")

    def start_worker(self):
        item = self.list.currentItem()
        if not item:
            QMessageBox.warning(self, "Geen selectie", "Selecteer eerst een bestand.")
            return
        naam = item.text()
        self.append(f"▶️ Download gestart voor {naam}")
        self.worker = SharePointWorker(mode="download", gekozen=naam, auto_open=self.auto_open.isChecked())
        self.worker.message.connect(self.append)
        self.worker.done.connect(self.klaar)
        self.worker.progress.connect(self.prog.setValue)
        self.worker.start()

    def dubbelklik(self, it):
        naam = it.text()
        self.append(f"🖱️ Dubbelklik: {naam}")
        self.worker = SharePointWorker(mode="download", gekozen=naam, auto_open=self.auto_open.isChecked())
        self.worker.message.connect(self.append)
        self.worker.done.connect(self.klaar)
        self.worker.progress.connect(self.prog.setValue)
        self.worker.start()

    def klaar(self, succ):
        if succ:
            QMessageBox.information(self, "Klaar", "✅ Verwerking afgerond.")
        else:
            QMessageBox.critical(self, "Fout", "❌ Er trad een fout op.")

# ======================================
# 🚀 MAIN
# ======================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = ExcelApp()
    w.show()
    sys.exit(app.exec())
