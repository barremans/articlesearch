# 📦 Artikelzoeker – Help

**Versie:** 2.6  
**Laatste update:** mei 2025

Deze applicatie laat je toe om artikels op te zoeken op basis van zoektermen. Resultaten worden overzichtelijk weergegeven, met detailinformatie via dubbelklik of rechtermuisklik. Werkt offline via Windows `.exe` (PyInstaller).

---

## 🔎 Zoekfunctionaliteit

- Voer een **zoekterm** in
- Kies een **zoekmodus**:  
  - `AND` – alle termen moeten voorkomen  
  - `OR` – minstens één term
- Kies of je **voorraad**, **reguliere artikelen** of **beide** wil zien via `Toon voorraad` dropdown:
  - `R` = Regulier
  - `S` = Voorraad
  - `B` = Beide
- Start zoeken via **Zoeken-knop** of `Ctrl+Enter`
- Resultaten verschijnen in een **tabel** met contextmenu
- Eerste rij wordt automatisch geselecteerd

---

## ✳️ Zoektermen en prefixen

### 🔹 Geen prefix
Zoekt op **intern artikelnummer (ItemCode)**  
*Voorbeeld:* `40.3.3.679`

### 🔹 `*` prefix
Zoekt in:
- Itemnaam (SAP)
- Lange omschrijving (`U_LO`)
- Productnaam (WMS)
- Foreign name (`FRGNNAME`)

*Voorbeeld:* `*bocht 90°`

### 🔹 `/` prefix
Zoekt op **leveranciersreferentie (SuppCatNum)**  
*Voorbeeld:* `/2102010900`

### 🔹 `-` prefix
Zoekt op een **exact woord** in:
- Artikelnaam (SAP)
- Productnaam
- Foreign name

De zoekterm moet exact overeenkomen met het volledige woord, hoofdletterongevoelig.

*Voorbeeld:* `-T-stuk`

---

## 🧾 Resultaten

De kolommen in de resultaten **wisselen automatisch** afhankelijk van de `Toon voorraad` instelling:

### 🔸 `R` of `B` → Reguliere artikelen

| Kolom        | Beschrijving                                  |
|--------------|-----------------------------------------------|
| `ItemCode`   | Interne artikelcode                           |
| `ItemName`   | Artikelbeschrijving (SAP)                     |
| `SuppCatNum` | Leveranciersreferentie                        |

### 🔸 `S` → Voorraadweergave

| Kolom               | Beschrijving                              |
|---------------------|-------------------------------------------|
| `ItemCode`          | Artikelcode                               |
| `ItemName`          | Artikelnaam                               |
| `SUPPLIERIDPRODUCT` | Leveranciersreferentie                    |
| `QUANTITY`          | Aantal op voorraad                        |
| `WHSNAME`           | Magazijn                                  |
| `LOCNAME`           | Locatie                                   |
| `QTYMININV`         | Minimum voorraad                          |
| `QTYMAXINV`         | Maximum voorraad                          |
| `SUPPLIERNAME`      | Leveranciernaam                           |
| `PRICESUPPLIER`     | Inkoopprijs leverancier                   |
| `NOTE`              | Opmerkingen                               |

- Hover over een cel toont de volledige inhoud als tooltip
- Resultaatteller toont aantal rijen
- Eerste rij automatisch geselecteerd
- Kolommen schalen automatisch met het venster

---

## 📋 Rijacties

- **Dubbelklik op een rij**:
  - Opent **detailvenster** met uitgebreide gegevens (StockInfo API)
- **Rechtermuisklik op rij**:
  - 📋 Rij kopiëren (alle kolomwaarden)
  - 🔍 Toon detailinformatie
  - 🏷️ Genereer label

---

## 🏷️ Label genereren

Voor elk resultaat kan je labels aanmaken:

- Via rechtermuisklik > **🏷️ Genereer label**
- Of met `Ctrl+L` (op geselecteerde rij)

### Inhoud van het label

- Artikelomschrijving
- Leveranciersartikelnummer
- Inbound-nummer (standaard: `00000000`)
- Artikelcode (optioneel zichtbaar)
- Barcode (Code128, gebaseerd op `ItemCode`)
- Huidige datum

Label wordt als **PDF** gegenereerd en automatisch geopend.

---

## ⚙️ Label-instellingen

Via menu **Instellingen > Label-instellingen...**

Instelbare parameters:

- 📐 Labelformaat: breedte & hoogte (mm)
- 📦 Barcode: positie (top/left) + schaal (breedte/hoogte)
- 🆔 Artikelnummer: positie + lettergrootte
- 📝 Beschrijving: positie + breedte + lettergrootte
- 📅 Datum: positie + lettergrootte
- 🧾 Inboundnummer: positie + lettergrootte
- 📇 Leveranciersref.: positie + lettergrootte

Instellingen worden opgeslagen in `settings.json`  
⚠️ Niet-numerieke waarden geven een foutmelding bij opslaan  
🔁 Wijzigingen zijn direct van kracht – herstart is niet nodig

---

## 🪪 Detailinformatie

Het detailvenster bestaat uit verschillende tabs met hover én dubbelklik-kopieerfunctie:

### 📦 LISA
Voorraad uit LISA-systeem  
Kolommen: `LOCNAME`, `WHSNAME`, `QUANTITY`, `QTYRESERVED`, `QTYMININV`, `QTYMAXINV`

### 🏢 SAP
Voorraad in SAP  
Kolommen: `WHSNAME`, `OnHand`, `IsCommited`, `OnOrder`, `MinStock`, `MaxStock`, `VrijeStock`

### 💰 Aankoop
Aankoopgegevens (`PURCH`)  
Kolommen: `Price`, `Currency`, `BuyUnitMsr`, `NumInBuy`, `PurPackMsr`, `PurPackUn`, `LastPurPrc`

### 💸 Verkoop
Verkoopgegevens (`SALES`)  
Kolommen: `Price`, `Currency`, `SalUnitMsr`, `NumInSale`, `SalPackMsr`, `SalPackUn`

### 📄 Laatste aankoop
Recente aankopen (`RET`)  
Kolommen: `DocNum`, `DocDate`, `ItemCode`, `Dscription`, `Quantity`, `ShipDate`, `VendorNum`, `BaseCard`, `CardName`, `WhsName`

### 🚚 Logistiek
Logistieke info (`LOG`) – zonder velden zoals `validFor`, `frozenFor`, etc.

### 🖼 Afbeelding
Toont afbeelding of PDF thumbnail  
Met weblink + uploadmogelijkheid

---

## 🖼 Afbeelding uploaden

Onder tabblad **Afbeelding**:

- Klik op **[Upload nieuw bestand]**
- Selecteer een bestand (PNG, JPG, PDF)
- Vul extra info in:
  - Beschrijving
  - Leveranciersgegevens
  - (Optioneel) weblink

Bestand wordt geconverteerd naar base64 en via de `OITMI` API geüpload.

---

## 🎹 Sneltoetsen

| Toets         | Actie                                      |
|---------------|---------------------------------------------|
| `Ctrl+Enter`  | Zoek uitvoeren                             |
| `Ctrl+L`      | Genereer label van geselecteerde rij       |
| `Ctrl+S`      | Label-instellingen opslaan                 |
| `F1`          | Toon helpvenster                           |
| `Delete`      | Zoekveld + tabel leegmaken + focus input   |
| `Page Up`     | Vorige zoekmodus (AND/OR)                  |
| `Page Down`   | Volgende zoekmodus (AND/OR)                |
| `Esc`         | Sluit detailvenster (focus hersteld naar input) |

---

## ⚙️ Instellingen wijzigen

Via **Instellingen > Instellingen wijzigen...**:

- Omgeving kiezen: `live` of `test`
- Voorraadtype: `R`, `S`, of `B`
- Toon detailvenster als modal (blokkering)
- Instellingen worden bewaard in `settings.json`
- Sommige aanpassingen vereisen herstart

---

## 🛠 Installatie & gebruik

- Applicatie draait als `.exe` (Windows)
- Gemaakt via PyInstaller
- Bestanden in project:
  - `main.py`, `ui_main.py`, `ui_detail.py`, `upload_dialog.py`
  - `label_generator.py`, `label_settings_dialog.py`, `label_settings.py`
  - `help.md`, `settings.json`, `requirements.txt`
  - `assets/`, `css/`, `logs/`, `dist/`
- Logging: `logs/app.log`

---

## 📁 Exporteer & installeer

- Gebruik `build_installer.bat` om build + zip te maken
- Kopieer ZIP naar andere pc/USB
- Installeer via `install_and_run.bat`
- Doelmap = `C:\SearchArticle`

---

## ℹ️ Feedback

> Voor vragen of feedback, contacteer de ontwikkelaar.
