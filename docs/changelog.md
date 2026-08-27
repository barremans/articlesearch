# 📝 Changelog

## [15.1.0] - 2026-08-27

### ✨ Nieuw
- 💳 **Betalingsgedrag & Openstaande Posten** — nieuw scherm via
  **Export → Betalingsgedrag...** (zelfde toegangsrechten als Open
  Elements). Twee tabbladen:
  - **Klanten**: gemiddeld betaalgedrag per klant (aantal documenten,
    gemiddeld aantal dagen tot betaling, gemiddeld verschil t.o.v. de
    vervaldatum, totaalbedragen) — filterbaar op aantal maanden,
    klantcode en betaalgedrag (alle klanten / enkel slechte betalers /
    enkel op tijd of vroeger).
  - **Facturen**: alle individuele facturen/voorschotten in de gekozen
    periode — filterbaar op aantal maanden, klantcode en op "Verschil
    vervaldatum" (alles / enkel te laat betaald / enkel correct betaald).
  - **Dubbelklik op een klant** in de Klanten-tab springt automatisch naar
    de Facturen-tab, gefilterd op die klant.
  - **Zoekbalk** per tabblad filtert live over alle kolommen; kolomkoppen
    zijn klikbaar om te sorteren.
  - **Export** naar CSV, Excel, of beide tegelijk — per tabblad apart of
    beide tabbladen ineens. De map met het geëxporteerde bestand wordt na
    export automatisch geopend, en de laatst gebruikte exportmap wordt
    onthouden voor de volgende keer.
  - Ingevulde maanden/klantcode op de Klanten-tab worden automatisch
    overgenomen naar de Facturen-tab.
  - **Sneltoetsen**: `Ctrl+Enter` (ophalen), `Ctrl+E` (exporteren),
    `Alt+1`/`Alt+2` (wissel tabblad), `Esc` (sluiten).

### 🐞 Bugfix
- 🖼️ **Afbeelding uploaden (detailvenster)**: de velden Beschrijving,
  Leveranciersartikelnummer en Leveranciersnaam worden nu automatisch
  vooraf ingevuld op basis van de reeds gekende artikelgegevens (eigen
  omschrijving, gegevens uit de zoekresultaten en/of de laatste aankoop)
  wanneer er nog geen eerdere afbeelding-informatie voor dat artikel
  bestaat. Voordien bleven deze velden in dat geval leeg en moest alles
  manueel ingetikt worden. Reeds bestaande waarden worden nooit
  overschreven.

---

## [15.0.2] - 2026-08-06

### ✨ Nieuw
- 📄 **Peppol-controlescherm volledig herontworpen**: overzichtelijke
  documentinfo (documenttype, klantnaam + code, klantreferentie) i.p.v.
  een kale DocEntry/Status-lijst.
- 🚦 **Duidelijke statusindicator** (✅ Voltooid / ⚠️ Waarschuwing /
  🔴 Fout / ⏳ Wachtend/onbekend) bovenaan het scherm, die rekening houdt
  met de ernst van de onderliggende foutmelding — niet enkel met de rauwe
  taakstatus.
- 🈯 **Foutmeldingen worden nu leesbaar vertaald** i.p.v. rauwe,
  technische JSON-tekst te tonen.
- 🔁 **Herhaalde identieke foutmeldingen** (retries) worden automatisch
  samengevoegd tot 1 regel met een pogingenteller, i.p.v. dezelfde fout
  meermaals te tonen.
- ⚠️ **Onbekende foutcodes duidelijk gemarkeerd**, met de mogelijkheid om
  de volledige foutmelding te kopiëren en rechtstreeks te melden via
  GitHub — zodat nieuwe foutcodes sneller aan de vertaallijst toegevoegd
  kunnen worden.

### 🛠 Verbeterd
- **Peppol-detailweergave:** een dubbelklik op een statusregel toont nu
  altijd de volledige foutmelding (voorheen afgekapt in de tabel).
- **Robuustere verwerking** van onvolledige/afgekapte foutberichten
  vanuit de API — het scherm blijft correct werken ook als een
  foutmelding technisch niet perfect is opgebouwd.

### 🐞 Bugfix
- **Kritieke fix:** herkende Peppol-foutcodes werden door een foutieve
  opzoeklogica nooit correct vertaald — dit zat al sinds de eerste versie
  van het Peppol-scherm.
- **Statusicoon-fix:** een onschuldige waarschuwing (bv. "document reeds
  verstuurd/in wachtrij") werd voorheen onterecht als blokkerende fout
  getoond.

### 🔒 Security
- **GitHub-integratie:** de sleutel voor het melden van bugs/features via
  GitHub wordt nu veilig via een systeeminstelling geladen i.p.v.
  hardcoded in de broncode te staan.

---

## [15.0.0] - 2026-08-04

> Verzamelentry voor alles wat sinds `[9.1.0]` in de app terechtkwam maar
> nog niet in dit lokale changelog stond (sessies 1–17). Eventuele
> tussenliggende versienummers die niet apart in de ontwikkelcontext zijn
> vastgelegd, worden hier niet los vermeld.

### ✨ Nieuw
- 📐 **Dimensions-tab** (DIM-1) toegevoegd aan het artikel-detailvenster
  (`ui_detail.py`), net na de tab "SAP". Toont afmetingen/gewicht
  (Verkoop-, Verpakkings- en Inventaris-eenheden) uit de al bestaande
  `MEASUREMENT_INFO`-data — **geen extra API-call** nodig.
- 🔀 **Kolomsortering Artikel-resultaten** (SORT-1): dubbelklik op de
  kolomkop van **Art.Nr., Leverancier** (alfabetisch) of **Qty, Prijs**
  (numeriek) sorteert de tabel. Tweede dubbelklik op dezelfde kolom keert
  de richting om; sortering wordt gereset bij elke nieuwe zoekopdracht.
  Enkel actief voor zoektype **Artikel**.
- 🏭 **Artikels-tab bij leveranciers** (ART-BP-1): nieuwe tab "Artikels" in
  het Business Partner-venster, zichtbaar wanneer de kaart een leverancier
  is. Toont alle artikelen gekoppeld aan die leverancier (incl.
  leveranciersartikelnummer, laatste inkoopprijs, afname laatste 6/12
  maand), met eigen zoekbalk, eigen verzamel-/kopieerlijst en
  dubbelklik-sortering op prijs en afnamehoeveelheden.
- 🔒 **Toegangsbeperking Credit Control-tab** (CC-ACCESS-1): de 5
  detaillijsten (Orders, Leveringen, Voorschotten, Facturen,
  Kredietnota's) in de CC-tab van het BP-venster zijn nu enkel zichtbaar
  voor leden van Azure AD-groepen **CGK-APP-L2, L3, L4 of L6**. De
  algemene financiële kopgegevens (kredietlimiet, saldo, status, ...)
  blijven zichtbaar voor iedereen.
- 🟢 **Visuele markering "Standaard artikel"** (MINWHS-KLEUR-1): in de
  Artikel-resultatentabel krijgt de cel "Min.Whs" een lichtgroene
  achtergrond + tooltip wanneer de waarde groter is dan 0.
- ↔️ **Vrij versleepbare kolommen** (KOLOMBREEDTE-1): kolombreedtes in de
  Artikel-resultatentabel zijn nu manueel aanpasbaar en dubbelklik-autofit
  ondersteund (net als Excel), i.p.v. een vast uitgerekte kolom.
- 🆕 **"Wat is er nieuw?"-knop** (WHATSNEW-1): zowel bij de opstart-melding
  van een beschikbare update als in Help → Over... kan de gebruiker nu de
  release notes van de laatste GitHub Release bekijken, met terugval naar
  een link naar GitHub als er geen beschrijving beschikbaar is.

---

### 🛠 Verbeterd
- **Artikels-tab (BP):** zoekbalk toegevoegd (filtert op Art.Nr.,
  Leverancier Art.Nr. en Omschrijving), naar analogie van de bestaande
  zoekfunctie in de Addresses- en Contacts-tabs.
- **Artikels-tab (BP):** kolommen CardCode/CardName en Omschrijving (Frgn)
  niet langer getoond — overbodig binnen de kaart van één leverancier.
- **Artikels-tab (BP):** kolombreedtes en stretch-gedrag werken nu op
  kolomsleutel i.p.v. vaste kolomindex, zodat toekomstige kolomtoevoegingen
  de lay-out niet meer verstoren.

---

### 🐞 Bugfix
- **"Geen voorraad"-melding verscheen nooit:** de vergelijking gebruikte
  intern nog `"Standaard"` terwijl de zoektype-keuzelijst effectief
  `"Artikel"` als waarde gebruikt. Gecorrigeerd in `ui_main.py`,
  `settings.py` en `settings_dialog.py`; bestaande instellingen met de
  oude waarde vallen automatisch terug op `"Artikel"`.
- **Kritieke fix toegangscontrole:** de Azure AD-groep `CGK-APP-L6`
  ontbrak in de basis-toegangscontrole (`main.py`), waardoor leden van
  die groep de applicatie zelf nooit konden openen — ook niet met
  geldige Credit Control-rechten.

---

### 🔒 Security
- **Datalek in Credit Control-tab gedicht:** financiële detaildata
  (orders, leveringen, voorschotten, facturen, kredietnota's) werd voorheen
  altijd opgehaald en ingeladen, ongeacht rechten — enkel visueel verborgen
  achter het vergrendelscherm. Nu wordt enkel de daadwerkelijke vulling van
  de 5 detaillijsten achter de rechtencontrole geplaatst; de algemene
  financiële kopgegevens blijven bewust voor iedereen zichtbaar.

---

## [9.0.5] - 2026-02-03

## [9.1.0] - 2026-02-09

### 🔐 Beveiliging & Toegang (Azure AD)

### ✨ Nieuw
- 🔑 **Verplichte Azure AD-login bij applicatiestart**
  - De applicatie vereist nu **altijd** een geldige Azure AD-aanmelding vóór de UI wordt opgebouwd.
  - Geen succesvolle login → **app start niet door**.

- 🚫 **Nieuwe “Geen toegang”-pagina**
  - Speciaal venster (`ui_no_access.py`) dat wordt getoond wanneer:
    - de gebruiker geen toegang heeft,
    - de login wordt geannuleerd,
    - of de gebruiker geen geldige rechten heeft.
  - Volledig **meertalig** (NL / EN) via bestaande `translations`.

- 🧭 **Meertalige foutmeldingen**
  - “Geen toegang”-scherm toont duidelijke uitleg in de ingestelde taal.
  - Gebruiker krijgt instructie om IT te contacteren indien nodig.

---

### 🛠 Verbeterd
- 🧠 **Slimmere basis-toegangslogica**
  - Gebruikers krijgen toegang tot de applicatie als ze:
    - lid zijn van **`Alle gebruikers`**
    - **OF** lid zijn van minstens één applicatiegroep:
      - `CGK-APP-L1`
      - `CGK-APP-L2`
      - `CGK-APP-L3`
      - `CGK-APP-L4`
      - `CGK-APP-L5`
  - Dit voorkomt onterechte blokkering van gebruikers met expliciete app-rechten.

- ⏳ **Azure AD login-timeout toegevoegd**
  - Wanneer de gebruiker:
    - het browservenster sluit,
    - niet inlogt,
    - of te lang wacht,
  - wordt de login **automatisch afgebroken** (timeout ±30s).
  - De applicatie blijft **niet meer hangen**.

- 🧱 **Geen race-conditions meer bij opstart**
  - Asynchrone AD-aanroepen bij startup verwijderd.
  - Alle toegangscontroles gebeuren **vóór** het hoofdvenster wordt gestart.

---

### 🔒 Security
- ❌ Geen toegang voor:
  - externe Azure AD tenants,
  - gastgebruikers zonder CGK-appgroepen,
  - persoonlijke Microsoft-accounts,
  - gebruikers zonder basisrechten.
- ✅ Bestaande rechtenstructuur (L1–L5, Finance, enz.) blijft volledig behouden.
- 🔐 Tokens en API-calls worden **pas** uitgevoerd na succesvolle toegang.

---

### 🧪 Getest
- ✅ Succesvolle login (CGK gebruiker).
- ✅ Gebruiker alleen in `CGK-APP-L1`.
- ❌ Login geannuleerd in browser.
- ❌ Externe Azure AD gebruiker.
- ❌ Gast zonder app-rechten.
- ❌ Time-out zonder gebruikersinteractie.

---

### ✨ Nieuw
- ⏱️ **Urenregistratie Downloader + Verwerker – verbeterde bestandsselectie**
  - Bestanden uit SharePoint worden nu **gesorteerd op wijzigingsdatum**  
    (**jongste eerst**, gebaseerd op `TimeLastModified`).
  - **Zoekfilter toegevoegd** boven de bestandslijst:
    - Live filtering op bestandsnaam en datum.
    - Geen extra SharePoint-calls nodig (client-side filtering).
  - Nieuwe optie **“Toon alle bestanden”**:
    - Standaard worden enkel de **5 meest recente** bestanden getoond.
    - Checkbox maakt het mogelijk om **de volledige lijst** zichtbaar te maken.
    - Zoekfilter werkt correct in beide modi (Top 5 / Alles).

---

### 🛠 Verbeterd
- **Gebruiksvriendelijkheid**
  - Overzichtelijkere bestandslijst met focus op recente weken.
  - Sneller navigeren in omgevingen met veel historische Excel-bestanden.
- **Technische structuur**
  - Bestandsmetadata (naam, grootte, datum) intern opgesplitst i.p.v. string-sortering.
  - Robuustere datumverwerking bij ontbrekende of ongeldige SharePoint-metadata.
- **GUI-interactie**
  - Dynamische hertekening van de lijst bij zoeken of wisselen van weergavemodus.
  - Consistente werking bij verversen van de lijst.

---

## [9.0.4] - 2025-12-11
- Patch Timings


## [9.0.3] - 2025-12-04

### ✨ Nieuw
- 🧮 **Tools – volledig nieuw menu**
- Nieuw beveiligd venster met diverse tools
- artikel search
  - rechts klik actie toegevoegd
    - keuze uit 
      - copy veld
      - copy rij


## [9.0.0] - 2025-12-04

### ✨ Nieuw
- 🧮 **Credit Control (CC BP) – volledig nieuw venster**
  - Nieuw beveiligd venster `ui_CcBP.py` toegevoegd aan het hoofdmenu  
    (**Export → Open Credit Control (CC BP)**).
  - Bevat nu:
    - ✅ Filters, groepering en sortering  
    - ✅ Selectiebeheer (➕ toevoegen, 📋 tonen, ❌ leegmaken, ⬇️ exporteren)  
    - ✅ Dubbelklik op klant → filterweergave  
    - ✅ Delete / Ctrl + D → reset filters  
    - ✅ Export naar Excel met automatische kolombreedte  
    - ✅ Dynamische kleurcodering voor **Risicokleur** en **Risicocategorie**  
    - ✅ Visuele markering voor “Over kredietlimiet” (rood/groen)
  - Exporteert selectie of volledige dataset automatisch naar `~/Downloads` met datumstempel.

- 🔐 **Azure AD-integratie**
  - Controleert of de gebruiker lid is van **Azure AD-groep `GPP_Finance`**.  
  - Geen toegang → melding en automatisch sluiten.  
  - Volledige integratie via `permissions_azure.py`.

- 🔄 **Integratie met hoofdvenster (`ui_main.py`)**
  - Nieuw menu-item onder **Export** voor Credit Control.  
  - Alleen beschikbaar in **online modus** (`OFFLINE_MODE = False`).  
  - Foutafhandeling via `QMessageBox`.  
  - Toegevoegd aan `self.docs_windows` voor centraal vensterbeheer.

- ⚙️ **Nieuwe hulpfunctie `_open_ccbp_window()`**
  - Toegevoegd aan `MainWindow` voor veilige, consistente toegang.  
  - Zelfde logica als `_open_docs_window()`.  
  - Toont waarschuwing bij offline gebruik.

- 💾 **Excel-export 2.0**
  - Ondersteunt volledige dataset én selectie-export.  
  - Inclusief automatische kolombreedte, datumformaat `dd-mm-yyyy` en timestamp-bestandsnaam.  
  - Bestanden worden automatisch opgeslagen in de `Downloads`-map.

---

### 🛠 Verbeterd
- **Hoofdapplicatie (`ui_main.py`)**
  - Code opgeschoond en menu’s geherstructureerd.  
  - Consistente logica voor alle exportmodules.  
  - Offline-indicator blijft zichtbaar in menubalk.

- **Credit Control-logica (`ui_CcBP.py`)**
  - API-aanroepen via `ThreadPoolExecutor` (geen UI-blokkering).  
  - Betere foutafhandeling met `api_success` / `api_error`-signalen.  
  - `prepare_dataframe()` normaliseert kolomnamen voor uniforme weergave.

- **Beveiliging**
  - AD-authenticatie en groepcontrole uitgevoerd vóór UI-opbouw.  
  - Offlinegebruikers krijgen duidelijke melding i.p.v. crash.

- **Gebruikerservaring**
  - Minimale grootte 1300×750 px.  
  - Kolommen resizen automatisch na laden of sorteren.  
  - Intuïtieve knoppen met emoji (➕ ❌ 📋 ⬇️).  
  - Statuslabel toont steeds aantal resultaten of geselecteerde klant.

---

### 💄 Visuele verbeteringen
- **Kleurcodering voor risico’s**
  - 🟢 LOW / GREEN  
  - 🟡 MEDIUM / YELLOW  
  - 🟠 HIGH / AMBER  
  - 🔴 CRITICAL / RED
- **Geselecteerde klanten** → lichtgroene markering.  
- **Filters en opties** hergroepeerd in drie secties:
  1. Hoofdcriteria  
  2. Extra opties  
  3. Selectiebeheer  
- Uniforme stijl met accentkleuren en strakke layouts.

---

### 🧩 Technisch
- Nieuwe bestanden:
  - `ui_CcBP.py` – hoofdvenster Credit Control  
  - `ui_CcBP_helper.py` – data-preprocessing en formattering
- Gewijzigd:
  - `ui_main.py` – menu-integratie en AD-controle  
  - `config.py` – ondersteuning voor `OFFLINE_MODE`
- Bibliotheken: `pandas`, `requests`, `openpyxl`.  
- Thread-safe signalering voor API-verwerking.

---

### 🧪 Getest
- ✅ Gevalideerd op **test** en **live** omgeving.  
- ✅ Meerdere `ConfigurationID`s getest voor API-consistentie.  
- ✅ Excel-export en selectiebeheer getest.  
- ✅ Offline- en AD-scenario’s succesvol gesimuleerd.

---

### 🔜 Volgende stappen
- 📊 Credit Risk Summary-tab met grafieken.  
- 🧾 PDF-export voor klantensamenvattingen.  
- 🧠 AI-analyse voor hoog-risico klanten (over limiet).

---

---
## [8.0.1] - 2025-11-26
    - Bugfix *.md files
---
## [8.0.0] - 2025-11-26

### ✨ Nieuw
- 🧾 **Project Info-venster uitgebreid**
  - Toegevoegd: **intelligente sortering** in tabbladen:
    - Aankooporders (type `12`) worden **bovenaan** geplaatst.
    - Documenten met status **“IN PROGRESS”** komen direct onder de aankooporders.
    - Overige documenten volgen daaronder.
  - **Kleuraccenten toegevoegd:**
    - Aankooporders (`type 12`) krijgen een **groene achtergrond**.
    - Documenten met status **OPEN** of **IN PROGRESS** worden **rood gemarkeerd** voor duidelijkheid.
  - Sortering geldt nu zowel in:
    - 📄 **PRJ Art. (VTA)** tab  
    - 🧰 **Installaties** tab
  - Verbeterde herkenning van statusvelden via **diepzoekfunctie** — statuswaarden worden nu correct gevonden, ongeacht of ze op hoofd- of subniveau staan (zoals in `POR`, `LART`, enz.).

- 🖱️ **Dubbelklikfunctionaliteit toegevoegd**
  - In de tabbladen **Artikels (ART)**, **Installaties** en **PRJ Art. (VTA)** kan je nu dubbelklikken op een artikelnummer om het **detailvenster (ui_detail.py)** direct te openen.
  - Het detailvenster toont automatisch alle informatie over het gekozen artikel (LISA, SAP, logistiek, aankopen, verkoop, afbeeldingen, …).
  - Venster opent bovenop het projectscherm en blijft actief tot sluiten.

- ⚠️ **Geen voorraadmelding toegevoegd**
  - Wanneer de gebruiker zoekt met **Search-type = "Standaard"** en **Toon voorraad = "S"**,  
    wordt nu een duidelijke melding getoond als **geen voorraad beschikbaar** is voor de opgegeven zoekterm.
  - De tabel toont in dat geval één rij met de melding *“⚠️ Geen voorraad aanwezig voor deze zoekterm.”*
  - Er verschijnt tevens een pop-upmelding om de gebruiker onmiddellijk te informeren.
  - De statusbalk toont: `Aantal resultaten: 0 (geen voorraad)`.

- 🧑‍🤝‍🧑 **Nieuw icoon toegevoegd voor Business Partner**
  - In `ui_bp.py` wordt nu het icoon `bp.png` gebruikt als **venstericoon** in de titelbalk.
  - Het icoon wordt tevens weergegeven naast het label **“Partner:”** in de zoekbalk.
  - Zorgt voor visuele herkenbaarheid tussen modules (`BP`, `PO`, `VTA`, `PRJ`, …).

---

### 🛠 Verbeterd
- Betere stabiliteit bij het openen van **documentvensters** (`PO` en `VTA`) via dubbelklik.
- Verbeterde weergave en consistentie van kolommen tussen tabbladen.
- Kleine optimalisaties in de UI-layout en sorteerlogica.
- Vensterpositie en focus worden nu correct behouden bij het openen van subvensters (zoals `ui_detail.py`).
- Business Partner-venster (`ui_bp.py`) geoptimaliseerd voor consistente icoonweergave.

---

### 💄 Visuele verbeteringen
- De melding in de tabel is **gecentreerd en geel gemarkeerd**, zodat ze duidelijk opvalt.
- Spinner en laadindicator worden netjes gestopt zodra de melding verschijnt.
- Subvensters openen nu altijd **bovenop** en met een consistente stijl (uit `assets/css/detail.qss`).
- Nieuw `bp.png`-icoon volgt dezelfde visuele stijl als andere module-iconen.

---


## [7.2.0] - 2025-11-25
### ✨ Nieuw
- 🔍 **VTA-integratie uitgebreid**
  - Nieuw zoektype **"VTA"** toegevoegd aan het hoofdzoekvenster.
  - Direct openen van het **VTA-venster (ui_vta.py)** bij zoekopdrachten van type “VTA”.
  - Automatisch invullen van het ingegeven VTA-nummer en ophalen van de data bij openen.
  - Zoekveld wordt automatisch **leeggemaakt en focus hersteld** na het openen.

- ⚙️ **Instellingen uitgebreid**
  - Nieuw keuzemenu in **Instellingen → Standaard zoektype**: nu ook optie **“VTA”**.
  - Gebruikers kunnen hun **voorkeurszoektype** (Standaard / Project / BP / VTA) opslaan in `settings.json`.
  - Ondersteuning voor **BP Type (default)** toegevoegd (`""`, `"C"`, `"S"`).
  - `settings.py` uitgebreid met validatie voor `"VTA"` in `load_default_search_type()` en `save_default_search_type()`.

- 🧭 **UI & navigatie**
  - VTA-venster opent **niet-modale** (onafhankelijke) vensters voor parallel gebruik.
  - Ctrl + D toegevoegd voor **Delete & focus** functionaliteit in `ui_vta.py`.
  - **Zoekbalk** in hoofdvenster wordt automatisch leeggemaakt na openen van VTA-venster.

- 🎨 **Kleuren in VTA-tabel**
  - Kolom **Status** krijgt dynamische kleuren:
    - 🔴 Rood met witte tekst bij “Open > 0”.
    - 🟢 Groen met zwarte tekst bij status “COMPLETE”.

### 🧰 Technisch
- Nieuwe functies in `settings.py`:
  - `save_default_search_type()` en `load_default_search_type()` ondersteunen nu `"VTA"`.
- `settings_dialog.py` bijgewerkt om `"VTA"` in het dropdownmenu te tonen.
- `ui_main.py` herwerkt om VTA-flow correct te openen, inclusief focus- en vensterbeheer.
- Verbeterde compatibiliteit tussen **ui_main** en **ui_vta** bij directe of indirecte opening.

---
## [7.0.3] - 2025-09-17
### Fixed
- 🐞 **Updater-fix**: het updatemechanisme hersteld zodat de applicatie opnieuw correct de **remote versie** ophaalt via `version.txt` in de repository.
- De `version.txt` wordt nu automatisch aangevuld met de **volledige download-URL** bij publicatie.
- Hierdoor detecteert de app opnieuw correct of een **nieuwere versie beschikbaar** is en wordt de **"Update nu"-knop** correct geactiveerd.



## [7.0.2] - 2025-09-17
### Changed
- Publicatieproces herwerkt: installateurs (.exe-bestanden) worden niet langer rechtstreeks in de repository opgeslagen, maar als **assets bij GitHub Releases**.
- `version.txt` bevat nu naast het versienummer ook de **volledige download-URL** van de meest recente installer.
- Toegevoegd `.gitignore` om `.exe`-bestanden uit de repository te houden en zo de repository slank te houden.

## [V7.0.1] - 2025-09-16
### 💳 Credit Control – lijsten & pop-ups
- **Altijd links uitlijnen** in álle tabellen (lijsten + pop-ups), ongeacht datatype.
- **NL-kopteksten/vertalingen** toegevoegd in lijsten en pop-ups (o.a. *Bestelnr, Leveringsnr, Datum, Vervaldatum, BTW, Munt, Openstaand*, …).
- **Datumnotatie**: alle datumvelden automatisch naar **dd/mm/jjjj**. Ondersteunt ISO (`YYYY-MM-DD[THH:MM:SS]`) en SAP `/Date(ms)/`.
- **DocEntry verborgen** in lijsten (ODPI/OINV/ORIN); blijft wel beschikbaar in row-payload voor doorklik.
- **Vrije tekst (FreeTxt/LineMemo)**:
  - **Orders (ORDRL), Facturen (INV1), Kredietnota’s (RIN1)** → **vrije tekst als kolom** in de grid. Het aparte tekstvlak is verwijderd.
  - **Leveringen (DNL1)** → **geen vrije tekst**: tekstvlak verwijderd en geen FreeTxt-kolom.
  - **Voorschotten (DPI1)** → vrije tekst als **kolom** (indien aanwezig in de data).
- **Datums in headers** van pop-up dialogen geformatteerd naar **dd/mm/jjjj**.
- **Dubbelklik-gedrag** blijft werken na sorteren; row-payload blijft vast aan kolom 0 via `Qt.UserRole`.
- 🐞 **Bugfix**: ontbrekende `snapshot()` in `CreditControlListsTab` toegevoegd (verhinderde `AttributeError` bij `show_after_unlock`).

### 📄 Aangepaste/belangrijke bestanden (versieheaders in code)
- `ui_bp_cc_lists_tab.py` — **V7.1.0** (links uitlijnen, datums, vertalingen, DocEntry verbergen, payload & dblclick)
- `ui_bp_cc_ordrl_dialog.py` — **V7.0.1** (FreeTxt als kolom, NL-headers, links uitlijnen)
- `ui_bp_cc_inv1_dialog.py` — **V7.0.1** (FreeTxt als kolom, NL-headers, links uitlijnen, datum header)
- `ui_bp_cc_rin1_dialog.py` — **V7.0.1** (FreeTxt als kolom, NL-headers, links uitlijnen, datum header)
- `ui_bp_cc_dpi1_dialog.py` — **V7.0.1** (FreeTxt als kolom, NL-headers, links uitlijnen, datum header)
- `ui_bp_cc_dnl1_dialog.py` — **V7.1.0** (geen FreeTxt-kolom/tekstvlak, NL-headers, links uitlijnen, datum header)

## [7.0.0] - 2025-09-17
### Added
- BP (Business Partner)-venster: **vertaling toegevoegd** zodat dit venster nu correct vertaald wordt in de gebruikersinterface.

---
## [v6.0.3] - 2025-09-13
### ✨ Nieuw: Open Sales/Purchase — Documents
- Nieuw venster **Open Sales/Purchase — Documents** (menu **Export → Open elements**).
- Beveiligd met wachtwoord (zelfde als BP). **Eénmalige** ingave per sessie; sluiten van het venster vergrendelt opnieuw.
- **Aantal** (voorheen “Key”): keuze **6** of **Anders** (vrij getal). Wordt meegestuurd naar de API.
- **Groepering/sortering** (radio-opties):
  - **CardName** *(standaardlogica)* → groepeer op klant/leverancier; sorteer binnen groep op **Vervaldatum ↑** (oudste eerst), daarna **MaandenOud** met **meer oud eerst** (dus -10 vóór -8).
  - **CardCode** → idem maar gegroepeerd op code.
  - **DocOwner** → groepeer op document-eigenaar; sorteer binnen groep op **Naam** + **Vervaldatum ↑**.
  - **SalesOwner** → groepeer op verkoper; sorteer binnen groep op **Naam** + **Vervaldatum ↑**.
  - **MaandenOud** → sorteer primair op **MaandenOud** (meer negatief eerst), secundair **Vervaldatum ↑**.
- **Tabs & structuur**
  - Visuele scheiding met disabled tabs: **— Verkoop —**, **— Samenvatting —**, **— Aankoop —**.
  - **Verkoop**: OSO → OSDL → OSDP → OSR → OSI (in deze volgorde).
  - **Aankoop**: OPO → OPDL → OPR → OPI (in deze volgorde).
  - Na ophalen wordt tab **OSO** automatisch geselecteerd (fallback: eerste beschikbare).
- **Samenvatting** (met subtabs en sorteerbare kolommen):
  - **Secties (Sales)** en **Secties (Purchase)**: totalen, earliest/latest due, outstanding.
  - **Klanten**: per CardCode/CardName twee kolommen **SalesOpen** en **PurchaseOpen** (klik op headers om ↑/↓ te wisselen).
  - **DocOwner**, **SalesOwner**, **Buyer**: aantallen per verantwoordelijke.
- **Kolommen & layout**
  - Standaardkolommen per sectie:  
    `DocNum, CardCode, CardName, DocDate, DocDueDate, DocTotal, PaidSum, Outstanding, OrderCount, MaandenOud, SalesOwner, DocOwner`
  - **VATNbr** en **DocEntry** worden **verborgen**.
  - Datums in **DD-MM-YYYY**.
  - **CardName breder**, **DocOwner smaller**; automatische kolombreedte (max cap) en herberekening na sorteren.
- **Export**
  - Knoppen **Exporteer…** (huidige tab of samenvatting) en **Exporteer alles** (volledige workbook).
  - Export-bereik: **Huidige tab / Alle tabs / Sales / Purchase**.
  - Bestandsnaam met **datumstempel** (bijv. `OSO_20250914.xlsx`, `OpenSales_20250914.xlsx`, `OpenDocuments_20250914.xlsx`).
  - Standaardmap **Downloads**.
  - Excel via **openpyxl** of **XlsxWriter**; één tab kan ook als **CSV**.
- **Integratie**
  - Nieuw menu **Export** in `ui_main` met item **Open elements** dat het venster opent.
  - Wachtwoord wordt gedeeld met BP-module (zelfde bron).

---

## [V6.0.1] - 2025-09-04
- 🐞 Bugfix: artikel “no dict” error opgelost.
- 🧭 Business Partner (BP)
  - Tab **“Overzicht”** verwijderd.
- 💳 Credit Control
  - **ODPI (Voorschotten), OINV (Facturen), ORIN (Kredietnota’s)** toegevoegd aan lijsten.
  - Kolommen **DPI1/INV1/RIN1** bewust **niet** in de tabellen getoond (blijven in row-payload voor pop-ups).
  - **Dubbelklik-pop-ups** toegevoegd:
    - Orders → **ORDRL** (met groot FreeTxt-veld)
    - Leveringen → **DNL1** (met FreeTxt/LineMemo)
    - Voorschotten → **DPI1** (met FreeTxt/LineMemo)
    - Facturen → **INV1** (met FreeTxt/LineMemo)
    - Kredietnota’s → **RIN1** (met FreeTxt/LineMemo)
  - Pop-ups blijven correct werken na sorteren (row-payload aan kolom 0 bevestigd via `Qt.UserRole`).
- 🔒 UI & security
  - **Debug-knop en debugpaneel** uit de Credit Control-tab verwijderd.
  - Wachtwoordslot blijft behouden; “Vergrendel opnieuw” blijft beschikbaar.

## [V6.0.0] - 2025-08-29
- toevoeging BusinessPartner zoek flow
- Business partner detail fiche toevoeging
- toevoeging credit control data
- voorbereiding voo AI op artikelen

## [v5.1.0] – 2025-07-09
- Aanpassingen op token manager
- voorbereidingen op Business Partner integratie

## [v5.0.2] – 2025-07-09

### 🌍 Meertaligheid & vertalingen
- Toegevoegd: **Taalkeuze (NL/EN)** in het instellingenvenster (`settings_dialog.py`).
- Nieuw: Centrale `translations`-directory met `nl.py` en `en.py` bestanden.
- Labels (bijv. "Update nu") in `ui_main.py` worden nu dynamisch geladen op basis van ingestelde taal.

### ⚙️ Settings verbeteringen
- `settings.json` bevat nu de key `"language"`, standaard ingesteld op `"NL"`.
- `settings.py`: Functies `load_language()` en `save_language()` toegevoegd.
- Automatisch aanvullen van ontbrekende keys bij laden van settings.

### 💡 Code refactor
- `show_settings_dialog` verplaatst naar eigen bestand `settings_dialog.py` voor betere structuur en onderhoudbaarheid.
- Oude, dubbele `_show_settings_dialog()` code uit `ui_main.py` verwijderd.

---

## [v5.0.1] – 2025-07-03
- 💡 **UI Verbeteringen & uniformisatie**
  - `ui_po.py` en `ui_so.py` gebruiken nu beide **dynamische headers via `field_labels`** uit `settings.json`, zodat kolomtitels eenvoudig aanpasbaar zijn.
  - Handmatig ophalen van data behoudt ingestelde kolombreedtes (geen automatische resize meer).
  - Standaard kolombreedtes ingesteld voor een consistent uiterlijk.
  - Automatisch verwijderen van prefixen (OR, BE en spaties) voor correcte documentnummers.
  - Betere parsing van documentnummers bij doorklik vanuit tabellen.

- ⚡ **Sneltoetsen uitgebreid**
  - `ui_po.py`
    - Ctrl + Enter: ophalen data
    - Page Up / Down: wisselen status (Open/Closed)
    - Alt + A: tab "Aankooporderlijnen"
    - Alt + G: tab "Goederenontvangsten"
    - Esc: venster sluiten
  - `ui_so.py`
    - Ctrl + Enter: ophalen data
    - Esc: venster sluiten

- 🪄 **UI fixes**
  - `ui_po.py` en `ui_so.py` komen nu altijd **boven andere vensters**, ook boven `ui_main` en `ui_detail`.
  - Verbeterde logica voor positioning en focus van child-windows.

- 🗂️ **Instellingen & settings.json**
  - Extra labels toegevoegd in `field_labels`, zodat aanpassingen direct vanuit JSON gebeuren.
  - Kolomkoppen van zowel aankooporderlijnen (`po_por1`) als goederenontvangsten (`po_go`) nu dynamisch.

- 🔧 **Code cleanup**
  - Alle kolomdefinities naar mapping dictionaries verplaatst.
  - Functies opgesplitst en consistent gemaakt.

- 📦 **Structuurwijzigingen & nieuwe modules**
  - Volledige herstructurering van `ui_detail.py` en alle tabs verplaatst naar aparte modules.
  - Nieuwe aparte Python-files per tab:
    - `ui_po.py` (aankooporder-tab)
    - `ui_lastpurchase.py` (laatste aankoop-tab)
  - Nieuwe aparte utility-files:
    - `file_editor_dialog.py`
    - `help_dialogs.py`
    - `settings_dialog.py`
  - `ui_main.py` aangepast voor integratie file editor.
  - Menu rapportering uitgebreid met openstaande issues & requests.

- 🏷️ ATP
  - Sneltoetsen toegevoegd: Ctrl + Enter (ophalen), Page Up/Down (magazijnkeuze).

- 🛒 Aankooporder
  - Sneltoetsen toegevoegd: Ctrl + Enter, Page Up/Down, Alt + A/G, Esc.

---

## [v5.0.0] – 2025-06-29
- 🎉 **Major release**: volledige herstructurering van `ui_detail.py` en alle tabs verplaatst naar aparte modules.
- 📦 Nieuwe aparte Python-files per tab:
  - `ui_lisa.py` (LISA-tab)
  - `ui_sap.py` (SAP-tab)
  - `ui_purchase.py` (Aankoop-tab)
  - `ui_sales.py` (Verkoop-tab)
  - `ui_return.py` (Laatste aankoop-tab)
  - `ui_logistics.py` (Logistiek-tab)
  - `ui_atp.py` (ATP-tab)
- 🏷️ Alle tabs gebruiken nu **headers mapping dictionaries**, zodat kolomkopteksten eenvoudig aanpasbaar zijn.
- ⚡ **Nieuw**: ATP-tab toegevoegd voor realtime beschikbaarheidsplanning, inclusief verkooporders en aankoopbestellingen.
- 💬 ALT-sneltoetsen voor snelle tabnavigatie behouden.

---

## [v4.2.3] – 2025-06-25
- 📋 Verbeterd: kopieerfunctie van verzamellijst (ART/VTA) exporteert nu ook **Outlook- en Word-compatibele HTML-tabellen**.

---

## [v4.2.2] – 2025-06-24
- ➕ Toegevoegd: kolommen **MD_SupplNbr** en **MD_Suppl** aan *PRJ Art.*-tab (VTA).
- 📋 Deze tonen respectievelijk het masterdata leveranciersnummer en -naam per artikel.

---

## [v4.2.1] – 2025-06-21
- 📏 Max- en min-size ingesteld op detail- en projectvenster.
- 🖱️ Dubbelklik op itemcode of omschrijving opent detailvenster.

---

## [v1.4.1] – 2025-06-14
- ➕ Toegevoegd: verzamelknop, leeg-knop en “Selecteer alles” bij Project ART-tab.
- 📋 Verzamelde rijen kunnen worden gekopieerd naar klembord in TSV + HTML.
- ❌ Leeg-knop deselecteert alle checkboxes in ART-tab.
- 🪄 Zelfde verzamel-functionaliteit als in standaard zoekresultaten.
- ♻️ Code opgeschoond en uitgelijnd met hoofdvenster.

---

## [v1.4.0] – 2025-06-14
- 🔍 Nieuw zoektype 'Project' met aangepaste UI.
- 🧠 Tooltip past zich aan op zoektype.
- 🧼 Verbergt zoekmodus en voorraadopties bij projectmodus.
- 📄 Changelog zichtbaar in menu → Help → Changelog.
- 🧾 `help.md` en `changelog.md` verplaatst naar submap `/docs`.
- 📁 FileEditorDialog hergebruikt voor changelog- en helpbestanden.

---

## [v1.3.2] – 2025-06-14
- 🆕 Nieuw: dropdown in instellingen om standaard zoektype te kiezen.
- 🛠️ Verbeterd: artikeltabel toont nu correcte kolommen voor projecten.
- 🐛 Fix: crash opgelost bij dubbele klik zonder selectie.

---

## [v1.3.1] – 2025-06-12
- 🐞 Bug opgelost in labelweergave.
- ⚙️ Verbeterde instellingsdialoog.

---

## [v1.3.0] – 2025-06-01
- 🆕 Nieuw: tabblad VTA toegevoegd aan projectweergave.
- 🎨 Verbeterd: labels in zoekvenster herschikt.

---

## [v1.2.0] – 2025-05-20
- 🚀 Initieel projectzoekvenster toegevoegd.
- 📦 Basis ondersteuning voor ART-gegevens.
