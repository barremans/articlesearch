# =============================================================================
# ArticleSearch
# File:    settings_dialog.py
# Role:    Modaal "Instellingen"-venster (QDialog) — omgeving, toon voorraad,
#          detail-als-modal, standaard zoektype, taal, BP-default-type,
#          tab-volgorde, Prod Stock Overview-defaults (dataset/eigenaar/
#          magazijn) + toegang tot het datasets-beheerscherm, Open Elements
#          overview-defaults (input-/outputmap). Ingedeeld in tabbladen per
#          groep (zie 2.0.0).
# Version: 2.0.0
# Author:  Bart Bossuyt
# Changes: 2.0.0 — HERINDELING: het scherm was uitgegroeid tot 1 lange
#                   verticale lijst (Algemeen/BP/Prod/Open Elements
#                   overview/Tab-volgorde allemaal onder elkaar) en werd
#                   daardoor onoverzichtelijk. Herbouwd met een QTabWidget:
#                   elke bestaande groep heeft nu zijn eigen tabblad
#                   ("Algemeen", "Business Partners", "Productie Stock
#                   Overview", "Open Elements overview", "Tab-volgorde") —
#                   1 klik toont enkel de instellingen van die groep, de
#                   andere blijven verborgen i.p.v. mee te scrollen. Elke
#                   groep is opgebouwd via een eigen `_build_xxx_tab()`-
#                   functie, zodat een toekomstige nieuwe groep enkel een
#                   nieuwe builder-functie + 1 `tabs.addTab(...)`-regel
#                   vergt, geen herstructurering van de rest. Functioneel
#                   ongewijzigd: exact dezelfde velden, dezelfde
#                   load_/save_-functies uit settings.py, 1 gedeelde
#                   "Opslaan"-knop onderaan (buiten de tabbladen) die alle
#                   groepen in 1 keer opslaat — zelfde gedrag als voorheen,
#                   enkel de indeling is anders. Vensterbreedte licht
#                   verkleind (420 → 460, hoogte 700 → 560) nu de inhoud
#                   niet langer allemaal onder elkaar staat.
# Changes: 1.4.0 — Open Elements overview: nieuwe sectie met 2 optionele
#                   standaardmappen (input/output, elk met "Bladeren..."),
#                   opgeslagen via settings.py's nieuwe
#                   oeoverview_default_input_folder/
#                   oeoverview_default_output_folder. Leeg blijven is
#                   toegestaan — ui_oeoverview.py valt dan terug op de
#                   laatst gebruikte map (QSettings). Geen validatie dat het
#                   ingevulde pad bestaat: enkel doorklikken via "Bladeren..."
#                   levert altijd een bestaande map op, manueel intikken van
#                   een (nog) niet-bestaand pad wordt niet tegengehouden,
#                   zelfde principe als de bestaande QSS-pad-velden.
# Changes: 1.3.0 — Prod Stock Overview: "Standaard dataset" en "Standaard
#                   eigenaar" zijn nu zuivere keuzelijsten (niet-bewerkbaar,
#                   zelfde stijl als "Standaard magazijn") i.p.v. editable
#                   comboboxen — op vraag van gebruiker ("ddl keuze ipv
#                   input"). De reeds opgeslagen waarde wordt, indien niet
#                   aanwezig in de live opgehaalde lijst (bv. offline, of
#                   een ondertussen gedeactiveerde dataset), alsnog als item
#                   toegevoegd zodat de instelling niet stilzwijgend op ""
#                   terugvalt bij het openen van dit venster.
# Changes: 1.2.0 — Prod Stock Overview: "Prod" toegevoegd aan de "Standaard
#                   zoektype"-dropdown. Nieuwe sectie "Productie Stock
#                   Overview": standaard dataset (combobox, live gevuld via
#                   prod_info.list_datasets() — faalt stil/offline-veilig
#                   als de call niet lukt), standaard eigenaar (combobox,
#                   afgeleid uit dezelfde lijst) en standaard magazijn
#                   (combobox: "", Stock_Algemeen, Stock_Antwerpen,
#                   Stock_Miami). Nieuwe knop "Datasets beheren..." opent
#                   ui_prod_datasets_dialog.ProdDatasetsDialog. Beide
#                   comboboxen zijn editable, zodat de instelling ook
#                   manueel ingevuld kan worden wanneer de datasetlijst
#                   (tijdelijk) niet opgehaald kon worden.
# Changes: 1.1.0 — BUGFIX: dropdown "Standaard zoektype" bood "Standaard"
#                   aan als item, terwijl de combobox in ui_main.py
#                   (self.search_type_select) als itemtekst "Artikel"
#                   gebruikt. Items aangepast naar ["Artikel", "Project",
#                   "BP", "VTA"] zodat de instelling effectief kan matchen.
#                   Zie ook settings.py v1.1.0 (zelfde fix, achterliggende
#                   load/save-functies).
# Changes: 1.0.0 — Baseline: bestaande functionaliteit vóór introductie van
#                   versiebeheer in commentaar. Voorgeschiedenis niet
#                   gedocumenteerd per deelversie — vanaf nu wel.
# =============================================================================

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox, QPushButton,
    QListWidget, QListWidgetItem, QMessageBox, QLineEdit, QFileDialog,
    QTabWidget, QWidget,
)

from settings import (
    load_environment, save_environment,
    load_show_stock, save_show_stock,
    load_detail_modal, save_detail_modal,
    load_default_search_type, save_default_search_type,
    load_tab_order, save_tab_order,
    load_language,
    save_language,
    load_bp_default_type, save_bp_default_type,
    load_prod_default_dataset_name, save_prod_default_dataset_name,
    load_prod_default_dataset_owner, save_prod_default_dataset_owner,
    load_prod_default_warehouse, save_prod_default_warehouse,
    load_oeoverview_default_input_folder, save_oeoverview_default_input_folder,
    load_oeoverview_default_output_folder, save_oeoverview_default_output_folder,
)


def _build_algemeen_tab(env: QComboBox, stock: QComboBox, modal: QCheckBox,
                         search_type_default: QComboBox, language_combo: QComboBox) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)

    layout.addWidget(QLabel("Omgeving:"))
    layout.addWidget(env)
    layout.addWidget(QLabel("Toon voorraad:"))
    layout.addWidget(stock)
    layout.addWidget(modal)
    layout.addWidget(QLabel("Standaard zoektype:"))
    layout.addWidget(search_type_default)
    layout.addWidget(QLabel("Taal:"))
    layout.addWidget(language_combo)
    layout.addStretch()
    return page


def _build_bp_tab(bp_type_default: QComboBox) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)

    layout.addWidget(QLabel("BP Type (default):"))
    layout.addWidget(bp_type_default)
    layout.addStretch()
    return page


def _build_prod_tab(prod_dataset_default: QComboBox, prod_owner_default: QComboBox,
                     prod_warehouse_default: QComboBox, manage_datasets_button: QPushButton) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)

    layout.addWidget(QLabel("Standaard dataset (indien gekozen: automatisch geselecteerd):"))
    layout.addWidget(prod_dataset_default)
    layout.addWidget(QLabel("Standaard eigenaar (filtert de keuzelijst indien geen dataset gekozen is):"))
    layout.addWidget(prod_owner_default)
    layout.addWidget(QLabel("Standaard magazijn (leeg = alle magazijnen):"))
    layout.addWidget(prod_warehouse_default)
    layout.addWidget(manage_datasets_button)
    layout.addStretch()
    return page


def _build_oeoverview_tab(input_row: QHBoxLayout, output_row: QHBoxLayout) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)

    layout.addWidget(QLabel("Standaard inputmap:"))
    layout.addLayout(input_row)
    layout.addWidget(QLabel("Standaard outputmap:"))
    layout.addLayout(output_row)
    layout.addStretch()
    return page


def _build_tab_order_tab(tab_order_list: QListWidget) -> QWidget:
    page = QWidget()
    layout = QVBoxLayout(page)

    layout.addWidget(QLabel("Versleep de rijen om de tab-volgorde te herschikken:"))
    layout.addWidget(tab_order_list)
    return page


def show_settings_dialog(parent):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Instellingen")
    dialog.resize(460, 560)

    layout = QVBoxLayout(dialog)

    # ------------------------------------------------------------------
    # Widgets — Algemeen
    # ------------------------------------------------------------------
    env = QComboBox()
    env.addItems(["live", "test"])
    env.setCurrentText(load_environment())

    stock = QComboBox()
    stock.addItems(["R", "S", "B"])
    stock.setCurrentText(load_show_stock())

    modal = QCheckBox("Toon detail als modal dialoog")
    modal.setChecked(load_detail_modal())

    # Standaard zoektype (moet matchen met de itemtekst in
    # ui_main.py: self.search_type_select.addItems(["Artikel", "Project", "BP", "VTA", "Prod"]))
    search_type_default = QComboBox()
    search_type_default.addItems(["Artikel", "Project", "BP", "VTA", "Prod"])
    search_type_default.setCurrentText(load_default_search_type())

    language_combo = QComboBox()
    language_combo.addItem("Nederlands", "NL")
    language_combo.addItem("English", "EN")
    language_combo.setCurrentText("Nederlands" if load_language() == "NL" else "English")

    # ------------------------------------------------------------------
    # Widgets — Business Partners
    # ------------------------------------------------------------------
    bp_type_default = QComboBox()
    bp_type_default.addItems(["", "C", "S"])
    bp_type_default.setCurrentText(load_bp_default_type())

    # ------------------------------------------------------------------
    # Widgets — Productie Stock Overview
    # ------------------------------------------------------------------
    # Datasets/eigenaars live proberen op te halen — offline-veilig: als de
    # call faalt (geen netwerk/rechten), blijft de keuzelijst beperkt tot
    # "" + de reeds opgeslagen waarde (zie hieronder). Zuivere keuzelijsten
    # (niet-bewerkbaar), zelfde stijl als "Standaard magazijn".
    prod_dataset_names = []
    prod_dataset_owners = []
    try:
        from prod_info import list_datasets
        _datasets = list_datasets()
        prod_dataset_names = sorted({d.get("DS_Name", "") for d in _datasets if d.get("DS_Name")})
        prod_dataset_owners = sorted({d.get("DS_Owner", "") for d in _datasets if d.get("DS_Owner")})
    except Exception:
        pass  # settingsvenster mag nooit crashen op een falende datasetlijst

    current_dataset_default = load_prod_default_dataset_name()
    # Reeds opgeslagen waarde altijd als item beschikbaar houden, ook als de
    # live lijst hem (nog) niet bevat (bv. dataset ondertussen gedeactiveerd,
    # of de lijst kon niet opgehaald worden) — anders valt de instelling
    # stilzwijgend terug op "" bij het openen van dit venster.
    if current_dataset_default and current_dataset_default not in prod_dataset_names:
        prod_dataset_names = sorted(prod_dataset_names + [current_dataset_default])

    prod_dataset_default = QComboBox()
    prod_dataset_default.addItem("")
    prod_dataset_default.addItems(prod_dataset_names)
    prod_dataset_default.setCurrentText(current_dataset_default)

    current_owner_default = load_prod_default_dataset_owner()
    if current_owner_default and current_owner_default not in prod_dataset_owners:
        prod_dataset_owners = sorted(prod_dataset_owners + [current_owner_default])

    prod_owner_default = QComboBox()
    prod_owner_default.addItem("")
    prod_owner_default.addItems(prod_dataset_owners)
    prod_owner_default.setCurrentText(current_owner_default)

    prod_warehouse_default = QComboBox()
    prod_warehouse_default.addItems(["", "Stock_Algemeen", "Stock_Antwerpen", "Stock_Miami"])
    prod_warehouse_default.setCurrentText(load_prod_default_warehouse())

    manage_datasets_button = QPushButton("Datasets beheren...")

    def _open_manage_datasets():
        from ui_prod_datasets_dialog import ProdDatasetsDialog
        ds_dialog = ProdDatasetsDialog(dialog)
        ds_dialog.exec()

    manage_datasets_button.clicked.connect(_open_manage_datasets)

    # ------------------------------------------------------------------
    # Widgets — Open Elements overview
    # ------------------------------------------------------------------
    # Optioneel — leeg = geen vaste standaard, dan valt ui_oeoverview.py
    # terug op de laatst gebruikte map.
    oeoverview_input_edit = QLineEdit()
    oeoverview_input_edit.setText(load_oeoverview_default_input_folder())
    oeoverview_input_edit.setPlaceholderText("Leeg = laatst gebruikte map")

    def _kies_oeoverview_input_folder():
        gekozen = QFileDialog.getExistingDirectory(
            dialog, "Standaard inputmap — Open Elements overview", oeoverview_input_edit.text()
        )
        if gekozen:
            oeoverview_input_edit.setText(gekozen)

    oeoverview_input_browse = QPushButton("Bladeren...")
    oeoverview_input_browse.clicked.connect(_kies_oeoverview_input_folder)
    oeoverview_input_row = QHBoxLayout()
    oeoverview_input_row.addWidget(oeoverview_input_edit)
    oeoverview_input_row.addWidget(oeoverview_input_browse)

    oeoverview_output_edit = QLineEdit()
    oeoverview_output_edit.setText(load_oeoverview_default_output_folder())
    oeoverview_output_edit.setPlaceholderText("Leeg = laatst gebruikte map")

    def _kies_oeoverview_output_folder():
        gekozen = QFileDialog.getExistingDirectory(
            dialog, "Standaard outputmap — Open Elements overview", oeoverview_output_edit.text()
        )
        if gekozen:
            oeoverview_output_edit.setText(gekozen)

    oeoverview_output_browse = QPushButton("Bladeren...")
    oeoverview_output_browse.clicked.connect(_kies_oeoverview_output_folder)
    oeoverview_output_row = QHBoxLayout()
    oeoverview_output_row.addWidget(oeoverview_output_edit)
    oeoverview_output_row.addWidget(oeoverview_output_browse)

    # ------------------------------------------------------------------
    # Widgets — Tab-volgorde
    # ------------------------------------------------------------------
    tab_order_list = QListWidget()
    tab_order_list.setDragDropMode(QListWidget.InternalMove)
    current_order = load_tab_order()
    all_tabs = ["art", "install", "vta", "vta_cert"]

    seen = set()
    for tab in current_order + [t for t in all_tabs if t not in current_order]:
        if tab not in seen:
            tab_order_list.addItem(QListWidgetItem(tab))
            seen.add(tab)

    # ------------------------------------------------------------------
    # Tabbladen samenstellen — nieuwe groep? 1 builder-functie + 1 regel
    # hieronder, geen andere wijziging nodig.
    # ------------------------------------------------------------------
    tabs = QTabWidget()
    tabs.addTab(
        _build_algemeen_tab(env, stock, modal, search_type_default, language_combo),
        "Algemeen",
    )
    tabs.addTab(_build_bp_tab(bp_type_default), "Business Partners")
    tabs.addTab(
        _build_prod_tab(prod_dataset_default, prod_owner_default, prod_warehouse_default, manage_datasets_button),
        "Productie Stock Overview",
    )
    tabs.addTab(
        _build_oeoverview_tab(oeoverview_input_row, oeoverview_output_row),
        "Open Elements overview",
    )
    tabs.addTab(_build_tab_order_tab(tab_order_list), "Tab-volgorde")

    # ------------------------------------------------------------------
    # Opslaan — 1 gedeelde knop buiten de tabbladen, slaat alle groepen
    # in 1 keer op (ongewijzigd gedrag t.o.v. voorheen).
    # ------------------------------------------------------------------
    save = QPushButton("Opslaan")

    def _save_config():
        save_environment(env.currentText())
        save_show_stock(stock.currentText())
        save_detail_modal(modal.isChecked())
        save_default_search_type(search_type_default.currentText())
        save_language(language_combo.currentData())
        save_bp_default_type(bp_type_default.currentText())
        save_prod_default_dataset_name(prod_dataset_default.currentText())
        save_prod_default_dataset_owner(prod_owner_default.currentText())
        save_prod_default_warehouse(prod_warehouse_default.currentText())
        save_oeoverview_default_input_folder(oeoverview_input_edit.text())
        save_oeoverview_default_output_folder(oeoverview_output_edit.text())
        new_order = [tab_order_list.item(i).text() for i in range(tab_order_list.count())]
        save_tab_order(new_order)
        QMessageBox.information(dialog, "Instellingen", "Instellingen opgeslagen.")
        dialog.accept()

    save.clicked.connect(_save_config)

    layout.addWidget(tabs)
    layout.addWidget(save)

    dialog.setLayout(layout)
    dialog.exec()