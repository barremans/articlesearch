# 📦 Artikelzoeker – Help

**Versie:** 2.8.0  
**Laatste update:** juni 2025

Deze applicatie laat je toe om artikels op te zoeken op basis van zoektermen of projecten. Resultaten worden overzichtelijk weergegeven, met detailinformatie via dubbelklik, sneltoets of rechtermuisklik. Werkt enkel **ONLINE** via een Windows `.exe` (gemaakt met PyInstaller).

---

## 🔍 Zoekfunctionaliteit

1. **Voer een zoekterm in** of kies een **project**
2. **Kies een zoekmodus:** `AND` of `OR`
3. **Kies voorraadfilter**: `R`, `S`, of `B` (enkel bij standaard zoektype)
4. **Start zoeken** met knop **Zoeken** of `Ctrl + Enter`
5. Resultaten verschijnen in een **tabel**
6. Tooltip en UI passen zich aan op zoektype
7. Detailweergave via dubbelklik of sneltoets

---

## 🗂️ Zoektype kiezen

Via dropdown **Zoek op**:

- **Standaard** – klassieke artikelzoeker
- **Project** – op basis van projectinformatie  
  → Laadt artikels en VTA-tabblad per project

Bij keuze **Project**:

- Velden “Zoekmodus” en “Toon voorraad” worden verborgen  
- De interface toont een ander venster met tabs:
  - 📋 Projectinfo
  - 📦 Artikels (ART)
  - 📋 VTA-overzicht

---

## 🧾 Projectvenster

Na selectie van een project toont de interface:

### 📋 Projectinfo
Overzicht van basisdata zoals nummer, beschrijving, klantinfo, memo’s

### 📦 Artikels (ART)

| Kolom        | Omschrijving            |
|--------------|-------------------------|
| Relatie      | Relatiecode             |
| CardName     | Leverancier             |
| SuppCatNum   | Leveranciersreferentie  |
| Artikel      | Artikelcode             |
| Omschrijving | Artikelomschrijving     |
| Aantal       | Hoeveelheid             |
| Prijs        | Prijs per stuk          |

Functies:

- ✅ Selecteerbare rijen met checkbox
- 📋 Voeg geselecteerde rijen toe aan verzamelijst
- 👁 Toon verzamelde lijst en kopieer naar klembord
- 🗑 Leeg verzamellijst & deselecteer alles
- 🧠 Tooltip per cel toont inhoud

### 📋 VTA-tab

Bevat info over bestellingen, voorraad en levering.

| Kolommen: | Artikel, omschrijving, benodigd, besteld, leverdatum, locatie, enz. |

---

## 📋 Rijacties (Standaard zoektype)

- **Dubbelklik op een rij** → opent detailvenster  
- **`Ctrl + O`** → detailvenster openen  
- **Rechtermuisklik** → toont:
  - 📋 Rij kopiëren
  - 🔍 Detail tonen
  - 🏷️ Label genereren

---

## 🏷️ Label genereren

- Sneltoets: `Ctrl + L`
- Via contextmenu op geselecteerde rij
- Label bevat artikeldata als PDF

---

## ⚙️ Label-instellingen

Via **Instellingen > Label-instellingen…**

- Positie en grootte van barcode
- Lettertypes en marges
- Aanpassingen worden automatisch toegepast

---

## 🪪 Detailinformatie

Tabs met o.a.:

| Tab              | Beschrijving                          |
|------------------|----------------------------------------|
| 📦 LISA          | Interne voorraadgegevens               |
| 🏢 SAP           | SAP-voorraad                           |
| 💰 Aankoop       | Inkoopdata                             |
| 💸 Verkoop       | Verkoopinformatie                      |
| 🚚 Logistiek     | Technische en logistieke info          |
| 📄 Laatste aankoop | Recente leveringen                   |
| 🖼️ Afbeelding    | Upload en preview van artikelbeelden   |

---

## 🖼 Afbeelding uploaden

1. Ga naar tab **Afbeelding**
2. Klik op **Upload nieuwe aanpassingen**
3. Vul de velden in (beschrijving, artikel-ID, vendor, URL)
4. Selecteer een bestand (PNG, JPG) of geef een URL op
5. Wordt geüpload via OITMI API (Base64)
6. Preview verschijnt automatisch na upload

---

## 🎹 Globale sneltoetsen

| Toets           | Actie                                   |
|-----------------|------------------------------------------|
| `Ctrl + Enter`  | Zoekopdracht uitvoeren                  |
| `Ctrl + L`      | Genereer label                          |
| `Ctrl + O`      | Open detailvenster                      |
| `Ctrl + S`      | Instellingen opslaan                    |
| `F1`            | Open helpvenster                        |
| `Delete`        | Wis zoekveld en tabel                   |
| `Esc`           | Sluit actieve venster                   |
| `Alt + B`       | Open **Bestand**-menu                   |
| `Alt + X`       | Afsluiten via menu                      |
| `Alt + I`       | Instellingen openen                     |
| `Alt + K`       | Kies omgeving                           |
| `Alt + W`       | Instellingen wijzigen                   |
| `Alt + L`       | Tab 📦 LISA of labelinstellingen        |
| `Alt + S`       | Tab 🏢 SAP                               |
| `Alt + A`       | Tab 💰 Aankoop                           |
| `Alt + V`       | Tab 💸 Verkoop                           |
| `Alt + G`       | Tab 🚚 Logistiek                         |
| `Alt + R`       | Tab 📄 Laatste aankoop                   |
| `Alt + F`       | Tab 🖼️ Afbeelding                        |
| `Alt + M`       | Meld bug of feature                     |
| `Alt + H`       | Help-menu                               |
| `Alt + E`       | Helpvenster                             |
| `Alt + O`       | Over…-venster                           |

---

## ⚙️ Instellingen wijzigen

Via **Instellingen > Instellingen wijzigen…**

- 🌍 Omgeving: `live` of `test`
- 🔍 Zoektype: `Standaard` of `Project`
- 📦 Voorraadweergave: `R`, `S`, `B`
- 🪪 Modal detailvenster: aan/uit  
> Instellingen worden opgeslagen in `settings.json`

---

## 📄 Changelog bekijken

Via **Help > Changelog**  
Toont overzicht van versiewijzigingen uit `changelog.md`

---

## 🔄 Bijwerken

- App checkt op nieuwe versies via GitHub API
- Melding verschijnt in **Help > Over…**
- Klik op **Update nu** om nieuwste versie te downloaden
- Update behoudt instellingen

---

## 🛠 Installatie & structuur

- Draait als `.exe` op Windows
- Gemaakt met PyInstaller

**Structuur:**

- `main.py`, `project_ui.py`, `ui_main.py`, `ui_detail.py`
- `settings.json`, `version.py`, `help.md`
- `assets/`, `label/`, `logs/`, `docs/`
- `build_installer.bat`, `export_to_usb3.bat`
- `updater.py`, `token_manager.py`, `data_request.py`
- `label/label_generator.py`, `project_token.py`

---

## 📁 Export & installatie

- `build_installer.bat` maakt een Inno Setup installatiepakket
- `.exe` wordt geplaatst in `dist/ArticleSearch_%VERSIE%`
- Start `ArticleSearchSetup_%VERSIE%.exe` op andere pc's

---

## 🐞 Bug of feature melden

Via **Rapporteren > Bug of feature melden…**

1. Kies type: Bug of Feature
2. Beschrijf het probleem of de wens
3. Wordt verwerkt op GitHub of intern

---

## ℹ️ Feedback

Voor vragen of suggesties, contacteer de ontwikkelaar.
