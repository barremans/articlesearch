# 📦 Artikelzoeker – Help

**Versie:** 2.7  
**Laatste update:** mei 2025

Deze applicatie laat je toe om artikels op te zoeken op basis van zoektermen. Resultaten worden overzichtelijk weergegeven, met detailinformatie via dubbelklik, sneltoets of rechtermuisklik. Werkt offline via Windows `.exe` (PyInstaller).

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
*Voorbeeld:* `-T-stuk`

---

## 🧾 Resultaten

De kolommen in de resultaten **wisselen automatisch** afhankelijk van de `Toon voorraad` instelling:

### 🔸 `R` of `B` → Reguliere artikelen

| Kolom        | Beschrijving                     |
|--------------|----------------------------------|
| `ItemCode`   | Interne artikelcode              |
| `ItemName`   | Artikelbeschrijving (SAP)        |
| `SuppCatNum` | Leveranciersreferentie           |

### 🔸 `S` → Voorraadweergave

| Kolom               | Beschrijving                    |
|---------------------|---------------------------------|
| `ItemCode`          | Artikelcode                     |
| `ItemName`          | Artikelnaam                     |
| `SUPPLIERIDPRODUCT` | Leveranciersreferentie          |
| `QUANTITY`          | Aantal op voorraad              |
| `WHSNAME`           | Magazijn                        |
| `LOCNAME`           | Locatie                         |
| `QTYMININV`         | Minimum voorraad                |
| `QTYMAXINV`         | Maximum voorraad                |
| `SUPPLIERNAME`      | Leveranciernaam                 |
| `PRICESUPPLIER`     | Inkoopprijs leverancier         |
| `NOTE`              | Opmerkingen                     |

---

## 📋 Rijacties

- **Dubbelklik op een rij** → opent detailvenster  
- **`Ctrl+O`** → opent ook geselecteerde rij in detailvenster  
- **Rechtermuisklik** →  
  - 📋 Rij kopiëren  
  - 🔍 Detail tonen  
  - 🏷️ Label genereren

---

## 🏷️ Label genereren

- `Ctrl+L` of via contextmenu op rij  
- Label bevat artikelgegevens en wordt als PDF geopend

---

## ⚙️ Label-instellingen

Menu **Instellingen > Label-instellingen...**

Instelbaar:
- Afmetingen, barcodepositie, teksten en lettergroottes
- Wijzigingen worden automatisch toegepast en opgeslagen

---

## 🪪 Detailinformatie

Tabs met info, kopieerbaar via dubbelklik:

| Tab            | Beschrijving                            | Sneltoets |
|----------------|------------------------------------------|-----------|
| 📦 LISA        | Voorraad uit LISA                        | `Alt+L`   |
| 🏢 SAP         | SAP-voorraad (incl. vrije stock)         | `Alt+S`   |
| 💰 Aankoop     | Inkoopgegevens                           | `Alt+A`   |
| 💸 Verkoop     | Verkoopinformatie                        | `Alt+V`   |
| 🚚 Logistiek   | Technische info (excl. 'frozenFor' etc.) | `Alt+G`   |
| 📄 Laatste aankoop | Recente leveringen                  | `Alt+R`   |
| 🖼️ Afbeelding  | Geüploade afbeelding + uploadfunctie     | `Alt+F`   |

---

## 🖼 Afbeelding uploaden

- Via tab **Afbeelding**  
- Selecteer lokaal bestand  
- Voeg beschrijving en leveranciersdata toe  
- Bestand wordt als PNG geüpload via OITMI API

---

## 🎹 Sneltoetsen

| Toets         | Actie                                      |
|---------------|---------------------------------------------|
| `Ctrl+Enter`  | Zoek uitvoeren                             |
| `Ctrl+L`      | Genereer label van geselecteerde rij       |
| `Ctrl+O`      | Open geselecteerde rij (detailvenster)     |
| `Ctrl+S`      | Label-instellingen opslaan                 |
| `F1`          | Toon helpvenster                           |
| `Delete`      | Zoekveld + tabel leegmaken + focus input   |
| `Esc`         | Sluit detail- of uploadvenster             |
| `Alt+B`       | Open menu **Bestand**                      |
| `Alt+X`       | Selecteer **Afsluiten** in Bestand-menu    |
| `Alt+I`       | Open menu **Instellingen**                 |
| `Alt+K`       | Kies omgeving (test/live)                  |
| `Alt+W`       | Instellingen wijzigen                      |
| `Alt+L`       | Label-instellingen / tab 📦 LISA           |
| `Alt+S`       | Tab 🏢 SAP                                 |
| `Alt+A`       | Tab 💰 Aankoop                             |
| `Alt+V`       | Tab 💸 Verkoop                             |
| `Alt+G`       | Tab 🚚 Logistiek                           |
| `Alt+R`       | Menu **Rapporteren** / tab 📄 Laatste      |
| `Alt+M`       | Bug of feature melden                      |
| `Alt+H`       | Open menu **Help**                         |
| `Alt+E`       | Toon helpvenster                           |
| `Alt+O`       | Toon over-venster                          |
| `Alt+F`       | Tab 🖼️ Afbeelding                          |

---

## ⚙️ Instellingen wijzigen

Via **Instellingen > Instellingen wijzigen...**

- Omgeving kiezen: `live` of `test`
- Voorraadtype: `R`, `S`, of `B`
- Toon detailvenster als modal (blokkering)
- Instellingen worden bewaard in `settings.json`

---

## 🔄 Bijwerken

De applicatie controleert automatisch of er een nieuwere versie beschikbaar is.

- Als er een update is, wordt de knop **Update nu** geactiveerd in het `? > Over...` venster
- Klikken opent het nieuwste ZIP-bestand in je browser

---

## 🛠 Installatie & gebruik

- Applicatie draait als `.exe` (Windows)
- Gemaakt via PyInstaller
- Bestanden in project:
  - `main.py`, `ui_main.py`, `ui_detail.py`, `test_oitmi_upload.py`
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

---

## 🐞 Bug of Feature melden

Je kan fouten of verbetersuggesties rechtstreeks doorgeven via het menu **Rapporteren > Bug of feature melden...**

### 🔧 Types meldingen

- **Bugmelding** → opent een GitHub Issue
- **Feature-aanvraag** → opent een Pull Request in de repo

### 📋 Invoervelden

- Naam van melder
- Type melding (bug of feature)
- Beschrijving

Na verzending krijg je een bevestiging met de link naar GitHub

### 🎯 Bestandsstructuur

- Bugmeldingen: `bugs/bug-xxxx.md`
- Features: `features/feature-xxxx.md` + PR naar `main`
