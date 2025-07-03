# 📦 Artikelzoeker – Help

**Versie:** 5.0.1

**Laatste update:** juli 2025

Deze applicatie laat je toe om artikels op te zoeken op basis van zoektermen. Resultaten worden overzichtelijk weergegeven, met detailinformatie via dubbelklik, sneltoets of rechtermuisklik. Werkt enkel **ONLINE** via een Windows `.exe` (gemaakt met PyInstaller).

---

## 🔎 Zoekfunctionaliteit

1. **Voer een zoekterm in**
2. **Kies een zoekmodus:**
   - `AND` – alle woorden moeten voorkomen
   - `OR` – minstens één woord
3. **Kies welk type artikelen je wil zien** via de dropdown **Toon voorraad**:
   - `R` = Reguliere artikelen
   - `S` = Voorraad-weergave
   - `B` = Beide
4. **Start de zoekopdracht** met de knop **Zoeken** of `Ctrl + Enter`
5. Resultaten verschijnen in een **tabel** met contextmenu
6. De eerste rij wordt automatisch geselecteerd

---

## ✳️ Zoektermen en prefixen

### Geen prefix
Zoekt op **intern artikelnummer (ItemCode)**  
Voorbeeld: `41.1.1`

### `*` prefix
Zoekt in:
- Itemnaam (SAP)
- Lange omschrijving (`U_LO`)
- Productnaam (WMS)
- Foreign name (`FRGNNAME`)

Voorbeeld: `*bocht`

### `/` prefix
Zoekt op **leveranciersreferentie (SuppCatNum)**  
Voorbeeld: `/2109009`

### `-` prefix
Zoekt op een **exact woord** in:
- Artikelnaam (SAP)
- Productnaam
- Foreign name

Voorbeeld: `-T-stuk`

---

## 🧾 Resultaten

De kolommen in de resultaten **passen zich automatisch aan** aan de instelling “Toon voorraad”:

### `R` of `B` → Reguliere artikelen

| Kolom        | Beschrijving               |
|---------------|---------------------------|
| `ItemCode`    | Interne artikelcode       |
| `ItemName`    | Artikelbeschrijving (SAP) |
| `SuppCatNum`  | Leveranciersreferentie    |

### `S` → Voorraadweergave

| Kolom              | Beschrijving           |
|--------------------|------------------------|
| `ItemCode`         | Artikelcode            |
| `ItemName`         | Artikelnaam           |
| `SUPPLIERIDPRODUCT` | Leveranciersreferentie |
| `QUANTITY`        | Aantal op voorraad     |
| `WHSNAME`         | Magazijn             |
| `LOCNAME`         | Locatie              |
| `QTYMININV`      | Minimum voorraad    |
| `QTYMAXINV`      | Maximum voorraad   |
| `SUPPLIERNAME`   | Leveranciernaam    |
| `PRICESUPPLIER` | Inkoopprijs leverancier |
| `NOTE`           | Opmerkingen         |

### Projectmodus (`Project` zoektype)

| Kolom         | Beschrijving                                                   |
|---------------|---------------------------------------------------------------|
| `Artikelnummer` | Artikelcode in projectcontext                                |
| `SupplNbr`    | Leveranciersreferentie uit projectgegevens                     |
| `PrefSuppl`   | Voorkeursleverancier                                           |
| `Gecert.`     | Gecertificeerd artikel (Y/N)                                   |
| `Omschrijving`| Artikel- of serviceomschrijving                                |
| `Leverancier` | Leverancier uit het projectdocument                            |
| `PurchNbr`    | Documentnummer van gekoppelde bestelling                       |
| `MD_SupplNbr` | Masterdata leveranciersnummer uit `LART`                       |
| `MD_Suppl`    | Masterdata leverancier (naam) uit `LART`                       |

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

De detailweergave is opgesplitst in **aparte tab-modules**, elk met aanpasbare kolomkoppen via mapping dictionaries in `settings.json`.  
Dubbelklik op een cel kopieert de hele rij naar het klembord.

| Tab             | Beschrijving                                     | Sneltoets |
|-----------------|-------------------------------------------------|-----------|
| 📦 LISA         | Voorraad uit LISA                               | `Alt + L` |
| 🏢 SAP          | SAP-voorraad (inclusief vrije voorraad)        | `Alt + S` |
| 💰 Aankoop      | Inkoopgegevens (inclusief `ui_po.py`)          | `Alt + A` |
| 💸 Verkoop      | Verkoopinformatie (`ui_so.py`)                | `Alt + V` |
| 🚚 Logistiek    | Logistieke en technische info                  | `Alt + G` |
| 📄 Laatste aankoop | Recente leveringen                         | `Alt + R` |
| 🖼️ Afbeelding  | Geüploade afbeeldingen + uploadfunctie         | `Alt + F` |
| ⚡ ATP          | Beschikbaarheidsplanning (ATP)                | `Alt + T` |

> `ui_po.py` en `ui_so.py` maken nu gebruik van dynamische header mappings en verbeterde sneltoetsen.

---

## 🖼 Afbeelding uploaden

1. Ga naar de tab **Afbeelding** in het detailvenster
2. Klik op **Upload nieuwe aanpassingen**
3. Vul de velden in (beschrijving, artikel-ID, vendor-data, weblink)
4. Selecteer een lokaal afbeeldingsbestand (PNG, JPG, enz.)
5. De afbeelding wordt automatisch omgezet naar PNG Base64 en geüpload via de OITMI API
6. Na upload verschijnt de vernieuwde afbeelding direct

---

## ⚡ ATP-tab

- Kies een magazijn in de dropdown
- Klik op **Data ophalen** → laadt verkoop- en aankooporders
- Tabel toont orderregels, klantinformatie, besteld/bevestigd, beschikbaarheden
- Onderaan zie je een teller met aantal verkoop- en aankooporders
- Beschikbaarheidskolommen worden **vet** weergegeven
- Aankoopregels krijgen een lichtgroene achtergrond

---

## 🎹 Globale sneltoetsen

| Toets          | Actie                                 |
|----------------|---------------------------------------|
| `Ctrl + Enter` | Zoekopdracht of data ophalen       |
| `Ctrl + L`     | Genereer label van geselecteerde rij |
| `Ctrl + O`     | Open geselecteerde rij in detailvenster |
| `Ctrl + S`     | Label-instellingen opslaan          |
| `F1`           | Open helpvenster                    |
| `Delete`       | Maak zoekveld en tabel leeg         |
| `Esc`          | Sluit detail-, upload- of PO/SO-venster |
| `Alt + L`      | Tab 📦 LISA                        |
| `Alt + S`      | Tab 🏢 SAP                         |
| `Alt + A`      | Tab 💰 Aankoop (of aankooporderlijnen) |
| `Alt + V`      | Tab 💸 Verkoop                     |
| `Alt + G`      | Tab 🚚 Logistiek                  |
| `Alt + R`      | Tab 📄 Laatste aankoop            |
| `Alt + F`      | Tab 🖼️ Afbeelding                |
| `Alt + T`      | Tab ⚡ ATP                         |
| `Alt + M`      | Bug of feature melden             |
| `Alt + H`      | Open menu Help                    |
| `Alt + E`      | Toon helpvenster                 |
| `Alt + O`      | Toon Over…-venster              |

---

## ⚙️ Instellingen wijzigen

Via **Instellingen > Instellingen wijzigen…**

- **Omgeving kiezen:** `live` of `test`
- **Voorraadtype:** `R`, `S` of `B`
- **Detailvenster als modal tonen:** ja/nee
- Alle instellingen worden bewaard in `settings.json`
- Kolomheaders kunnen eenvoudig aangepast worden via mapping dictionaries

---

## 🔄 Bijwerken

De applicatie controleert automatisch op nieuwe versies via de GitHub-API.

- Je ontvangt een melding in **Help > Over…** als er een update is
- Klik op **Update nu** → opent downloadpagina
- Installeer over bestaande versie; instellingen blijven bewaard

---

## 🛠 Installatie & gebruik

- De applicatie draait op Windows als standalone `.exe` (PyInstaller)
- **Bestandsstructuur:**
  - `main.py`, `ui_main.py`, `ui_detail.py`, …
  - Aparte modules: `ui_lisa.py`, `ui_sap.py`, `ui_purchase.py`, `ui_sales.py`, `ui_return.py`, `ui_logistics.py`, `ui_atp.py`, `ui_po.py`, `ui_so.py`
  - `assets/`, `logs/`, `label/`, `docs/`
- **Logging:** alle meldingen in `logs/app.log`

---

## 📁 Exporteer & installeer

- Gebruik `build_installer.bat` om een Inno Setup-installer te maken
- De `.exe` vind je in `dist/ArticleSearch_%VERSIE%/`
- Installer uitvoeren: `ArticleSearchSetup_%VERSIE%.exe`
- Standaard pad: `C:\ArticleSearch`

---

## ℹ️ Feedback

> Voor vragen of opmerkingen kun je contact opnemen met de ontwikkelaar.

---

## 🐞 Bug of feature melden

Via **Rapporteren > Bug of feature melden…**

1. **Type melding**
    - Bug
    - Feature-aanvraag
2. **Beschrijving** van het probleem of wens

Na verzenden wordt de melding op GitHub aangemaakt.

- **Bugmeldingen:** `bugs/bug-xxxx.md`
- **Feature-aanvragen:** `features/feature-xxxx.md`

---
