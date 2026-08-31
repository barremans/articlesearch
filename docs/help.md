# 📦 Artikelzoeker – Help

**Versie:** 15.3.0  
**Laatste update:** augustus 2026  

De applicatie laat je toe om **artikels**, **projectitems**, **business partners (BP)**, **VTA's**, **openstaande documenten**, **Credit Control (CC BP)**, **Productie Stock Overview** én **Urenregistraties** te consulteren en te verwerken.  
Werkt **online** via de Windows `.exe` (PyInstaller) met **Azure AD-beveiliging**.

---

## 🧭 Navigatie & menu

- **Bestand** → Afsluiten  
- **Instellingen** → Omgeving, (BP/VTA/Prod) defaults, QSS-styles, taal, zoektype, datasets beheren  
- **Export** →  
  - **Open Elements** – openstaande documenten  
  - **Open Credit Control (CC BP)**  
  - **Betalingsgedrag...** – gemiddeld betaalgedrag per klant en detail per factuur  
- **Applicaties** →  
  - **Urenregistratie Downloader + Verwerker**  
- **Rapporteren** → Bug/feature melden, open cases  
- **Help** → Help, Over…, Changelog  

> 🔒 Credit Control is enkel beschikbaar **online** en voor gebruikers in de  
> **Azure AD-groep “GPP_Finance”**.

---

## 🔎 Zoeken (hoofdscherm)

1. **Zoekterm** invullen  
2. **Type** kiezen:
   - `Artikel` – zoekt artikels  
   - `Project` – zoekt in projectartikelen  
   - `BP` – zoekt Business Partners (klanten/leveranciers)  
   - `VTA` – zoekt VTA-documenten  
   - `Prod` – toont het **Productie Stock Overview** voor een gekozen dataset *(nieuw)*  
3. **Modus** *(Artikel/BP)*: `AND` of `OR`  
4. **Tweede keuzelijst**:
   - **Artikel**: *Toon voorraad* → `R` (regulier), `S` (voorraad), `B` (beide)  
   - **BP**: *Type* → `""` (alle), `C` (Customer), `S` (Supplier)  
5. Klik op **Zoeken** (`Ctrl + Enter`)

> Bij **VTA** opent automatisch het **VTA-venster**, vult het nummer in en haalt de data op.  
> Het hoofdzoekveld wordt daarna **leeggemaakt** en **focus hersteld**.
>
> Bij **Prod** verschijnt i.p.v. het zoekterm-veld een **dataset-keuzelijst** —
> zie de aparte sectie hieronder.

---

## 🧾 VTA-venster

- Automatisch geopend bij zoektype **VTA**.  
- Toont alle VTA-lijnen met:
  - **Statuskleur**:
    - 🟢 *COMPLETE* → groen met zwarte tekst  
    - 🔴 *Open > 0* → rood met witte tekst  
- **Zoekfunctie** binnen VTA-items (filter op artikel of omschrijving).  
- **Sneltoetsen**:
  - `Ctrl + D` → veld wissen en focus terug  
  - `Ctrl + Enter` → data ophalen  

---

## 🏭 Productie Stock Overview

Zoektype **Prod** — toont het stock-overzicht van alle artikelen in een
gekozen **dataset** (een genoemde, herbruikbare lijst artikelnummers,
bv. "Wekelijkse HDPE" of "Draai"). De resultaten verschijnen **inline in
het hoofdscherm** (geen apart pop-upvenster), in dezelfde resultatentabel
als Artikel/BP — inclusief de "Selectie"-checkboxkolom, dus ook hier kan
je rijen **toevoegen aan de lijst** en kopiëren naar Outlook/Word zoals
gewoonlijk.

### Gebruik
1. Kies **Search-type: Prod**.
2. Kies een **Dataset** in de keuzelijst (naam + eigenaar).
3. Optioneel: kies een **Magazijn** (Alle magazijnen / Algemeen /
   Antwerpen / Miami) — dit wisselt enkel welke Stock-kolom(men) getoond
   worden, **zonder** de data opnieuw op te halen.
4. Klik op **Zoeken** (`Ctrl + Enter`) om de stock-data effectief op te
   halen. De tabel staat standaard gesorteerd op **Art.Nr.**
5. Gebruik het **Filter**-veld om live te filteren op art.nr. of
   omschrijving binnen de al opgehaalde data (geen nieuwe API-call).
6. **Exporteer naar Excel** exporteert de huidige (gefilterde) weergave.

Klik op de kolomkop **"Art.Nr."** of **"Omschrijving"** om te sorteren
(nogmaals klikken keert de richting om) — zelfde principe als bij de
Artikel-tabel.

### Kleurcodering
- 🟢 **Min. SAP > 0** → lichtgroene celachtergrond ("standaard artikel").
- 🔴 **Stock Algemeen < 1** → lichtrode celachtergrond (aandachtspunt).
- 🟡 **Stock vandaag < Min. SAP** → gele celachtergrond (te weinig
  actuele voorraad t.o.v. het ingestelde minimum).

### Dataset-selectie: standaardwaarden
Welke datasets in de keuzelijst verschijnen — en welke standaard
geselecteerd is — hangt af van de instellingen (zie hieronder):
- Een **standaard dataset** ingesteld → die staat automatisch
  geselecteerd (uit de volledige lijst).
- Enkel een **standaard eigenaar** ingesteld (geen dataset) → de
  keuzelijst toont enkel datasets van die eigenaar.
- Geen van beide ingesteld → volledige lijst, geen automatische keuze.

Gedeactiveerde datasets (zie hieronder — "Lock") verschijnen niet in de
keuzelijst.

### Datasets beheren
Via **Instellingen → Datasets beheren...** open je het beheerscherm:
- **Nieuw...** / **Bewerken...** — naam, eigenaar en artikelnummers
  instellen. Plak een lijst artikelnummers (gescheiden door spatie, tab,
  puntkomma, komma of regeleinde, of een mix) — dit wordt **automatisch**
  omgezet naar één lange, komma-gescheiden lijst. De knop
  **"Normaliseren"** doet dit ook manueel voor reeds getypte/geladen
  inhoud.
- **Verwijderen bestaat niet** — vink **"Gedeactiveerd"** aan om een
  dataset niet langer in de keuzelijst te tonen (i.p.v. te verwijderen).
- **Gewijzigd door** en **Gewijzigd op** worden automatisch gevuld —
  respectievelijk je Windows-gebruikersnaam (niet aanpasbaar) en het
  tijdstip van opslaan.

### ⌨️ Sneltoetsen
| Toets          | Actie                                   |
|----------------|------------------------------------------|
| `Ctrl + Enter` | Zoeken (data ophalen voor gekozen dataset) |
| `Ctrl + E`     | Exporteer naar Excel                    |
| `Delete`       | Filter wissen                           |

---

## 🧑‍💼 BP-venster

- Dubbelklik op een BP-resultaat opent het **BP-venster** met:
  - **Contacten**, **Adressen** en **Credit Control**.  
- Credit Control toont na ontgrendeling:
  - **Orders**, **Leveringen**, **Voorschotten**, **Facturen**, **Kredietnota’s**.  
  - Dubbelklik toont onderliggende **detail-lijnen** in pop-upvensters.  

---

## 💳 Credit Control (CC BP)

Open via **Export → Open Credit Control (CC BP)**  

### 🔒 Beveiliging
- Enkel beschikbaar voor gebruikers in **Azure AD-groep “GPP_Finance”**  
- Offline gebruik is niet toegestaan (`OFFLINE_MODE = False`)  
- Geen toegang → duidelijke foutmelding  

### 📊 Functionaliteit
- **Filteropties**, **sortering**, **groepering**  
- **Selectiebeheer** (➕ toevoegen, 📋 tonen, ❌ leegmaken)  
- **Excel-export** (volledige dataset of selectie)  
- **Dynamische kleurcodering**:
  - 🟢 LOW / GREEN  
  - 🟡 MEDIUM / YELLOW  
  - 🟠 HIGH / AMBER  
  - 🔴 CRITICAL / RED  
- **Over kredietlimiet** → visueel rood/groen gemarkeerd  

### ⌨️ Sneltoetsen
| Toets          | Actie              |
|----------------|--------------------|
| `Ctrl + D`     | Filters wissen     |
| `Ctrl + Enter` | Data vernieuwen    |
| `Esc`          | Venster sluiten   |

---

## 💰 Betalingsgedrag & Openstaande Posten

Open via **Export → Betalingsgedrag...**

### 🔒 Beveiliging
- Zelfde toegangsvoorwaarde als Open Elements: enkel voor gebruikers in
  **Azure AD-groep "GPP_Finance"**.
- Offline gebruik is niet toegestaan.

### 📊 Functionaliteit
Het venster bevat twee tabbladen. Er wordt **niets automatisch opgehaald**
bij het openen — klik telkens op **Ophalen** om de gekozen filters te
bevragen.

**Tabblad "Klanten"** *(standaard geopend)* — één rij per klant:
- Filters: **aantal maanden**, **klantcode**, en **betaalgedrag**
  (alle klanten / enkel slechte betalers / enkel op tijd of vroeger)
- Toont o.a. aantal documenten, gemiddeld aantal dagen tot betaling,
  gemiddeld verschil t.o.v. de vervaldatum, totaalbedragen
- **Dubbelklik op een klant** → springt automatisch naar het tabblad
  "Facturen", gefilterd op die klant, en haalt meteen de bijhorende
  facturen op

**Tabblad "Facturen"** — één rij per factuur/voorschot:
- Filters: **aantal maanden**, **klantcode**, en **verschil vervaldatum**
  (alles / enkel te laat betaald / enkel correct betaald)
- Het aantal maanden en de klantcode van het tabblad "Klanten" worden
  automatisch overgenomen naar dit tabblad

**Beide tabbladen:**
- **Zoekbalk** filtert live over alle kolommen
- Klik op een kolomkop om te **sorteren**
- **Exporteer...** (huidig tabblad) of **Exporteer alles** (beide
  tabbladen samen) — kies nadien **CSV**, **Excel (XLSX)**, of **beide**.
  Na het opslaan wordt de map met het bestand automatisch geopend, en de
  laatst gebruikte map wordt onthouden voor de volgende export.

### ⌨️ Sneltoetsen
| Toets            | Actie                          |
|------------------|---------------------------------|
| `Ctrl + Enter`   | Ophalen (actief tabblad)       |
| `Ctrl + E`       | Exporteer... (actief tabblad)  |
| `Alt + 1`        | Wissel naar tabblad "Klanten"  |
| `Alt + 2`        | Wissel naar tabblad "Facturen" |
| `Esc`            | Venster sluiten                |

---

## ⏱️ Urenregistratie Downloader + Verwerker

Open via **Applicaties → Urenregistratie Downloader + Verwerker**

Deze module laat je toe om **urenregistratie-Excelbestanden** van SharePoint te downloaden, automatisch te verwerken en overzichtstabellen te genereren.

---

### 🔐 Authenticatie
- Automatische login via **Azure AD**
- Interactieve Microsoft-login enkel indien nodig
- Eén login per sessie (token refresh automatisch)

---

### 📂 Bestanden ophalen

Klik op **🔄 Lijst verversen**.

#### Sortering
- Bestanden worden **gesorteerd op SharePoint-wijzigingsdatum**
- **Jongste bestanden staan altijd bovenaan**
- Sortering gebeurt **niet** op bestandsnaam

---

### ⭐ Standaardweergave: Top 5
- Standaard worden enkel de **5 meest recente bestanden** getoond
- Ideaal voor dagelijks gebruik

---

### ☑️ Optie: Toon alle bestanden
- Checkbox **“📂 Toon alle bestanden”**
- Toont de **volledige historische lijst**
- Zoekfunctie blijft actief

---

### 🔍 Zoeken
- **Live zoekveld** boven de lijst
- Filtert op:
  - bestandsnaam
  - datumweergave
- Werkt lokaal (geen nieuwe SharePoint-call)

Voorbeelden:
- `01-2026`
- `aanwezigheden`
- `week`

---

### ⬇️ Downloaden & verwerken

Start via:
- **Dubbelklik** op een bestand  
- of **⬇️ Download geselecteerd**

Automatisch:
1. Download naar `C:\temp`
2. Excel opschonen:
   - Lege tabbladen verwijderd
   - Tabblad **WeekTotaal** verwijderd
3. Overzichten aangemaakt:
   - Weekoverzichten
   - Samengevoegde tijdsintervallen
4. Bestand wordt **terug opgeslagen**

Optie:
- **📂 Excel automatisch openen na verwerking**

---

### ⌨️ Sneltoetsen (Urenregistratie)

| Toets | Actie |
|------|------|
| `Esc` | Venster sluiten |
| Dubbelklik | Download & verwerk |

---

## 📑 Open Sales/Purchase — Documents

Open via **Export → Open Elements**

- Beveiligd met wachtwoord (BP-wachtwoord)
- Eénmalige ontgrendeling per sessie
- Groepering, sortering en uitgebreide Excel-export

---

## ✳️ Zoektermen & prefixen (artikels)

| Prefix   | Zoekveld                                       | Voorbeeld |
|----------|------------------------------------------------|----------|
| *(geen)* | Artikelcode (ItemCode)                         | `41.1.1` |
| `*`      | Omschrijving / foreign name                   | `*bocht` |
| `/`      | Leveranciersreferentie (SuppCatNum)            | `/2109009` |
| `-`      | Exact woord                                    | `-T-stuk` |

> Prefixen gelden niet voor **BP**, **VTA** of **Prod**.

---

## 🎹 Algemene sneltoetsen

| Locatie     | Toets          | Actie                    |
|------------|---------------|--------------------------|
| Hoofdscherm | `Ctrl + Enter` | Zoeken                   |
|             | `Delete`       | Zoekveld leegmaken       |
|             | `Esc`          | Venster sluiten          |

---

## ⚙️ Instellingen

- Omgeving: live / test  
- Standaard zoektype: Artikel / Project / BP / VTA / Prod  
- BP Type default: `""`, `C`, `S`  
- **Productie Stock Overview**: standaard dataset, standaard eigenaar
  (filtert de keuzelijst wanneer geen dataset gekozen is; beide zijn
  keuzelijsten, geen vrije tekst), standaard magazijn — plus de knop
  **"Datasets beheren..."**  
- Taal: NL / EN  
- QSS-styles live aanpasbaar  

Instellingen worden opgeslagen in `settings.json`.

---

## 🔄 Updates
- Automatische versiecheck bij opstart
- **Help → Over…** toont huidige versie en updateknop
- Instellingen blijven behouden

---

## 🐞 Bug of feature melden
Via **Rapporteren → Bug of feature melden…**  
Automatische GitHub-issue met logbestand.

---

## ℹ️ Contact
Voor vragen of feedback: contacteer de ontwikkelaar.

© CGK Group
