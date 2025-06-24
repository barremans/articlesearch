# 📦 Artikelzoeker – Help

**Versie:** 2.8.0

**Laatste update:** mei 2025

Deze applicatie laat je toe om artikels op te zoeken op basis van zoektermen. Resultaten worden overzichtelijk weergegeven, met detailinformatie via dubbelklik, sneltoets of rechtermuisklik. Werkt enkel **ONLINE** via een Windows `.exe` (gemaakt met PyInstaller).


<!-- De afbeeldingen (badges) moeten zich bevinden in assets/badges/ en alleen met bestandsnaam worden aangeroepen -->
<!--
![Zoeken](Zoeken-AND_OR-lightblue.png) ![Detailweergave](detail.png) ![Label Generatie](label.png) ![Afbeelding Upload](afbeelding.png) ![Auto-Update](auto_update.png)

![Version](version.png) ![Last Update](last_update.png) ![Platform](platform.png) ![Python](python.png) ![PySide6](pyside6.png)
-->
---

## 🔎 Zoekfunctionaliteit

1.  **Voer een zoekterm in**

2.  **Kies een zoekmodus:**

- `AND` – alle woorden moeten voorkomen

- `OR` – minstens één woord

3.  **Kies welk type artikelen je wil zien** via de dropdown **Toon voorraad**:

- `R` = Reguliere artikelen

- `S` = Voorraad-weergave

- `B` = Beide

4.  **Start de zoekopdracht** met de knop **Zoeken** of `Ctrl + Enter`

5.  Resultaten verschijnen in een **tabel** met contextmenu

6.  De eerste rij wordt automatisch geselecteerd

---

## ✳️ Zoektermen en prefixen

### Geen prefix

Zoekt op **intern artikelnummer (ItemCode)**

Voorbeeld: 41.1.1

### `*` prefix

Zoekt in:

- Itemnaam (SAP)

- Lange omschrijving (`U_LO`)

- Productnaam (WMS)

- Foreign name (`FRGNNAME`)

Voorbeeld: \*bocht

### `/` prefix

Zoekt op **leveranciersreferentie (SuppCatNum)**

Voorbeeld: /2109009

### `-` prefix

Zoekt op een **exact woord** in:

- Artikelnaam (SAP)

- Productnaam

- Foreign name

Voorbeeld: -T-stuk

---

## 🧾 Resultaten

De kolommen in de resultaten **aanpassen zich automatisch** aan de instelling “Toon voorraad”:

### `R` of `B` → Reguliere artikelen

| Kolom | Beschrijving |

|----------------|------------------------------------|

| `ItemCode `| Interne artikelcode |

| `ItemName` | Artikelbeschrijving (SAP) |

| `SuppCatNum` | Leveranciersreferentie |

### `S` → Voorraadweergave

| Kolom | Beschrijving |

|---------------------|---------------------------------|

| `ItemCode` | Artikelcode |

| `ItemName` | Artikelnaam |

| `SUPPLIERIDPRODUCT` | Leveranciersreferentie |

| `QUANTITY` | Aantal op voorraad |

| `WHSNAME` | Magazijn |

| `LOCNAME` | Locatie |

| `QTYMININV` | Minimum voorraad |

| `QTYMAXINV` | Maximum voorraad |

| `SUPPLIERNAME` | Leveranciernaam |

| `PRICESUPPLIER` | Inkoopprijs leverancier |

| `NOTE` | Opmerkingen |

### Projectmodus (`Project` zoektype)

| Kolom         | Beschrijving                                                                 |
|---------------|------------------------------------------------------------------------------|
| `Artikelnummer` | Artikelcode in projectcontext                                               |
| `SupplNbr`    | Leveranciersreferentie uit projectgegevens                                   |
| `PrefSuppl`   | Voorkeursleverancier                                                         |
| `Gecert.`     | Gecertificeerd artikel (Y/N)                                                 |
| `Omschrijving`| Artikel- of serviceomschrijving                                              |
| `Leverancier` | Leverancier uit het projectdocument                                          |
| `PurchNbr`    | Documentnummer van gekoppelde bestelling                                     |
| `MD_SupplNbr` | Masterdata leveranciersnummer uit `LART`                                     |
| `MD_Suppl`    | Masterdata leverancier (naam) uit `LART`                                     |

> De kolommen `MD_SupplNbr` en `MD_Suppl` worden opgehaald uit het veld `LART[0]` van elk artikel en g

---

## 📋 Rijacties

- **Dubbelklik op een rij** → opent detailvenster

- **`Ctrl + O`** → opent geselecteerde rij in detailvenster

- **Rechtermuisklik op een rij** → toont contextmenu met:

- 📋 **Rij kopiëren**

- 🔍 **Detail tonen**

- 🏷️ **Label genereren**

---

## 🏷️ Label genereren

- Sneltoets: `Ctrl + L`

- Of via contextmenu op een geselecteerde rij

- Het label bevat artikelgegevens en wordt als PDF geopend

---

## ⚙️ Label-instellingen

Via **Instellingen > Label-instellingen…**

Instelbare opties:

- Afmetingen en positie van barcode

- Teksten en lettergroottes

- Wijzigingen worden automatisch toegepast en opgeslagen

---

## 🪪 Detailinformatie

Tabs met detaildata; dubbelklik op cellen in de tab om de hele rij te kopiëren:

| Tab | Beschrijving | Sneltoets |

|-------------------------|---------------------------------------------|------------|

| 📦 LISA | Voorraad uit LISA | `Alt + L` |

| 🏢 SAP | SAP-voorraad (inclusief vrije voorraad) | `Alt + S` |

| 💰 Aankoop | Inkoopgegevens | `Alt + A` |

| 💸 Verkoop | Verkoopinformatie | `Alt + V` |

| 🚚 Logistiek | Logistieke en technische info (excl. sommige velden) | `Alt + G` |

| 📄 Laatste aankoop | Recente leveringen | `Alt + R` |

| 🖼️ Afbeelding | Geüploade afbeeldingen + uploadfunctionaliteit | `Alt + F` |

---

## 🖼 Afbeelding uploaden

1. Ga naar de tab **Afbeelding** in het detailvenster

2. Klik op **Upload nieuwe aanpassingen**

3. Vul de velden in (beschrijving, artikel-ID, vendor-data, weblink)

4. Selecteer een lokaal afbeeldingsbestand (PNG, JPG, etc.) of geef een URL

5. De afbeelding wordt automatisch omgezet naar PNG Base64 en geüpload via de OITMI API

6. Na een geslaagde upload verschijnt de vernieuwde afbeelding meteen in de tab

---

## 🎹 Globale sneltoetsen

| Toets | Actie |

|----------------|------------------------------------------------------|

| `Ctrl + Enter` | Zoekopdracht uitvoeren |

| `Ctrl + L` | Genereer label van geselecteerde rij |

| `Ctrl + O` | Open geselecteerde rij in detailvenster |

| `Ctrl + S` | Label-instellingen opslaan |

| `F1` | Open helpvenster |

| `Delete` | Maak zoekveld en tabel leeg en focus input |

| `Esc` | Sluit detail- of uploadvenster |

| `Alt + B` | Open menu **Bestand** |

| `Alt + X` | Selecteer **Afsluiten** in **Bestand**-menu |

| `Alt + I` | Open menu **Instellingen** |

| `Alt + K` | Kies omgeving (test/live) |

| `Alt + W` | Open **Instellingen wijzigen…** |

| `Alt + L` | Label-instellingen in menu / tab 📦 LISA |

| `Alt + S` | Tab 🏢 SAP |

| `Alt + A` | Tab 💰 Aankoop |

| `Alt + V` | Tab 💸 Verkoop |

| `Alt + G` | Tab 🚚 Logistiek |

| `Alt + R` | Menu **Rapporteren** / tab 📄 Laatste aankoop |

| `Alt + M` | Bug of feature melden |

| `Alt + H` | Open menu **Help** |

| `Alt + E` | Toon helpvenster |

| `Alt + O` | Toon **Over…**-venster |

| `Alt + F` | Tab 🖼️ Afbeelding |

---

## ⚙️ Instellingen wijzigen

Via **Instellingen > Instellingen wijzigen…**

- **Omgeving kiezen:** `live` of `test`

- **Voorraadtype:** `R`, `S` of `B`

- **Detailvenster als modal tonen:** ja/nee

- Alle instellingen worden bewaard in `settings.json`

---

## 🔄 Bijwerken

De applicatie controleert automatisch op nieuwe versies via de GitHub-API.

- Als er een nieuwe versie beschikbaar is, ontvang je een melding in het venster **Help > Over…**

- Klik op **Update nu** om de nieuwste `.exe` in je browser te openen

- Je installeert gewoon over de bestaande versie; instellingen blijven bewaard

---

## 🛠 Installatie & gebruik

- De applicatie draait op Windows als een standalone `.exe` (gemaakt met PyInstaller)

- **Bestandsstructuur:**

- `main.py`, `ui_main.py`, `ui_detail.py`, …

- `test_oitmi_upload.py` (uploader)

- `data_request.py`, `stock_info.py`

- `updater.py`, `version.py`

- `label/label_generator.py`, `label/label_settings_dialog.py`

- `help.md`, `settings.json`, `requirements.txt`

- Mappen: `assets/`, `assets/css/`, `logs/`, `label/`, `dist/`

- **Logging:** alle logmeldingen vind je in `logs/app.log`

---

## 📁 Exporteer & installeer

- Gebruik `build_installer.bat` om de applicatie te bouwen en een Inno Setup-installer te maken

- Na de build vind je de standalone `.exe` in de map `dist/ArticleSearch_%VERSIE%/`

- Je kunt het installatieprogramma (`ArticleSearchSetup_%VERSIE%.exe`) rechtstreeks uitvoeren op andere PC’s of vanaf een USB-stick

- Standaard installatiepad: `C:\ArticleSearch`

---

## ℹ️ Feedback

> Voor vragen of opmerkingen kun je contact opnemen met de ontwikkelaar.

---

## 🐞 Bug of feature melden

Via het menu **Rapporteren > Bug of feature melden…** kun je een melding maken:

1.  **Type melding**

- Bug

- Feature-aanvraag

2.  **Beschrijving** van het probleem of de wens

Na verzenden wordt er een melding aangemaakt op GitHub.

- **Bugmeldingen** worden opgeslagen onder `bugs/bug-xxxx.md`

- **Feature-aanvragen** komen onder `features/feature-xxxx.md` en leiden tot een pull request naar `main`

---
