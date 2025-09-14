# 📦 Artikelzoeker – Help

**Versie:** 6.0.3  
**Laatste update:** september 2025

Deze applicatie laat je toe om **artikels**, **projectitems**, **business partners**, en **openstaande documenten** (sales/purchase) efficiënt te consulteren. Werkt **online** via de Windows `.exe` (PyInstaller).

---

## 🧭 Navigatie & menu

- **Bestand** → Afsluiten  
- **Instellingen** → Omgeving, (BP) type defaults, QSS-styles, …  
- **Rapporteren** → Bug/feature melden, open cases  
- **Help** → Help, Over…, Changelog  
- **Export** → **Open elements** *(nieuw venster voor openstaande documenten)*

---

## 🔎 Zoeken (hoofdscherm)

1. **Zoekterm** invullen.
2. **Type** kiezen:
   - `Standaard` – zoekt artikels
   - `Project` – zoekt in projectartikelen
   - `BP` – zoekt Business Partners (klanten/leveranciers)
3. **Modus** *(Standaard/BP)*: `AND` of `OR`
4. **Tweede keuzelijst**:
   - **Standaard**: **Toon voorraad** → `R` (regulier), `S` (voorraad), `B` (beide)
   - **BP**: **Type** → `""` (alle), `C` (Customer), `S` (Supplier)
5. Start met **Zoeken** (`Ctrl + Enter`)

Resultaten verschijnen in een tabel. Dubbelklik of rechtermuisklik voor meer acties.

---

## 🧑‍💼 BP-venster (samenvatting)

- Dubbelklik op een BP-resultaat opent het **BP-venster** met **Contacten**, **Adressen** en **Credit Control** (beveiligd).
- Credit Control toont na ontgrendeling **Orders**, **Leveringen**, **Voorschotten**, **Facturen**, **Kredietnota’s**.  
  Dubbelklik toont detail-lijnen in pop-up.

---

## 📑 Open Sales/Purchase — Documents *(nieuw)*

Open via **menu: Export → Open elements**.

### 🔒 Beveiliging
- Venster is **vergrendeld** bij openen.
- Wachtwoord is **hetzelfde als BP** (centrale bron).
- **Eénmalig** per sessie; sluiten van dit venster vergrendelt opnieuw.

### 🔢 Aantal
- Kies **6** of **Anders** en vul een vrij getal in.
- Dit aantal wordt meegegeven aan de API. (Indien de endpoint dit negeert, wordt server-side gefikst.)

### 🧮 Groepering & sortering
Kies één optie (radio):

- **CardName** *(standaard)*  
  - Groepeer op **CardName**  
  - Sorteer binnen elke groep: **Vervaldatum ↑** (oudste eerst) → **MaandenOud** (meer oud eerst; negatievere waarde eerst)

- **CardCode**  
  - Idem maar groepeer op **CardCode**

- **DocOwner**  
  - Groepeer op **DocOwner**  
  - Sorteer binnen groep: **Naam** → **Vervaldatum ↑**

- **SalesOwner**  
  - Groepeer op **SalesOwner**  
  - Sorteer binnen groep: **Naam** → **Vervaldatum ↑**

- **MaandenOud**  
  - Sorteer primair op **MaandenOud** (meer negatief = ouder = eerst), dan **Vervaldatum ↑**

> Na ophalen wordt tab **OSO** automatisch geselecteerd (fallback: eerste beschikbare).

### 🗂 Tabs & structuur
- Visuele scheiding met disabled tabs: **— Verkoop —**, **— Samenvatting —**, **— Aankoop —**  
- **Verkoop**: `OSO`, `OSDL`, `OSDP`, `OSR`, `OSI`  
- **Aankoop**: `OPO`, `OPDL`, `OPR`, `OPI`  
- **Samenvatting** bevat subtabs:
  - **Secties (Sales)** en **Secties (Purchase)**: aantallen, totalen, earliest/latest due, outstanding
  - **Klanten**: per CardCode/CardName **SalesOpen** en **PurchaseOpen**  
    👉 Klik op kolomkoppen om ↑/↓ sortering te wisselen
  - **DocOwner**, **SalesOwner**, **Buyer**: aantallen per verantwoordelijke

### 📋 Kolommen
- Per sectie worden deze kolommen getoond:  
  `DocNum, CardCode, CardName, DocDate, DocDueDate, DocTotal, PaidSum, Outstanding, OrderCount, MaandenOud, SalesOwner, DocOwner`
- **VATNbr** en **DocEntry** worden **niet getoond**.
- Datumweergave: **DD-MM-YYYY**.
- Automatische kolombreedte met cap; **CardName** breder, **DocOwner** smaller.

### ⬇️ Exporteren
- **Exporteer…**: huidige tab (of volledige Samenvatting als multitab-workbook).
- **Exporteer alles**: volledige workbook met **alle secties + samenvattingen**.
- **Export-bereik**: **Huidige tab / Alle tabs / Sales / Purchase**.
- **Bestandsnaam** bevat datumstempel (bv. `OpenSales_20250914.xlsx`).
- **Downloads** als standaardmap.  
- Excel via **openpyxl** of **XlsxWriter**; één tab kan ook als **CSV**.

---

## ✳️ Zoektermen & prefixen (artikels)

| Prefix   | Zoekveld                                        | Voorbeeld   |
|----------|-------------------------------------------------|-------------|
| *(geen)* | Artikelcode (ItemCode)                          | `41.1.1`    |
| `*`      | Omschrijving, lange omschrijving, foreign name  | `*bocht`    |
| `/`      | Leveranciersreferentie (SuppCatNum)             | `/2109009`  |
| `-`      | Exact woord in naam/foreign name                | `-T-stuk`   |

> Prefixen gelden niet voor BP of Documents.

---

## 🎹 Sneltoetsen

| Locatie            | Toets           | Actie                      |
|--------------------|-----------------|----------------------------|
| Hoofdscherm        | `Ctrl + Enter`  | Zoeken                     |
|                    | `Ctrl + L`      | Label genereren (artikels) |
|                    | `Ctrl + O`      | Detail openen              |
|                    | `Delete`        | Zoekveld + tabel leeg      |
|                    | `Esc`           | Venster sluiten            |
| BP-venster         | `Ctrl + Enter`  | Data ophalen               |
|                    | `Esc`           | Sluiten                    |
| Documents-venster  | `Ctrl + Enter`  | Ophalen                    |
|                    | —               |                            |

---

## ⚙️ Instellingen (selectie)

- **Omgeving**: live/test  
- **Voorraad-modus (artikels)**: R/S/B  
- **Detail als modal**: ja/nee  
- **Standaard zoektype**: Standaard/Project/BP  
- **BP Type (default)**: `""`, `C`, `S`  
- **Taal (NL/EN)**  
- **QSS-styles** live te bewerken

---

## 🔄 Updates

- Automatische check bij opstart  
- **Help → Over…** toont versie & “Update nu”  
- Instellingen blijven bewaard

---

## 🛠 Installatie

- Windows `.exe` via PyInstaller

---

## 🐞 Bug of feature melden

- Via **Rapporteren** → “Bug of feature melden…”  
- Na verzenden wordt een GitHub-issue aangemaakt

---

## ℹ️ Contact

Voor vragen of feedback: contacteer de ontwikkelaar.
