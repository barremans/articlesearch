# 📝 Changelog

## [v6.0.3] - 2025-09-13
### ✨ Nieuw: Open Sales/Purchase — Documents
- Nieuw venster **Open Sales/Purchase — Documents** (menu **Export → Open elements**).
- Beveiligd met wachtwoord (zelfde als BP). **Eénmalige** ingave per sessie; sluiten van het venster vergrendelt opnieuw.
- **Aantal** (voorheen “Key”): keuze **6** of **Anders** (vrij getal). Wordt meegestuurd naar de API.
- **Groepering/sortering** (radio-opties):
  - **CardName** *(standaardlogica)* → groepeer op klant/leverancier; sorteer binnen groep op **Vervaldatum ↑** (oudste eerst), daarna **MaandenOud** met **meer oud eerst** (dus -10 vóór -8).
  - **CardCode** → idem maar gegroepeerd op code.
  - **DocOwner** → groepeer op document-eigenaar; sorteer binnen groep op **Naam** + **Vervaldatum ↑**.
  - **SalesOwner** → groepeer op verkoper; sorteer binnen groep op **Naam** + **Vervaldatum ↑**.
  - **MaandenOud** → sorteer primair op **MaandenOud** (meer negatief eerst), secundair **Vervaldatum ↑**.
- **Tabs & structuur**
  - Visuele scheiding met disabled tabs: **— Verkoop —**, **— Samenvatting —**, **— Aankoop —**.
  - **Verkoop**: OSO → OSDL → OSDP → OSR → OSI (in deze volgorde).
  - **Aankoop**: OPO → OPDL → OPR → OPI (in deze volgorde).
  - Na ophalen wordt tab **OSO** automatisch geselecteerd (fallback: eerste beschikbare).
- **Samenvatting** (met subtabs en sorteerbare kolommen):
  - **Secties (Sales)** en **Secties (Purchase)**: totalen, earliest/latest due, outstanding.
  - **Klanten**: per CardCode/CardName twee kolommen **SalesOpen** en **PurchaseOpen** (klik op headers om ↑/↓ te wisselen).
  - **DocOwner**, **SalesOwner**, **Buyer**: aantallen per verantwoordelijke.
- **Kolommen & layout**
  - Standaardkolommen per sectie:  
    `DocNum, CardCode, CardName, DocDate, DocDueDate, DocTotal, PaidSum, Outstanding, OrderCount, MaandenOud, SalesOwner, DocOwner`
  - **VATNbr** en **DocEntry** worden **verborgen**.
  - Datums in **DD-MM-YYYY**.
  - **CardName breder**, **DocOwner smaller**; automatische kolombreedte (max cap) en herberekening na sorteren.
- **Export**
  - Knoppen **Exporteer…** (huidige tab of samenvatting) en **Exporteer alles** (volledige workbook).
  - Export-bereik: **Huidige tab / Alle tabs / Sales / Purchase**.
  - Bestandsnaam met **datumstempel** (bijv. `OSO_20250914.xlsx`, `OpenSales_20250914.xlsx`, `OpenDocuments_20250914.xlsx`).
  - Standaardmap **Downloads**.
  - Excel via **openpyxl** of **XlsxWriter**; één tab kan ook als **CSV**.
- **Integratie**
  - Nieuw menu **Export** in `ui_main` met item **Open elements** dat het venster opent.
  - Wachtwoord wordt gedeeld met BP-module (zelfde bron).

---

## [V6.0.1] - 2025-09-04
- 🐞 Bugfix: artikel “no dict” error opgelost.
- 🧭 Business Partner (BP)
  - Tab **“Overzicht”** verwijderd.
- 💳 Credit Control
  - **ODPI (Voorschotten), OINV (Facturen), ORIN (Kredietnota’s)** toegevoegd aan lijsten.
  - Kolommen **DPI1/INV1/RIN1** bewust **niet** in de tabellen getoond (blijven in row-payload voor pop-ups).
  - **Dubbelklik-pop-ups** toegevoegd:
    - Orders → **ORDRL** (met groot FreeTxt-veld)
    - Leveringen → **DNL1** (met FreeTxt/LineMemo)
    - Voorschotten → **DPI1** (met FreeTxt/LineMemo)
    - Facturen → **INV1** (met FreeTxt/LineMemo)
    - Kredietnota’s → **RIN1** (met FreeTxt/LineMemo)
  - Pop-ups blijven correct werken na sorteren (row-payload aan kolom 0 bevestigd via `Qt.UserRole`).
- 🔒 UI & security
  - **Debug-knop en debugpaneel** uit de Credit Control-tab verwijderd.
  - Wachtwoordslot blijft behouden; “Vergrendel opnieuw” blijft beschikbaar.

## [V6.0.0] - 2025-08-29
- toevoeging BusinessPartner zoek flow
- Business partner detail fiche toevoeging
- toevoeging credit control data
- voorbereiding voo AI op artikelen

## [v5.1.0] – 2025-07-09
- Aanpassingen op token manager
- voorbereidingen op Business Partner integratie

## [v5.0.2] – 2025-07-09

### 🌍 Meertaligheid & vertalingen
- Toegevoegd: **Taalkeuze (NL/EN)** in het instellingenvenster (`settings_dialog.py`).
- Nieuw: Centrale `translations`-directory met `nl.py` en `en.py` bestanden.
- Labels (bijv. "Update nu") in `ui_main.py` worden nu dynamisch geladen op basis van ingestelde taal.

### ⚙️ Settings verbeteringen
- `settings.json` bevat nu de key `"language"`, standaard ingesteld op `"NL"`.
- `settings.py`: Functies `load_language()` en `save_language()` toegevoegd.
- Automatisch aanvullen van ontbrekende keys bij laden van settings.

### 💡 Code refactor
- `show_settings_dialog` verplaatst naar eigen bestand `settings_dialog.py` voor betere structuur en onderhoudbaarheid.
- Oude, dubbele `_show_settings_dialog()` code uit `ui_main.py` verwijderd.

---

## [v5.0.1] – 2025-07-03
- 💡 **UI Verbeteringen & uniformisatie**
  - `ui_po.py` en `ui_so.py` gebruiken nu beide **dynamische headers via `field_labels`** uit `settings.json`, zodat kolomtitels eenvoudig aanpasbaar zijn.
  - Handmatig ophalen van data behoudt ingestelde kolombreedtes (geen automatische resize meer).
  - Standaard kolombreedtes ingesteld voor een consistent uiterlijk.
  - Automatisch verwijderen van prefixen (OR, BE en spaties) voor correcte documentnummers.
  - Betere parsing van documentnummers bij doorklik vanuit tabellen.

- ⚡ **Sneltoetsen uitgebreid**
  - `ui_po.py`
    - Ctrl + Enter: ophalen data
    - Page Up / Down: wisselen status (Open/Closed)
    - Alt + A: tab "Aankooporderlijnen"
    - Alt + G: tab "Goederenontvangsten"
    - Esc: venster sluiten
  - `ui_so.py`
    - Ctrl + Enter: ophalen data
    - Esc: venster sluiten

- 🪄 **UI fixes**
  - `ui_po.py` en `ui_so.py` komen nu altijd **boven andere vensters**, ook boven `ui_main` en `ui_detail`.
  - Verbeterde logica voor positioning en focus van child-windows.

- 🗂️ **Instellingen & settings.json**
  - Extra labels toegevoegd in `field_labels`, zodat aanpassingen direct vanuit JSON gebeuren.
  - Kolomkoppen van zowel aankooporderlijnen (`po_por1`) als goederenontvangsten (`po_go`) nu dynamisch.

- 🔧 **Code cleanup**
  - Alle kolomdefinities naar mapping dictionaries verplaatst.
  - Functies opgesplitst en consistent gemaakt.

- 📦 **Structuurwijzigingen & nieuwe modules**
  - Volledige herstructurering van `ui_detail.py` en alle tabs verplaatst naar aparte modules.
  - Nieuwe aparte Python-files per tab:
    - `ui_po.py` (aankooporder-tab)
    - `ui_lastpurchase.py` (laatste aankoop-tab)
  - Nieuwe aparte utility-files:
    - `file_editor_dialog.py`
    - `help_dialogs.py`
    - `settings_dialog.py`
  - `ui_main.py` aangepast voor integratie file editor.
  - Menu rapportering uitgebreid met openstaande issues & requests.

- 🏷️ ATP
  - Sneltoetsen toegevoegd: Ctrl + Enter (ophalen), Page Up/Down (magazijnkeuze).

- 🛒 Aankooporder
  - Sneltoetsen toegevoegd: Ctrl + Enter, Page Up/Down, Alt + A/G, Esc.

---

## [v5.0.0] – 2025-06-29
- 🎉 **Major release**: volledige herstructurering van `ui_detail.py` en alle tabs verplaatst naar aparte modules.
- 📦 Nieuwe aparte Python-files per tab:
  - `ui_lisa.py` (LISA-tab)
  - `ui_sap.py` (SAP-tab)
  - `ui_purchase.py` (Aankoop-tab)
  - `ui_sales.py` (Verkoop-tab)
  - `ui_return.py` (Laatste aankoop-tab)
  - `ui_logistics.py` (Logistiek-tab)
  - `ui_atp.py` (ATP-tab)
- 🏷️ Alle tabs gebruiken nu **headers mapping dictionaries**, zodat kolomkopteksten eenvoudig aanpasbaar zijn.
- ⚡ **Nieuw**: ATP-tab toegevoegd voor realtime beschikbaarheidsplanning, inclusief verkooporders en aankoopbestellingen.
- 💬 ALT-sneltoetsen voor snelle tabnavigatie behouden.

---

## [v4.2.3] – 2025-06-25
- 📋 Verbeterd: kopieerfunctie van verzamellijst (ART/VTA) exporteert nu ook **Outlook- en Word-compatibele HTML-tabellen**.

---

## [v4.2.2] – 2025-06-24
- ➕ Toegevoegd: kolommen **MD_SupplNbr** en **MD_Suppl** aan *PRJ Art.*-tab (VTA).
- 📋 Deze tonen respectievelijk het masterdata leveranciersnummer en -naam per artikel.

---

## [v4.2.1] – 2025-06-21
- 📏 Max- en min-size ingesteld op detail- en projectvenster.
- 🖱️ Dubbelklik op itemcode of omschrijving opent detailvenster.

---

## [v1.4.1] – 2025-06-14
- ➕ Toegevoegd: verzamelknop, leeg-knop en “Selecteer alles” bij Project ART-tab.
- 📋 Verzamelde rijen kunnen worden gekopieerd naar klembord in TSV + HTML.
- ❌ Leeg-knop deselecteert alle checkboxes in ART-tab.
- 🪄 Zelfde verzamel-functionaliteit als in standaard zoekresultaten.
- ♻️ Code opgeschoond en uitgelijnd met hoofdvenster.

---

## [v1.4.0] – 2025-06-14
- 🔍 Nieuw zoektype 'Project' met aangepaste UI.
- 🧠 Tooltip past zich aan op zoektype.
- 🧼 Verbergt zoekmodus en voorraadopties bij projectmodus.
- 📄 Changelog zichtbaar in menu → Help → Changelog.
- 🧾 `help.md` en `changelog.md` verplaatst naar submap `/docs`.
- 📁 FileEditorDialog hergebruikt voor changelog- en helpbestanden.

---

## [v1.3.2] – 2025-06-14
- 🆕 Nieuw: dropdown in instellingen om standaard zoektype te kiezen.
- 🛠️ Verbeterd: artikeltabel toont nu correcte kolommen voor projecten.
- 🐛 Fix: crash opgelost bij dubbele klik zonder selectie.

---

## [v1.3.1] – 2025-06-12
- 🐞 Bug opgelost in labelweergave.
- ⚙️ Verbeterde instellingsdialoog.

---

## [v1.3.0] – 2025-06-01
- 🆕 Nieuw: tabblad VTA toegevoegd aan projectweergave.
- 🎨 Verbeterd: labels in zoekvenster herschikt.

---

## [v1.2.0] – 2025-05-20
- 🚀 Initieel projectzoekvenster toegevoegd.
- 📦 Basis ondersteuning voor ART-gegevens.
