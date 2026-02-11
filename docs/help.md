# 📦 Artikelzoeker – Help

**Versie:** 9.0.5  
**Laatste update:** februari 2026  

De applicatie laat je toe om **artikels**, **projectitems**, **business partners (BP)**, **VTA's**, **openstaande documenten**, **Credit Control (CC BP)** én **Urenregistraties** te consulteren en te verwerken.  
Werkt **online** via de Windows `.exe` (PyInstaller) met **Azure AD-beveiliging**.

---

## 🧭 Navigatie & menu

- **Bestand** → Afsluiten  
- **Instellingen** → Omgeving, (BP/VTA) defaults, QSS-styles, taal, zoektype  
- **Export** →  
  - **Open Elements** – openstaande documenten  
  - **Open Credit Control (CC BP)**  
- **Applicaties** →  
  - **Urenregistratie Downloader + Verwerker** *(nieuw)*  
- **Rapporteren** → Bug/feature melden, open cases  
- **Help** → Help, Over…, Changelog  

> 🔒 Credit Control is enkel beschikbaar **online** en voor gebruikers in de  
> **Azure AD-groep “GPP_Finance”**.

---

## 🔎 Zoeken (hoofdscherm)

1. **Zoekterm** invullen  
2. **Type** kiezen:
   - `Standaard` – zoekt artikels  
   - `Project` – zoekt in projectartikelen  
   - `BP` – zoekt Business Partners (klanten/leveranciers)  
   - `VTA` – zoekt VTA-documenten  
3. **Modus** *(Standaard/BP)*: `AND` of `OR`  
4. **Tweede keuzelijst**:
   - **Standaard**: *Toon voorraad* → `R` (regulier), `S` (voorraad), `B` (beide)  
   - **BP**: *Type* → `""` (alle), `C` (Customer), `S` (Supplier)  
5. Klik op **Zoeken** (`Ctrl + Enter`)

> Bij **VTA** opent automatisch het **VTA-venster**, vult het nummer in en haalt de data op.  
> Het hoofdzoekveld wordt daarna **leeggemaakt** en **focus hersteld**.

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

> Prefixen gelden niet voor **BP** of **VTA**.

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
- Standaard zoektype: Standaard / Project / BP / VTA  
- BP Type default: `""`, `C`, `S`  
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
