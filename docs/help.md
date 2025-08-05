# 📦 Artikelzoeker – Help

**Versie:** 5.0.1

**Laatste update:** juli 2025

Deze applicatie laat je toe om artikels en projectitems efficiënt op te zoeken, met uitgebreide details, voorraadinfo en koppelingen naar aankoop- en verkooporders. Werkt enkel **ONLINE** via de Windows `.exe` (PyInstaller).

---

## 🔎 Zoeken

1. **Voer een zoekterm in** bovenaan
2. **Kies type zoekopdracht:**
   - `Standaard`: zoekt artikels
   - `Project`: zoekt in projectartikelen
3. **Selecteer modus** (enkel bij standaard):
   - `AND` = alle woorden aanwezig
   - `OR` = minstens één woord
4. **Voorraadweergave:** R (regulier), S (voorraad), B (beide)
5. **Start met Zoeken** (`Ctrl + Enter`)

Resultaten verschijnen in een tabel, eerste rij is automatisch geselecteerd. Dubbelklik of rechtermuisklik voor meer acties.

---

## ✳️ Zoektermen & prefixen

| Prefix | Zoekveld                         | Voorbeeld    |
|----------|---------------------------------|--------------|
| *geen* | Artikelcode (ItemCode)         | `41.1.1`    |
| `*`    | Omschrijving, lange omschrijving, foreign name | `*bocht`    |
| `/`    | Leveranciersreferentie (SuppCatNum) | `/2109009` |
| `-`    | Exact woord in naam/foreign name | `-T-stuk`  |

---

## 🧾 Resultatenkolommen

### Standaard (R/B)

| Kolom       | Omschrijving                |
|-------------|-----------------------------|
| `ItemCode`  | Interne code                |
| `ItemName`  | SAP-beschrijving           |
| `SuppCatNum`| Leveranciersreferentie    |

### Voorraad (S)

| Kolom             | Omschrijving              |
|-------------------|---------------------------|
| `ItemCode`        | Artikelcode             |
| `ItemName`        | Artikelnaam            |
| `SUPPLIERIDPRODUCT` | Leveranciersref.     |
| `QUANTITY`       | Voorraad                 |
| `WHSNAME`        | Magazijn              |
| `LOCNAME`        | Locatie               |
| `QTYMININV`     | Minimumvoorraad    |
| `QTYMAXINV`     | Maximumvoorraad   |
| `SUPPLIERNAME` | Leveranciernaam    |
| `PRICESUPPLIER`| Inkoopprijs         |
| `NOTE`          | Opmerkingen       |

### Project

| Kolom        | Omschrijving                                |
|--------------|---------------------------------------------|
| `Artikelnummer` | Projectartikelcode                   |
| `SupplNbr`   | Leveranciersref. project              |
| `PrefSuppl`  | Voorkeursleverancier               |
| `Gecert.`    | Gecertificeerd (Y/N)              |
| `Omschrijving`| Projectomschrijving              |
| `Leverancier`| Leverancier uit document       |
| `PurchNbr`   | Bestelnummer gekoppeld      |
| `MD_SupplNbr`| Masterdata leveranciersref. |
| `MD_Suppl`   | Masterdata leveranciernaam |

---

## 📋 Acties per rij

- **Dubbelklik** → detailvenster
- **`Ctrl + O`** → open geselecteerde rij
- **Rechtsklik** → contextmenu:
  - 📋 Kopiëren
  - 🔍 Detail tonen
  - 🏷️ Label genereren

---

## 🏷️ Label

- **Sneltoets:** `Ctrl + L`
- Wordt automatisch gegenereerd als PDF
- Instellingen: via **Instellingen > Label-instellingen**

---

## 🪪 Detailvenster

Tabs met uitgebreide informatie. Dubbelklik op een cel kopieert de rij.

| Tab               | Info                               | Sneltoets |
|------------------|----------------------------------|-----------|
| 📦 LISA         | LISA-voorraad                    | `Alt + L` |
| 🏢 SAP          | SAP-voorraad en vrije stock | `Alt + S` |
| 💰 Aankoop      | Aankoopinfo, linkt naar PO's  | `Alt + A` |
| 💸 Verkoop      | Verkoopinfo, linkt naar SO's | `Alt + V` |
| 🚚 Logistiek    | Technische/logistieke data  | `Alt + G` |
| 📄 Laatste aankoop | Recente inkoop            | `Alt + R` |
| 🖼️ Afbeelding  | Afbeeldingen en uploads    | `Alt + F` |
| ⚡ ATP          | Beschikbaarheidsplanning   | `Alt + T` |

---

## 🖼 Afbeelding uploaden

1. Open detail > tab 🖼️ Afbeelding
2. Klik **Upload nieuwe aanpassingen**
3. Vul velden (beschrijving, vendor, link)
4. Selecteer bestand (PNG/JPG/PDF)
5. Automatische conversie & upload via OITMI API
6. Vernieuwde afbeelding verschijnt direct

---

## ⚡ ATP

- Selecteer magazijn
- Klik **Data ophalen**
- Zicht op verkoop- en aankooporders
- Beschikbaarheden vetgedrukt
- Aankoopregels = lichtgroen

---

## 🎹 Sneltoetsen

| Toets         | Actie                         |
|---------------|-----------------------------|
| `Ctrl + Enter` | Zoek of data ophalen  |
| `Ctrl + L`    | Label genereren      |
| `Ctrl + O`    | Detail openen        |
| `Delete`      | Zoekveld + tabel leeg |
| `Esc`         | Venster sluiten       |
| `F1`          | Help openen           |
| `Alt + L`     | Tab LISA             |
| `Alt + S`     | Tab SAP            |
| `Alt + A`     | Tab Aankoop       |
| `Alt + V`     | Tab Verkoop       |
| `Alt + G`     | Tab Logistiek     |
| `Alt + R`     | Tab Laatste aankoop |
| `Alt + F`     | Tab Afbeelding    |
| `Alt + T`     | Tab ATP          |
| `Alt + M`     | Bug/feature melden |
| `Alt + H`     | Menu Help       |
| `Alt + O`     | Over-venster   |

---

## ⚙️ Instellingen

- **Omgeving:** live/test
- **Voorraad:** R/S/B
- **Detail als modal:** ja/nee
- **Zoektype standaard:** Standaard/Project
- **Tabs volgorde aanpassen:** drag & drop
- Configuratie in `settings.json`

---

## 🔄 Updates

- Automatische check bij opstart
- Melding in **Over…**
- **Update nu** opent browser naar nieuwste versie
- Instellingen blijven bewaard

---

## 🛠 Installatie

- Windows `.exe` via PyInstaller
- Structuur:
  - `ui_main.py`, `ui_detail.py`, ...
  - Modules: `ui_lisa.py`, `ui_sap.py`, `ui_purchase.py`, `ui_sales.py`, `ui_lastpurch.py`, `ui_logistics.py`, `ui_atp.py`, `ui_po.py`, `ui_so.py`, `oitmi_upload.py`, ...
  - `assets/`, `docs/`, `label/`, `logs/`
- Logs in `logs/app.log`

---

## 📁 Installer

- Bouw via `build_installer.bat` (Inno Setup)
- Installer: `ArticleSearchSetup_%VERSIE%.exe`
- Standaard pad: `C:\ArticleSearch`

---

## 🐞 Bug of feature melden

- **Via menu Rapporteren**
- Kies type: Bug of Feature
- Beschrijf probleem of wens
- Na verzenden wordt GitHub issue aangemaakt

---

## ℹ️ Contact

Voor vragen of feedback: contacteer de ontwikkelaar.
