# articlesearch
# 📦 Artikelzoeker

![Versie](https://img.shields.io/badge/versie-2.6-blue.svg)
![Status](https://img.shields.io/badge/status-actief-brightgreen.svg)
![Laatste update](https://img.shields.io/badge/laatste%20update-mei%202025-lightgrey.svg)

**Offline Windows-applicatie voor het zoeken, bekijken en labelen van artikelen – met voorraaddata, filters, sneltoetsen en detailvensters.**

---

## 🚀 Functies

- Zoek op artikelcode, naam, omschrijving, leveranciersreferentie, enz.
- Kies `AND` of `OR` zoekmodus
- Toon reguliere artikelen, voorraad, of beide
- Dynamische tabelweergave met kolomfiltering
- Detailvenster met tabbladen (SAP, voorraad, aankoop, verkoop, enz.)
- Labelgeneratie (PDF) met barcode
- Werkt volledig offline (.exe via PyInstaller)

---

## 🔎 Zoekfunctionaliteit

- Zoek via invoerveld + keuze uit `AND` / `OR`
- Filter op voorraadtype (`R`, `S`, `B`)
- Start met `Zoeken` of `Ctrl+Enter`
- Eerste resultaat wordt automatisch geselecteerd

### Prefixen

| Prefix | Betekenis                             | Voorbeeld         |
|--------|----------------------------------------|-------------------|
| *(geen)* | Intern artikelnummer (`ItemCode`)     | `40.3.3.679`      |
| `*`    | Naamvelden (SAP, WMS, omschrijving)     | `*bocht 90°`      |
| `/`    | Leveranciersreferentie (`SuppCatNum`)   | `/2102010900`     |
| `-`    | Exact woord in naamvelden              | `-T-stuk`         |

---

## 📊 Zoekresultaten

### `R` of `B` – Reguliere artikelen
| Kolom        | Omschrijving            |
|--------------|--------------------------|
| `ItemCode`   | Artikelcode              |
| `ItemName`   | Artikelnaam (SAP)        |
| `SuppCatNum` | Leveranciersreferentie   |

### `S` – Voorraadweergave
| Kolom               | Omschrijving               |
|---------------------|----------------------------|
| `ItemCode`, `ItemName`, `SUPPLIERIDPRODUCT`, `QUANTITY`, `WHSNAME`, `LOCNAME`, `QTYMININV`, `QTYMAXINV`, `SUPPLIERNAME`, `PRICESUPPLIER`, `NOTE` |

> 🔹 Hover toont volledige inhoud  
> 🔹 Kolommen schalen automatisch  
> 🔹 Resultaatteller actief

---

## 🧾 Rijacties

- **Dubbelklik:** opent detailvenster
- **Rechtermuisklik:**  
  - 📋 Rij kopiëren  
  - 🔍 Toon detail  
  - 🏷️ Genereer label

---

## 🏷️ Labelgeneratie

- Activeer via rechtermuisklik of `Ctrl+L`
- Genereert PDF met:
  - Artikelomschrijving
  - Leveranciersartikelnummer
  - Inboundnummer (`00000000`)
  - Datum
  - Barcode (Code128, `ItemCode`)

### Instellingen aanpassen:
`Instellingen > Label-instellingen...`  
Opslag in `settings.json`, direct actief, geen herstart nodig.

---

## 🪪 Detailvenster

Tabs met kopieerbare cellen:

- **📦 LISA** – Voorraad per locatie
- **🏢 SAP** – SAP voorraadstatus
- **💰 Aankoop** – Inkoopgegevens
- **💸 Verkoop** – Verkoopparameters
- **📄 Laatste aankoop** – Historiek
- **🚚 Logistiek** – Artikeldetails
- **🖼 Afbeelding** – Bestanden en upload

---

## 🖼 Afbeelding uploaden

1. Ga naar tabblad **Afbeelding**
2. Klik **Upload nieuw bestand**
3. Ondersteunde formaten: PNG, JPG, PDF
4. Wordt omgezet naar base64 en geüpload via API (`OITMI`)

---

## 🎹 Sneltoetsen

| Toets         | Actie                                  |
|---------------|------------------------------------------|
| `Ctrl+Enter`  | Zoek uitvoeren                          |
| `Ctrl+L`      | Genereer label                          |
| `Ctrl+S`      | Instellingen opslaan                    |
| `F1`          | Helpvenster openen                      |
| `Delete`      | Zoekveld + tabel leegmaken              |
| `Page Up/Down`| Wissel zoekmodus                        |
| `Esc`         | Sluit detailvenster                     |

---

## ⚙️ Instellingen

`Instellingen > Instellingen wijzigen...`  
Pas aan:
- 🌍 Omgeving: `live` / `test`
- 🏷️ Standaard voorraadtype: `R`, `S`, `B`
- 🪟 Detailvenster als modal?  
> Alles wordt opgeslagen in `settings.json`

---

## 🛠 Installatie

- Windows `.exe` (gemaakt met PyInstaller)
- Belangrijke bestanden:
  - `main.py`, `ui_main.py`, `label_generator.py`, ...
  - `settings.json`, `requirements.txt`
  - Mappen: `assets/`, `css/`, `logs/`, `dist/`

### Log
Bestand: `logs/app.log`

---

## 📦 Export & distributie

1. Gebruik `build_installer.bat` om een ZIP te maken  
2. Kopieer ZIP naar andere pc  
3. Start `install_and_run.bat`  
4. Installatiemap: `C:\SearchArticle`

---

## 📬 Feedback

> 💡 Voor vragen of feedback, contacteer de ontwikkelaar via intern kanaal of e-mail.

---

## 📚 Licentie

Deze applicatie is intern ontwikkeld. Gebruik binnen het bedrijf of gelieerde organisaties is toegestaan volgens de interne afspraken.  
Niet bestemd voor publieke distributie.
