# -*- mode: python ; coding: utf-8 -*-
# =============================================================================
# ArticleSearch
# File:    SearchArticle.spec
# Role:    PyInstaller build-specificatie — bundelt main.py + assets/docs
#          (incl. docs/pep_errors.json) tot de ArticleSearch-installer
#          (via build_installer15.bat, Networkmap-patroon).
# Version: 1.2.0
# Author:  Bart Bossuyt
# Changes: 1.2.0 — pep_errors_datas-toevoeging (v1.1.0) teruggedraaid:
#                   ui_peppol.py leest pep_errors.json voortaan uit
#                   docs/pep_errors.json (v2.0.2) i.p.v. de root naast de
#                   exe. De docs/-map wordt al bewezen betrouwbaar
#                   meegekopieerd (zowel via de Tree("docs", ...) hieronder
#                   als via de xcopy-stap in build_installer15.bat, zelfde
#                   pad als docs/changelog.md) — de aparte, ongeteste
#                   Analysis(datas=...)-toevoeging voor een los bestand
#                   naast de exe was hierdoor overbodig én bleek in de
#                   praktijk niet te werken (pep_errors.json kwam niet mee
#                   bij een test-installatie op een andere computer).
# Changes: 1.1.0 — PEP-1: pep_errors.json toegevoegd aan de bundel
#                   (pep_errors_datas), naast de exe (target ".") i.p.v.
#                   onder docs/assets — zodat het bestaande relatieve pad
#                   in ui_peppol.py (Path("pep_errors.json")) ongewijzigd
#                   blijft werken. Voorwaardelijk (os.path.exists-check)
#                   zodat de build niet faalt als het bestand ontbreekt
#                   tijdens lokaal testen. **TERUGGEDRAAID in v1.2.0** —
#                   werkte niet betrouwbaar, zie die changelog-regel.
# Changes: 1.0.0 — Baseline: bestaande functionaliteit vóór introductie
#                   van versiebeheer in commentaar (assets/css qss
#                   gegarandeerd).
# =============================================================================

import os
from PyInstaller.utils.hooks import collect_all, collect_data_files
from PyInstaller.building.datastruct import Tree

# --- MSAL (Azure AD) ---
msal_datas = collect_data_files("msal")
try:
    msal_ext_datas = collect_data_files("msal.extensions")
except Exception:
    msal_ext_datas = []

# --- Pandas zonder tests ---
pandas_datas, pandas_binaries, pandas_hidden = collect_all("pandas")
pandas_hidden = [h for h in pandas_hidden if not h.startswith("pandas.tests")]

# --- VC++ runtime in _internal plaatsen ---
extra_bins = []
windir = os.environ.get("WINDIR", r"C:\Windows")
candidates = [
    os.path.join(windir, "System32", "vcruntime140.dll"),
    os.path.join(windir, "System32", "vcruntime140_1.dll"),
    os.path.join(windir, "System32", "msvcp140.dll"),
    r".\.venv\Scripts\vcruntime140.dll",
    r".\.venv\Scripts\vcruntime140_1.dll",
    r".\.venv\Scripts\msvcp140.dll",
]
for p in candidates:
    if os.path.exists(p):
        extra_bins.append((p, "_internal"))

block_cipher = None

# ✅ Analysis: ALLEEN tuples
a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=pandas_binaries + extra_bins,
    datas=(
        pandas_datas
        + msal_datas
        + msal_ext_datas
    ),
    hiddenimports=[
        *pandas_hidden,
        "upload_dialog",
        "msal",
        # ❌ msal.extensions bestaat NIET als module
        "requests",
        "urllib3",
        "cryptography",
    ],
    excludes=["pandas.tests"],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="ArticleSearch",
    icon=r"assets\logo.ico",
    console=False,
    disable_windowed_traceback=False,
)

# ✅ Tree ALLEEN HIER toevoegen
collect_datas = []

if os.path.isdir("docs"):
    collect_datas.append(
        Tree("docs", prefix="docs", excludes=["**/__pycache__/*"])
    )

if os.path.isdir("assets"):
    collect_datas.append(
        Tree("assets", prefix="assets", excludes=["**/__pycache__/*"])
    )

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    *collect_datas,   # ✅ JUISTE PLEK
    strip=False,
    upx=False,
    name="ArticleSearch",
)
