# 📦 Artikelzoeker – Help

**Versie:** 6.0.1  
**Laatste update:** augustus 2025

Deze applicatie laat je toe om **artikels**, **projectitems** en **business partners** efficiënt op te zoeken, met uitgebreide details, voorraadinfo en koppelingen naar aankoop- en verkooporders. Werkt enkel **ONLINE** via de Windows `.exe` (PyInstaller).

---

## 🔎 Zoeken

1. **Voer een zoekterm in** bovenaan.
2. **Kies type zoekopdracht:**
   - `Standaard` – zoekt artikels
   - `Project` – zoekt in projectartikelen
   - `BP` – zoekt Business Partners (klanten/leveranciers)
3. **Selecteer modus** *(enkel bij Standaard & BP)*:
   - `AND` = alle woorden aanwezig
   - `OR` = minstens één woord
4. **Tweede keuzelijst** (onder de modus) is contextgevoelig:
   - Bij **Standaard**: **Toon voorraad** → `R` (regulier), `S` (voorraad), `B` (beide)
   - Bij **BP**: **Type** → `""` (alle), `C` (Customer), `S` (Supplier)
5. **Start met Zoeken** (`Ctrl + Enter`)

Resultaten verschijnen in een tabel. De eerste rij wordt automatisch geselecteerd. Dubbelklik of rechtermuisklik voor meer acties.

---

## ✳️ Zoektermen & prefixen (artikels)

| Prefix   | Zoekveld                                        | Voorbeeld   |
|----------|-------------------------------------------------|-------------|
| *(geen)* | Artikelcode (ItemCode)                          | `41.1.1`    |
| `*`      | Omschrijving, lange omschrijving, foreign name  | `*bocht`    |
| `/`      | Leveranciersreferentie (SuppCatNum)             | `/2109009`  |
| `-`      | Exact woord in naam/foreign name                | `-T-stuk`   |

> Prefixen zijn **niet** van toepassing op BP-zoekopdrachten.

---

## 🧾 Resultatenkolommen

### Standaard (R/B)

| Kolom        | Omschrijving         |
|--------------|----------------------|
| `ItemCode`   | Interne code         |
| `ItemName`   | SAP-beschrijving     |
| `SuppCatNum` | Leveranciersref.     |

### Voorraad (S)

| Kolom               | Omschrijving         |
|---------------------|----------------------|
| `ItemCode`          | Artikelcode          |
| `ItemName`          | Artikelnaam          |
| `SUPPLIERIDPRODUCT` | Leveranciersref.     |
| `QUANTITY`          | Voorraad             |
| `WHSNAME`           | Magazijn             |
| `LOCNAME`           | Locatie              |
| `QTYMININV`         | Minimumvoorraad      |
| `QTYMAXINV`         | Maximumvoorraad      |
| `SUPPLIERNAME`      | Leveranciernaam      |
| `PRICESUPPLIER`     | Inkoopprijs          |
| `NOTE`              | Opmerkingen          |

### Project

| Kolom            | Omschrijving                       |
|------------------|------------------------------------|
| `Artikelnummer`  | Projectartikelcode                 |
| `SupplNbr`       | Leveranciersref. project           |
| `PrefSuppl`      | Voorkeursleverancier               |
| `Gecert.`        | Gecertificeerd (Y/N)               |
| `Omschrijving`   | Projectomschrijving                |
| `Leverancier`    | Leverancier uit document           |
| `PurchNbr`       | Bestelnummer gekoppeld             |
| `MD_SupplNbr`    | Masterdata leveranciersref.        |
| `MD_Suppl`       | Masterdata leveranciernaam         |

### Business Partners (BP)

| Kolom            | Omschrijving                  |
|------------------|-------------------------------|
| `CardCode`       | Partnercode                   |
| `CardName`       | Partnernaam                   |
| `FederalTaxID`   | BTW-nummer                    |
| `ContactPerson`  | (Eerste) actieve contactnaam  |

> Dubbelklik op een BP-rij opent het **BP-venster** met detailinfo.

---

## 📋 Acties per rij

- **Dubbelklik** → detailvenster  
  - Artikels → artikel-detail  
  - BP → BP-venster (credit control + tabs)
- **`Ctrl + O`** → open geselecteerde rij
- **Rechtsklik** → contextmenu:
  - 📋 Kopiëren
  - 🔍 Detail tonen *(niet bij BP)*
  - 🏷️ Label genereren *(enkel artikels)*

---

## 🏷️ Label (artikels)

- **Sneltoets:** `Ctrl + L`  
- Wordt automatisch gegenereerd als PDF  
- Instellingen: **Instellingen > Label-instellingen**

---

## 🪪 Artikel-detailvenster (artikels)

Tabs met uitgebreide informatie. Dubbelklik op een cel kopieert de rij.

| Tab                 | Info                              | Sneltoets |
|---------------------|-----------------------------------|-----------|
| 📦 LISA            | LISA-voorraad                     | `Alt + L` |
| 🏢 SAP             | SAP-voorraad en vrije stock       | `Alt + S` |
| 💰 Aankoop         | Aankoopinfo, linkt naar PO's      | `Alt + A` |
| 💸 Verkoop         | Verkoopinfo, linkt naar SO's      | `Alt + V` |
| 🚚 Logistiek       | Technische/logistieke data        | `Alt + G` |
| 📄 Laatste aankoop | Recente inkoop                    | `Alt + R` |
| 🖼️ Afbeelding     | Afbeeldingen en uploads           | `Alt + F` |
| ⚡ ATP             | Beschikbaarheidsplanning          | `Alt + T` |

---

## 🧑‍💼 BP-venster (Business Partner)

Het BP-venster toont bovenaan een **hoofding** met **standaard BP-data** en – zodra beschikbaar – **specifieke Credit Control-data**.

### Hoofding (bovenaan)

- **Standaard BP-data** (links & midden):
  - Partnercode, partnernaam, type (C/S), adres(sen), telefoon, GSM
  - Contactpersoon, e-mail, BTW-nummer, geldigheid
  - Notes & Free text (HTML/opmaak ondersteund)
  - IBAN / IBAN 2
  - Valuta (uit BP)
- **Credit Control-data** (rechts):  
  Wordt asynchroon opgehaald en **overschrijft** de financiële placeholder-waarden uit BP zodra beschikbaar:
  - Kredietlimiet, huidig saldo, open orders, open leveringen
  - Open facturen, open voorschotten, open credit notes
  - Totaal open waarde, beschikbaar krediet *(negatief = rood & vet)*
  - Kredietstatus *(“Over Limit” = ❗ + rood & vet)*
  - % opgebruikte krediet *(>100% = rood & vet)*
  - Betalingsconditie, laatste update, laatste factuurdatum

> Valuta komt steeds uit de BP-bron (niet uit Credit Control).

### Tabs onder de hoofding

- **Contacten**  
  Zoek en filter op naam/functie/telefoon/e-mail.  
  Filter op status: *Alle / Actief / Inactief*.  
  Dubbelklik toont een **Contactdetails**-dialoog.

- **Adressen**  
  Zoek op titel/postcode/plaats.  
  Filter op type: *B (Betaling) / S (Levering)*.  
  Dubbelklik toont een **Adresdetails**-dialoog.

- *(Voorzien)* **Credit Control detail**  
  Uitbreiding met diepte-informatie volgt in een afzonderlijke tab.

### Sneltoetsen (BP-venster)

| Toets          | Actie            |
|----------------|------------------|
| `Ctrl + Enter` | Data ophalen     |
| `Esc`          | Venster sluiten  |

---

## 🖼 Afbeelding uploaden (artikels)

1. Open detail > tab 🖼️ Afbeelding  
2. Klik **Upload nieuwe aanpassingen**  
3. Vul velden (beschrijving, vendor, link)  
4. Selecteer bestand (PNG/JPG/PDF)  
5. Automatische conversie & upload via OITMI API  
6. Vernieuwde afbeelding verschijnt direct

---

## ⚡ ATP (artikels)

- Selecteer magazijn  
- Klik **Data ophalen**  
- Zicht op verkoop- en aankooporders  
- Beschikbaarheden vetgedrukt  
- Aankoopregels = lichtgroen

---

## 🎹 Sneltoetsen (hoofdvenster)

| Toets           | Actie                         |
|-----------------|-------------------------------|
| `Ctrl + Enter`  | Zoeken                        |
| `Ctrl + L`      | Label genereren (artikels)    |
| `Ctrl + O`      | Detail openen                 |
| `Delete`        | Zoekveld + tabel leeg         |
| `Esc`           | Venster sluiten               |
| `F1`            | Help openen                   |

---

## ⚙️ Instellingen

- **Omgeving:** live/test  
- **Voorraad (artikels):** R/S/B  
- **Detail als modal:** ja/nee  
- **Standaard zoektype:** Standaard/Project/**BP**  
- **BP Type (default):** `""`, `C`, `S`  
- **Tabs volgorde (project/overig):** drag & drop  
- Configuratie in `settings.json`

> In BP-modus bewaart de tweede keuzelijst het **BP-type** als *default* (`bp_default_type`). In Standaard-modus bewaart diezelfde keuzelijst de **voorraadweergave** (`show_stock`).

---

## 🔄 Updates

- Automatische check bij opstart  
- Melding en **Update nu** via **Help > Over…**  
- Instellingen blijven bewaard

---

## 🛠 Installatie

- Windows `.exe` via PyInstaller  
- Structuur:
  - Kern: `ui_main.py`, `ui_detail.py`, `project_ui.py`, …
  - **BP-modules (nieuw):**
    - `ui_bp.py` – hoofdvenster BP
    - `ui_bp_header_panel.py` – hoofding met BP & Credit Control
    - `ui_bp_contacts_tab.py` – tab Contacten
    - `ui_bp_addresses_tab.py` – tab Adressen
    - `ui_bp_helper.py` – helpers (labels/opmaak/mapping)
    - `cc_service.py` – Credit Control service
    - `bp_token.py` – authenticatie header
    - `config.py` – API-omgevingen (`API_ENVIRONMENTS`, `ENVIRONMENT`)
  - Artikeltabs: `ui_lisa.py`, `ui_sap.py`, `ui_purchase.py`, `ui_sales.py`, `ui_lastpurch.py`, `ui_logistics.py`, `ui_atp.py`, `ui_po.py`, `ui_so.py`
  - Overig: `oitmi_upload.py`, `label/`, `assets/`, `docs/`, `logs/`

Logs in `logs/app.log`.

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
