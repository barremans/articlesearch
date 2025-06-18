# SearchArticle.spec
# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

# ✅ Voeg alle datafiles van reportlab toe (fonts, templates, etc.)
reportlab_datas = collect_data_files('reportlab')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('docs/help.md', 'docs'),                 # 📘 Helpbestand
        ('docs/changelog.md', 'docs'),            # 📄 Changelog
        ('settings.json', '.'),                   # ⚙️ App-instellingen
        ('requirements.txt', '.'),                # 📦 Requirements
        ('version.py', '.'),                      # 🔢 Versie info
        ('updater.py', '.'),                      # 🔄 Updater module
        ('assets/spinner.gif', 'assets'),         # ⏳ Loading GIF
        ('assets/*', 'assets'),
        ('assets/css/*', 'assets/css'),           # 🎨 QSS stylesheets
        ('assets/badges/*', 'assets/badges'),
        ('logs/*', 'logs'),                       # 📝 Logbestanden
        ('label/*', 'label'),                     # 🏷️ Label functionaliteit
        ('docs/*', 'docs')                        # 📚 Markdown documentatie
    ] + reportlab_datas,
    hiddenimports=[
        'upload_dialog',
        'oitmi_upload',
        'config',
        'stock_token',
        'auth',
        'token_manager',
        'data_request',
        'stock_info',
        'ui_detail',
        'ui_main',
        'settings',
        'updater',
        'version',
        'label.label_generator',
        'label.label_settings_dialog',
        'bug_report_dialog',
        'test_oitmi_upload',
        'PIL',
        'PIL.Image',
        'requests',
        'packaging',
        'packaging.version',
        'oitmi_token',
        'reportlab',
        'reportlab.pdfgen',
        'reportlab.lib.utils',
        'reportlab.graphics',
        'reportlab.graphics.shapes',
        'reportlab.graphics.renderPDF',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ArticleSearch',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon='C:/PY/cgk tools/cgk-tools/images/CGKico.ico'
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ArticleSearch'
)
