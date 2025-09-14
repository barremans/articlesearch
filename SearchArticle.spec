# SearchArticle.spec  V6.x
# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_all

# Pandas assets zonder tests
pandas_datas, pandas_binaries, pandas_hidden = collect_all("pandas")
pandas_hidden = [h for h in pandas_hidden if not h.startswith("pandas.tests")]

# Zorg dat de VC++ runtime naast python312.dll in _internal staat
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
        extra_bins.append((p, "_internal"))  # ⬅️ belangrijk

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=pandas_binaries + extra_bins,
    datas=pandas_datas,
    hiddenimports=pandas_hidden + ['upload_dialog'],
    excludes=['pandas.tests'],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ArticleSearch',
    icon='assets\\logo.ico',
    console=False,
    disable_windowed_traceback=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='ArticleSearch',  # onedir outputmap
)
