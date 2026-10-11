# ArticleSearch — Ontwikkelcontext v29 (geconsolideerd)
_Gegenereerd op 2026-10-10 — technische referentie voor nieuwe chats in dit Claude Project_

> **📦 v29 = één geconsolideerd context-bestand.** Het vervangt alle eerdere
> versies en voegt samen wat over meerdere, uit elkaar gegroeide bestanden
> en chats verspreid zat:
> - `articlesearch_context_v26.md` (Project-bron, 2026-08-31)
> - `articlesearch_context_v24 (2).md` (Project-bron, 2026-09-01 — een
>   aparte tak met de PaymentsDue-vervolgen die nooit in v26 kwamen)
> - v27 en v28 (2026-08-31, enkel in een eerdere chat, nooit in de
>   Project-bronnen terechtgekomen)
> - de sessie van 2026-09-11 (Open Elements overview — had geen
>   context-bestand)
> - de signing-sessie van 2026-09-17 (`04-smartscreen-defender-signing.md`)
> - `CGK_Searchtool_context_v1.md` + `v2.md` (samengevat in §13)
> - de sessie van 2026-10-10 (GitHub-token)
>
> **Bron van waarheid voor de code:** de bestandsversies en rollen in §3
> komen rechtstreeks uit de headers van de bestanden op GitHub, commit
> `c44c17b` (= release **15.6.0**, 2026-10-10 12:36). Wat in oudere
> context-bestanden anders stond, is hier overschreven door wat effectief
> in de code staat.
>
> **Veilig te verwijderen uit de Project-bronnen na het opslaan van dit
> bestand:** `articlesearch_context_v26.md`,
> `articlesearch_context_v24 (2).md`. **Laten staan:**
> `CGK_Searchtool_context_v1.md`/`v2.md` (bron voor de aparte
> migratie-chat), `peppol_ontwerpbrief_v1.md`,
> `04-smartscreen-defender-signing.md`.
>
> **Niet geverifieerd in deze consolidatie:** bestanden zonder
> versieheader zijn niet inhoudelijk doorgenomen (in §3 gemarkeerd met ◦);
> hun rol komt uit eerdere sessies of uit de bestandsnaam.

---

## 1. Projectoverzicht

| | |
|---|---|
| **App** | ArticleSearch ("Artikelzoeker") — PySide6 desktop-app (Windows), CGK Group |
| **Doel** | Artikels, projecten, business partners (BP), VTA en productie-stock opzoeken; financiële overzichten (Credit Control, Open Elements, Betalingsgedrag); Peppol-statuscontrole; labels; urenregistratie |
| **Developer** | Bart Bossuyt (Author in elke versieheader) |
| **Stack** | Python 3.12, PySide6 6.9.0, requests, msal 1.31.0 + msal-extensions 1.3.1, pandas 2.1.4, openpyxl, reportlab + python-barcode, Markdown, PyInstaller 6.11.1 |
| **Backend** | Centrale REST-API `https://api.cgk-group.com` (test: `api-test.cgk-group.com`) → SAP Business One (HANA, schema `SBOCGKLIVE`) en LISA-tabellen |
| **Auth** | Azure AD (MSAL) voor app-toegang en AD-groepen; per databron een eigen OAuth-achtige API-client (`TokenManager`) |
| **Taal** | Nederlandstalige UI, comments en meldingen; Engelse variabelen. Taalkeuze NL/EN in instellingen (beperkt gebruikt) |
| **Lokale werkmap** | `C:\searcharticle_code` (platte structuur, alles in de hoofdmap; venv in `.venv`) |
| **Repo** | `barremans/articlesearch` — **publiek** |
| **Huidige versie** | **15.6.0** (2026-10-10) |
| **Distributie** | PyInstaller (`SearchArticle.spec`) → Inno Setup-installer → GitHub Release → Microsoft Intune (SYSTEM). Installeert in `C:\ArticleSearch` |
| **Opvolger** | CGK_Searchtool (mapstructuur, versie 26.x) — in migratie, zie §13. ArticleSearch blijft daarnaast bestaan |

---

## 2. Architectuur

### 2.1 Opstart (`main.py`)

```
main.py
 ├─ config.OFFLINE_MODE?            → ja: geen toegang
 ├─ try_azure_login(timeout 30 s)   → permissions_azure.connect_to_azure_ad()
 │     MSAL PublicClientApplication met persistente, DPAPI-versleutelde cache
 │     (%LOCALAPPDATA%\ArticleSearch\msal_cache.bin) → na de eerste login
 │     een stille token-refresh, geen browser-popup meer bij elke start
 ├─ has_base_access()               → lid van minstens één BASE_ACCESS_GROUP?
 │     nee → NoAccessWindow (ui_no_access.py)
 ├─ preload_tokens()                → ArticleSearch- en StockInfo-token
 └─ MainWindow (ui_main.py)
```

### 2.2 Datastroom

```
UI-scherm (ui_*.py)
   │  zoekterm + parameters
   ▼
data_request.send_data_request()          of een eigen *_info.py per feature
   │  payload per 'kind' (data | project | bp | cc), ConfigurationID uit config.py
   ▼
*_token.py / auth.py  → token_manager.TokenManager (cache + auto-refresh)
   ▼
POST {base_url}/api/datarequest           (Prod-datasets opslaan: apart import-endpoint)
   ▼
Response { IsError, Data, ... } → genormaliseerd → UI
```

**Vaste patronen:**
- **Per feature drie lagen:** `*_token.py` (auth-header per client) /
  `*_info.py` (payload + normalisatie, geen Qt) / `ui_*.py` (scherm).
- **Elke databron een eigen API-client** (client_id + secret in
  `config.py` → `API_CLIENTS`) en een eigen `ConfigurationID`
  (`API_ENVIRONMENTS[env]`). Bewust, voor toegangscontrole per databron.
- **Twee respons-vormen:** de oudere endpoints geven een `"item"`/`"Item"`-
  wrapper (afgehandeld in `data_request.py`, `artbp_info.py`); de nieuwere
  (PaymentsDue, Prod Stock) geven een platte lijst in `Data`. Daarom
  hebben die een eigen `_post()` en hergebruiken ze `send_data_request()`
  niet.
- **Nieuwe schermen laden niets bij openen** — pas na klik op "Ophalen".
- Bijna alle niet-basis databronnen bestaan enkel in `live`, niet in `test`.

---

## 3. Bestandsoverzicht (stand GitHub, release 15.6.0)

◦ = geen versieheader; rol uit eerdere sessies of afgeleid uit de naam,
niet inhoudelijk doorgenomen.

**Kern**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `main.py` | 1.1.0 | 134 | Entry point: security gate (offline-check, Azure AD-login met timeout, basisgroepen), preload van tokens, start `MainWindow` of `NoAccessWindow` |
| `config.py` | 1.3.1 | 253 | Omgevingen, ConfigurationID's (`API_ENVIRONMENTS`) en clients (`API_CLIENTS`). **Bevat secrets** |
| `auth.py` | ◦ | 65 | Auth-headers voor de standaardclient `ArticleSearch` en de `BpS`-uitzondering; `preload_token()` |
| `token_manager.py` | ◦ | 211 | `TokenManager`: haalt en cachet tokens, tolerante veldherkenning, JWT-exp als terugval |
| `data_request.py` | ◦ | 189 | `send_data_request()`: payload per `kind` (data/project/bp/cc) en normalisatie van de respons |
| `settings.py` | 1.3.0 | 460 | Persistente instellingen in `settings.json`; alle `load_*`/`save_*`-functies (zie §5.5) |
| `settings_dialog.py` | 2.0.0 | 357 | Instellingen-venster, in tabbladen per groep |
| `permissions_azure.py` | 1.1.0 | 244 | Azure AD-login (MSAL) met persistente versleutelde cache, groepscheck `user_in_azure_group()`, `get_current_user_display_name()`, SharePoint-token |
| `version.py` | ◦ | 2 | `__version__` — aangepast door `bump_version.py` bij elke build |
| `updater.py` | 1.3.0 | 178 | Update-check via `version.txt` en release notes via de Releases API; zonder token |

**Hoofdvenster en artikeldetail**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `ui_main.py` | 1.18.0 | 2490 | Hoofdvenster: zoekscherm, resultatentabel, menu's, openen van alle submodules, Prod Stock Overview inline |
| `ui_detail.py` | 1.4.0 | 420 | Detail-venster van een artikel met alle tabs; ontvangt de volledige detail-payload |
| `ui_lisa.py` | 1.2.0 | 217 | Tab LISA: voorraad per locatie/magazijn; Min/Max uit `STOCK.SAP` (workaround) |
| `ui_sap.py` | 1.1.0 | 145 | Tab SAP: voorraad per magazijn incl. berekende vrije stock |
| `ui_dimensions.py` | 1.0.0 | 156 | Tab Dimensions: afmetingen en gewichten uit `MEASUREMENT_INFO` |
| `ui_purchase.py` | ◦ | 35 | Tab Aankoop |
| `ui_sales.py` | ◦ | 37 | Tab Verkoop |
| `ui_logistics.py` | ◦ | 41 | Tab Logistiek |
| `ui_lastpurch.py` | ◦ | 63 | Tab Laatste aankoop (`RET`) |
| `ui_atp.py` | ◦ | 196 | Tab ATP (beschikbaarheidsplanning) |
| `stock_info.py` | ◦ | 102 | `get_item_detail_stockinfo()`: volledige detail-payload (`WEZ7CY`) |
| `stock_token.py` | ◦ | 34 | Auth-headers client `StockInfo` (detail-payload) |
| `atp_token.py` | ◦ | 44 | Auth-headers client `Atp` |
| `oitmi_upload.py` | ◦ | 210 | `ImageUploader`-dialoog: afbeelding + beschrijving/leverancier uploaden |
| `oitmi_api.py` | ◦ | 12 | API-aanroep voor de afbeelding-upload (OITMI) |
| `oitmi_token.py` | ◦ | 16 | Auth-headers client `OITMI` |
| `upload_dialog.py` | ◦ | 86 | Upload-dialoog (in `hiddenimports` van de spec) |
| `base64_image_utils.py` | ◦ | 13 | Hulpfuncties voor base64-afbeeldingen |
| `ui_image_search.py` | ◦ | 1241 | Zoeken op afbeelding (niet doorgenomen) |

**Business Partner en Credit Control**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `ui_bp.py` | 1.2.0 | 401 | BP-venster: zoeken, headerpaneel, tabs Adressen/Contacten/Credit Control/Artikels; async ophalen |
| `ui_bp_header_panel.py` | ◦ | 303 | Headerpaneel met basis- en financiële kopgegevens; `CardType` bepaalt klant/leverancier |
| `ui_bp_helper.py` | ◦ | 94 | Hulpfuncties BP: `map_card_type()`, `extract_bp_core()`, `fmt_num()` |
| `ui_bp_addresses_tab.py` | ◦ | 186 | Tab Adressen met zoekbalk en detaildialoog |
| `ui_bp_contacts_tab.py` | ◦ | 221 | Tab Contacten met zoekbalk en detaildialoog |
| `ui_bp_articles_tab.py` | 1.5.0 | 501 | Tab Artikels (enkel leveranciers): lazy load, zoekbalk, eigen verzamellijst, sortering |
| `ui_bp_cc_detail_tab.py` | 1.3.0 | 280 | Tab Credit Control: vergrendeling op AD-groepen (CC-ACCESS-1), 5 detaillijsten |
| `ui_bp_cc_lists_tab.py` | ◦ | 477 | De 5 subtabs (Orders/Leveringen/Voorschotten/Facturen/Kredietnota's) |
| `ui_bp_cc_ordrl_dialog.py` | ◦ | 215 | Detaildialoog orderlijnen |
| `ui_bp_cc_dnl1_dialog.py` | ◦ | 133 | Detaildialoog leveringslijnen |
| `ui_bp_cc_dpi1_dialog.py` | ◦ | 145 | Detaildialoog voorschotlijnen |
| `ui_bp_cc_inv1_dialog.py` | ◦ | 126 | Detaildialoog factuurlijnen |
| `ui_bp_cc_rin1_dialog.py` | ◦ | 126 | Detaildialoog kredietnotalijnen |
| `bp_token.py` | ◦ | 43 | Auth-headers client `Bp` (BP-kaart) |
| `artbp_info.py` | 1.0.2 | 86 | `get_supplier_articles(card_code)`: artikels per leverancier (`KX9RLR`) |
| `artbp_token.py` | 1.0.0 | 41 | Auth-headers client `ArtBpSearch` |
| `cc_service.py` | ◦ | 179 | Dataservice Credit Control (niet doorgenomen) |
| `cc_token.py` | ◦ | 36 | Auth-headers Credit Control-clients |
| `security_cc.py` | ◦ | 56 | Vergrendeling Credit Control (niet doorgenomen) |
| `ui_CcBP.py` | ◦ | 487 | Apart Finance-scherm Credit Control over meerdere BP's; eigen groep `GPP_Finance` |
| `ui_CcBP_helper.py` | ◦ | 95 | Kolomvolgorde en labels voor `ui_CcBP.py` |

**Export / Finance**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `ui_docs.py` | ◦ | 364 | Open Elements: openstaande verkoop-/aankoopdocumenten (pandas) |
| `ui_docs_schema.py` | ◦ | 120 | Kolomschema en vertalingen voor Open Elements en de CC-dialogen |
| `security_docs.py` | ◦ | 54 | `is_unlocked()` voor Open Elements / CC BP (niet doorgenomen) |
| `ui_oeoverview.py` | 1.2.0 | 327 | Open Elements overview: 2 lokale bronbestanden → overzicht per verkoopmedewerker |
| `oeoverview_info.py` | 1.3.0 | 816 | Bedrijfslogica Open Elements overview (CSV/Excel inlezen, valideren, groeperen, wegschrijven) |
| `ui_duepayment.py` | 1.5.0 | 838 | Betalingsgedrag: tabs Klanten/Closed/Forecast, filters, sortering, export |
| `duepayment_info.py` | 1.1.0 | 146 | Payload en normalisatie voor de 3 PaymentsDue-endpoints |
| `duepayment_token.py` | 1.0.0 | 89 | Auth-headers clients `DuePaymentDetail` en `DuePaymentOverview` |

**Productie Stock Overview**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `prod_info.py` | 1.3.0 | 309 | Datasets opvragen/opslaan, stock-overzicht, normalisatie van artikelnummers |
| `prod_token.py` | 1.0.0 | 76 | Auth-headers clients `ProdDataset` en `ProdStock` |
| `ui_prod_datasets_dialog.py` | 1.5.0 | 473 | Beheer van Prod-datasets met eigenaarschap en beheerdersgroep |
| `ui_prod_stock.py` | 1.0.0 | 265 | Oud pop-upvenster Prod Stock — **niet meer in gebruik** |

**Project, VTA, orders**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `project_ui.py` | ◦ | 466 | Projectvenster (niet doorgenomen) |
| `project_token.py` | ◦ | 44 | Auth-headers client `Project` |
| `ui_vta.py` | ◦ | 277 | VTA-venster (niet doorgenomen) |
| `vta_token.py` | ◦ | 43 | Auth-headers client `VTA` |
| `ui_po.py` | ◦ | 231 | Aankooporder-tab/venster |
| `po_token.py` | ◦ | 44 | Auth-headers client `Po` |
| `ui_so.py` | ◦ | 175 | Verkooporder-tab/venster |

**Peppol**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `ui_peppol.py` | 2.0.3 | 727 | Peppol-controlescherm: documentinfo, status, vertaalde en gededupliceerde meldingen |
| `pep_token.py` | ◦ | 43 | Auth-headers client `PEP` |

**Bug/feature melden (uniform feedbackpakket)**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `github_feedback.py` | 1.0.0 | 241 | `GitHubFeedbackClient`: Issue aanmaken en open meldingen ophalen. Uniform, geen Qt, geen token |
| `github_feedback_config.py` | 1.0.0 | 48 | App-naam, repo, naam van de melder, app-versie — enige app-specifieke bestand van het pakket |
| `github_secret_local.example.py` | 1.0.0 | 23 | Sjabloon voor `github_secret_local.py` (zonder token) |
| `check_github_secret.py` | 1.0.0 | 264 | Controle vóór push en build: geen token in git, token aanwezig en geldig |
| `bug_report_dialog.py` | 2.0.0 | 172 | `BugDialog`: bug of feature melden |
| `github_cases.py` | 2.0.0 | 143 | `show_github_cases()`: open bugmeldingen en feature-aanvragen tonen |

**Overige schermen en hulpmodules**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `ui_no_access.py` | ◦ | 48 | "Geen toegang"-venster (NL/EN) |
| `ui_labels.py` | ◦ | 167 | Labelscherm |
| `label/label_generator.py` | ◦ | 126 | Label-PDF met barcode |
| `label/label_settings.py` | ◦ | 52 | Labelinstellingen |
| `label/label_settings_dialog.py` | ◦ | 112 | Dialoog labelinstellingen |
| `ui_timings.py` | ◦ | 501 | Urenregistratie: SharePoint-bestanden downloaden en verwerken |
| `ui_timings_17_13.py` | ◦ | 475 | Oudere variant van `ui_timings.py` |
| `help_dialogs.py` | ◦ | 109 | Help- en changelog-dialogen |
| `file_editor_dialog.py` | ◦ | 48 | `FileEditorDialog` (qss/md bewerken) |
| `translations/__init__.py` | ◦ | 10 | Vertaallaag |
| `translations/nl.py` | ◦ | 18 | Teksten NL |
| `translations/en.py` | ◦ | 18 | Teksten EN |

**Build en release**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `SearchArticle.spec` | 1.3.0 | 147 | PyInstaller-spec: tokencontrole, `Analysis(["main.py"])`, `Tree("docs")`, `Tree("assets")` |
| `build_installer15.bat` | 1.4.0 | 379 | Build + Inno Setup-installer, signeren en verifiëren |
| `build_and_publish.ps1` | ◦ | 206 | Vraagt parameters, zoekt het certificaat, bouwt en publiceert |
| `publish.ps1` | ◦ | 133 | Release-gate op handtekening, GitHub Release, `version.txt`, commit + push |
| `bump_version.py` | ◦ | 59 | Verhoogt `__version__` in `version.py` (patch/minor/major) |
| `export_to_usb5.bat` | ◦ | 375 | Export van het project naar USB |
| `export_to_usb4.bat` | ◦ | 200 | Export naar USB (oud) |
| `setup_from_usb.ps1` | ◦ | 78 | Project opzetten vanaf USB |

**Oud / test**

| Bestand | Versie | Regels | Rol |
|---|---|---|---|
| `main_1_0_0.py` | ◦ | 99 | Oude versie van `main.py` (kandidaat voor `zzz/`) |
| `getBearer.py` | ◦ | 69 | Los hulpscript om een bearer-token op te halen |
| `setup.py` | ◦ | 21 | Oud setup-script |
| `test.py` | ◦ | 4 | Testscript |
| `test_cc_v2_call.py` | ◦ | 32 | Testscript CC v2 |
| `test_unified.py` | ◦ | 209 | Testscript |

**Niet in git, wel nodig om te bouwen:** `github_secret_local.py` (het
GitHub-token; genegeerd via `.gitignore`-regel `*_secret_local.py`).

**Overige mappen:** `assets/` (iconen, `css/*.qss`), `docs/` (in de app
gebundeld: `changelog.md`, `help.md`, `pep_errors.json`), `label/`
(labelgenerator + lettertypes), `translations/`, `releases/latest/version.txt`
(door `publish.ps1` geschreven, door `updater.py` gelezen), `zzz/`
(archief, niet actief), `temp/` en `backup/` (kopieën, niet actief).

---

## 4. Databronnen en datacontracten

### 4.1 ConfigurationID's en clients (`config.py` v1.3.1)

`base_url`: live `https://api.cgk-group.com`, test
`https://api-test.cgk-group.com`. Secrets staan in `config.py` en worden
hier niet herhaald.

**ConfigurationID's** (`API_ENVIRONMENTS`)

| Sleutel | live | test | Gebruikt voor |
|---|---|---|---|
| `data_config_id` | `9423TC` | `0TY75H` | Artikelzoek (`send_data_request`, kind `data`) |
| `stock_config_id` | `6DIRXZ` | `7KQKVE` | Stock (ouder endpoint) |
| `stock_configP_id` | `WEZ7CY` | `YZ4KLG` | Detail-payload artikel (§4.3) |
| `project_configP_id` | `AXF4GX` | — | Project |
| `atp_configP_id` | `1IZDVW` | — | ATP |
| `po_configP_id` | `3EGOKM` | — | Aankooporders |
| `so_configP_id` | `C80TSJ` | — | Verkooporders |
| `bp_configP_Bp` | `U63P1T` | — | BP-kaart |
| `so_configP_Bp` | `OMW5IN` | — | BP-zoeklijst |
| `so_configP_Cc` | `OLH3RP` | — | Credit Control (v1) |
| `so_configP_CcV2` | `0B7JWA` | — | Credit Control v2 |
| `so_configP_CcBpV2` | `HG443N` | — | Credit Control per BP v2 |
| `so_configP_OE` | `4AA8DF` | — | Open Elements |
| `vta_config_id` | `G6HH9T` | — | VTA |
| `pep_config_id` | `FSOLI1` | — | Peppol-status (§4.5) |
| `artbp_configP_id` | `KX9RLR` | — | Artikels per leverancier (§4.4) |
| `duepayment_detail_configP_id` | `UIY02H` | — | PaymentsDue — Klanten (§4.6) |
| `duepayment_overview_configP_id` | `YCT5LR` | — | PaymentsDue — Closed (§4.6) |
| `duepayment_forecast_configP_id` | `HY04WB` | — | PaymentsDue — Forecast (§4.6) |
| `prod_dataset_configP_id` | `BAEIG0` | — | Prod-datasets opvragen (§4.7) |
| `prod_stock_configP_id` | `VX3PMC` | — | Prod stock-overzicht (§4.7) |
| `prod_dataset_import_path` | `/api/import/DATAPROD/U/dbname/SBOCGKLIVE` | — | Prod-dataset opslaan (pad, geen ID) |

De koppeling sleutel → gebruik komt uit eerdere sessies en de sleutelnamen; voor de oudere sleutels (`so_configP_*`, `stock_config_id`) is ze niet in de code nagekeken.

**Clients** (`API_CLIENTS`)

| Naam in code | client_id | Omgevingen |
|---|---|---|
| `ArticleSearch` | `ArticleSearch` | test, live |
| `StockInfo` | `StockInfo` | test, live |
| `StockInfoP` | `StockInfoP` | test, live |
| `OITMI` | `OITMI` | test, live |
| `Project` | `Project` | live |
| `Atp` | `AtpWhs` | live |
| `Po` | `PurchaseOrder` | live |
| `So` | `SalesOrder` | live |
| `Bp` | `businesspartneru` | live |
| `Cc` | `CreditControl` | live |
| `CcV2` | `CreditControl` | live |
| `CcBpV2` | `CreditControl` | live |
| `BpS` | `BpSearchMin` | live |
| `OE` | `OpenElements` | live |
| `VTA` | `VTA` | live |
| `PEP` | `SmartlynxStatusInv` | live |
| `ArtBpSearch` | `ArtBpSearch` | live |
| `DuePaymentDetail` | `DuePaymentDetail` | live |
| `DuePaymentOverview` | `DuePaymentOverview` | live |
| `ProdDataset` | `Datasetprod` | live |
| `ProdStock` | `ProdStockOverview` | live |

Overige constanten in `config.py`: `ENVIRONMENT` (uit instellingen),
`OFFLINE_MODE = False`, `CC_TAB_PASSWORD` (fallback-wachtwoord,
overschrijfbaar via env var), `CC_LOCK_DISABLED` (dev-bypass via env var —
mag in productie nooit actief zijn).

### 4.2 Artikelzoek (SAP HANA stored procedure)

`SBOCGKLIVE.ARV_SP_CGK_SEARCH_PRODUCT_DYNAMIC(zoekterm, mode, show_stock)`

| Prefix in zoekterm | Betekenis | `mode` (AND/OR) gebruikt? |
|---|---|---|
| `-` | Exact zoeken op kernwoorden (komma-gescheiden) | Ja |
| `*` | Vrij zoeken (LIKE) op kernwoorden | Ja |
| `/` | Zoeken op leveranciersartikelnummer | Nee |
| _(geen)_ | Intern artikelnummer, exact of wildcard (`%`/`_`) | Nee — bewust altijd OR tussen `o.ItemCode` en `p.INTERNIDPRODUCT` |

`show_stock`: `R` (ruw), `S` (met voorraad per locatie; enkel dan is
`QTYMININV` = "Min.Whs" aanwezig), `B` (beide).

### 4.3 Detail-payload artikel (`WEZ7CY` live / `YZ4KLG` test, client `StockInfo`)

`stock_info.get_item_detail_stockinfo(item_code)` → `Data[0]` met
basisvelden (`ItemCode`, `ItemName`, `FrgnName`, ...) en deze secties:

| Key | Vorm | Tab in Detail-venster |
|---|---|---|
| `STOCK.LISA` | list | LISA |
| `STOCK.SAP` | list | SAP |
| `MEASUREMENT_INFO` | dict | Dimensions |
| `FIN.PURCH` | list | Aankoop |
| `FIN.SALES` | list | Verkoop |
| `LOG` | dict | Logistiek |
| `RET` | list | Laatste aankoop |
| `DIG` | list | Afbeelding (+ upload via `oitmi_upload.py`) |
| `EXTRA_INFO`, `GROUP_INFO`, `STOCK.PL` | dict/dict/list | nog niet gebruikt |

- **MEASUREMENT_INFO:** prefix `S` = verkoop-, `B` = verpakkings-, `I` =
  inventaris-eenheid (aanname, standaard SAP B1); elk veld heeft een
  bijhorend `*UnitName`.
- **Bekende backend-bug:** `STOCK.LISA[].QTYMININV`/`QTYMAXINV` is de som
  over álle magazijnen, herhaald op elke rij. `STOCK.SAP` van dezelfde
  payload is wel correct. Workaround in `ui_lisa.py` v1.2.0 (zie §6.2);
  de bron zelf is nog niet hersteld.

### 4.4 Artikels per leverancier (`KX9RLR`, client `ArtBpSearch`)

`artbp_info.get_supplier_articles(card_code)` — zoekt altijd op
`@CardCode`. Respons `{"Data": [{"Item": {...}}, ...]}`. Getoond:
`ItemCode`, `SuppCatNum`, `ItemName`, `ItmsGrpCod`, `ItmsGrpNam`,
`UserText`, `LastPurPrc`, `LastPurCur`, `QtyPurchasedLast6Months`,
`QtyPurchasedLast12Months`. Niet getoond: `FrgnName`, `CardCode`,
`CardName`.

### 4.5 Peppol-status (`FSOLI1`, client `PEP` = `SmartlynxStatusInv`)

`POST /api/datarequest` met `{"ConfigurationID": ..., "Key": <documentnr>}`.
Respons: `INFO` (altijd 1 element: `SourceTable`, `DocumentType`,
`CardCode`, `CardName`, `NumAtCard`), `TASK`, `STATUS`.
- Documenttypes: OINV (factuur), ORIN (creditnota), ODPI (voorschot),
  OPOR (aankooporder). Eén leverancier: GF.
- `U_Message` kan **structureel afgekapt** zijn → regex-fallback naast
  `json.loads()`.
- Twee JSON-vormen: `Code`/`Description` en `code`/`detail` →
  case-insensitieve extractie.
- Dezelfde fout komt 2-3 keer voor (retries) → dedupliceren + teller.
- `docs/pep_errors.json`: genamespaced per leverancier
  (`{"GF": {"<code>": {...}}}`), meertalig (`{"nl": "..."}`), met
  `severity` (`error`/`warning`). Opzoeken moet **binnen** de namespace
  (`_lookup_error()`).
- Volledig contract en open ontwerpvragen: `peppol_ontwerpbrief_v1.md`.

### 4.6 Betalingsgedrag — PaymentsDue

| Endpoint | ConfigurationID | Client | Niveau | MultiKey |
|---|---|---|---|---|
| Detail | `UIY02H` | `DuePaymentDetail` | 1 rij per klant (gemiddelden) | `@months`, `@cardcode`, `@due` (`""` alles / `"0"` late betalers / `"1"` op tijd) |
| Overview | `YCT5LR` | `DuePaymentOverview` | 1 rij per document | `@months`, `@cardcode` |
| Forecast | `HY04WB` | `DuePaymentOverview` (hergebruikt) | 1 rij per openstaande factuur, met `VerwachteBetaaldatum` en `Vervalstatus` | `@months`, `@cardcode` |

Stored procedures: `ARV_SP_CGK_GET_AVG_DUE_PAYMENTS_DETAIL`,
`ARV_SP_CGK_GET_PAYMENTS_DUE_OVERVIEW`. Respons: platte lijst in `Data`.
Van `Vervalstatus` is enkel de waarde `"LATE"` gezien; daarom geen vaste
filter op dat veld.

### 4.7 Productie Stock Overview

| Wat | ConfigurationID / pad | Client (client_id) |
|---|---|---|
| Datasets opvragen | `BAEIG0`, MultiKey `@name`, `@owner` | `ProdDataset` (`Datasetprod`) |
| Dataset aanmaken/bijwerken (upsert op `CODE`) | `POST {base_url}/api/import/DATAPROD/U/dbname/SBOCGKLIVE`, platte body `CODE`/`NAME`/`ARTNBR`/`CHANGEBY`/`CHANGEDATE`/`LOCK`/`OWNER` | `ProdDataset` |
| Stock-overzicht | `VX3PMC`, MultiKey `@items`, `@del` = `","` | `ProdStock` (`ProdStockOverview`) |

- Tabel `CGK_PRODUCTION_DATASET`; velden `DS_Code`, `DS_Name`,
  `DS_ArtNbr`, `DS_ChangeBy`, `DS_ChangeDate`, `DS_Lock`, `DS_Owner`.
  **HANA-kolomnamen zijn hoofdlettergevoelig** (`"DS_Code"` met
  aanhalingstekens).
- Artikelnummers worden opgeslagen als zuivere komma-lijst
  (`_ITEM_JOIN_SEP = ","`); `parse_artnbr()` leest ook het oude
  `"\r\n,"`-formaat.
- Verwijderen bestaat niet: enkel `LOCK=1`.
- Stock-respons: `ArtCode`, `Omschrijving`, `StockHeden`, `MinSAP`,
  `MaxSAP`, `MaxRek`, `TotaalStock`, `Gereserveerd`, `InBestelling`,
  `Beschikbaar`, `KGOpVoorraad`, `BENPlatenPerPallet`, `NietCgk`,
  `U_customText`, `Stock_Algemeen`, `Stock_Antwerpen`, `Stock_Miami`,
  `LISA_Qty`.
- Niet bevestigd: veldnaam/formaat `CHANGEDATE`; nieuwe code =
  `max(DS_Code)+1` client-side (geen lock); geen chunking bij grote
  datasets; "Min. SAP" is één cijfer per artikel, niet per magazijn.

### 4.8 Open Elements overview (geen API)

Lokale verwerking van twee SAP B1-exports (openstaande orders en
leveringen, CSV of Excel) door `oeoverview_info.py`: groeperen per
verkoopmedewerker (SalesOwner, terugval DocOwner), filteren op leeftijd
(orders > 6 maanden, leveringen > 1 maand), wegschrijven per medewerker
als xlsx en/of csv met kolom "Openstaand" en een totaalrij.

---

## 5. Hoofdvenster, menu's en toegang

### 5.1 Zoektypes (`search_type_select`)

`Artikel`, `Project`, `BP`, `VTA`, `Prod`. **De itemtekst is "Artikel",
niet "Standaard"** — elke vergelijking en de instelling
`default_search_type` moeten daarmee overeenkomen.

### 5.2 Menu's

| Menu | Items |
|---|---|
| Bestand | Afsluiten |
| Instellingen | Kies omgeving (test/live) · Instellingen wijzigen... · Label-instellingen... · Bewerk style.qss / detail.qss / upload.qss |
| Export | Open Elements · Open Elements overview... · Open Credit Control (CC BP) · Betalingsgedrag... |
| Tools | Timings (urenregistratie) · API check (Peppol) |
| Rapporteren | Bug of feature melden... · Show open cases |
| Help | Help · Over... (met "Update nu" en "Wat is er nieuw?") · Changelog... |

### 5.3 Toegangsrechten (Azure AD-groepen)

| Onderdeel | Vereist | Waar |
|---|---|---|
| App starten | `Alle gebruikers` of één van `CGK-APP-L1` t.e.m. `CGK-APP-L6` | `main.py` → `BASE_ACCESS_GROUPS` |
| BP → tab Credit Control: de 5 detaillijsten | `CGK-APP-L2`, `L3`, `L4` of `L6` | `ui_bp_cc_detail_tab.py` → `CC_ACCESS_GROUPS` |
| BP → financiële kopgegevens (kredietlimiet, saldo, ...) | iedereen | bewust niet vergrendeld |
| Export → Open Elements, Open Elements overview, Betalingsgedrag | `GPP_Finance` + niet offline | `ui_main.py` |
| Export → Open Credit Control (CC BP) | `GPP_Finance` + niet offline + `security_docs.is_unlocked()` | `ui_CcBP.py` |
| Tools → Timings | `CGK-APP-L1` | `ui_main.py` |
| Tools → API check (Peppol) | `CGK-APP-L1` of `CGK-APP-L2` | `ui_main.py` |
| Prod-datasets bewerken | eigenaar (ook bij benadering) of `CGK-APP-L6` (beheerder); bekijken kan iedereen | `ui_prod_datasets_dialog.py` |

Groepen worden bij de login één keer opgehaald en gecachet;
`user_in_azure_group()` doet geen extra netwerk-call.

### 5.4 Sneltoetsen en gedrag

- `Ctrl+Return` zoeken · `Ctrl+O` geselecteerde rij openen · `Ctrl+L`
  label · `F1` help · `Delete` zoekveld (bij Prod: het filter) wissen ·
  `Ctrl+E` exporteren (enkel bij Prod).
- Checkbox in kolom 0 ("Selectie") → verzamellijst, kopieerbaar als
  HTML-tabel (Outlook/Word).
- Dubbelklik op een rij: artikel → `DetailWindow`; BP → `BpWindow`.
- Rechtsklik: kopieer cel/rij, toon detail, genereer label.
- QSS wordt live herladen (`QFileSystemWatcher`).
- Kolomkoppen komen uit de instellingen (`COLUMN_HEADERS_S`/`_DEFAULT`),
  niet uit de code.

### 5.5 Instellingen (`settings.py` v1.3.0, `settings.json`)

Sleutels: `default_search_type`, `environment`, `show_stock`,
`detail_modal`, `language`, `tab_order`, `project_tab_order`,
`bp_default_type`, `prod_default_dataset_name`,
`prod_default_dataset_owner`, `prod_default_warehouse`,
`oeoverview_default_input_folder`, `oeoverview_default_output_folder`,
`label_settings`, `field_labels`, `main_qss_path`, `detail_qss_path`,
`upload_qss_path`. Ontbrekende sleutels worden bij het laden aangevuld
uit `DEFAULT_SETTINGS`; migratie is nooit nodig.

`settings_dialog.py` v2.0.0 is ingedeeld in tabbladen: Algemeen ·
Business Partners · Productie Stock Overview · Open Elements overview ·
Tab-volgorde. Beperkte keuzes zijn echte keuzelijsten, geen vrije tekst.

Laatst gebruikte exportmappen staan in `QSettings` (org "CGK Group", app
"ArticleSearch"), niet in `settings.json`.

---

## 6. Modules — huidige stand per onderdeel

### 6.1 Artikel-resultatentabel (`ui_main.py` v1.18.0)

- **SORT-1:** dubbelklik op kolomkop "Art.Nr.", "Leverancier"
  (alfabetisch), "Qty", "Prijs" (numeriek, op ruwe API-waarde). Matching op
  de getoonde koptekst (`SORTABLE_ARTICLE_HEADER_LABELS`).
- **MINWHS-KLEUR-1:** cel "Min.Whs" lichtgroen (`#d9f2d9`) als > 0
  ("standaard artikel").
- **QTYKLEUR-1:** cel "Qty" geel (`#fff3b0`) als het **totaal per
  (Art.Nr., Magazijn)** onder Min.Whs zit. Min.Whs geldt per magazijn,
  niet per locatie — per rij vergelijken is fout.
- **KOLOMBREEDTE-1:** alle kolommen `Interactive` (versleepbaar,
  dubbelklik = autofit); breedtes gaan verloren bij een nieuwe zoekactie.
- "Geen voorraad"-melding bij Artikel + Toon voorraad = S + 0 resultaten.
- Ruwe rijdata blijft bewaard in `self._last_article_data`.

### 6.2 Detail-venster (`ui_detail.py` v1.4.0)

Tabs: LISA, SAP, Dimensions, Aankoop, Verkoop, Logistiek, Laatste aankoop,
Afbeelding, ATP.
- **LISA** (`ui_lisa.py` v1.2.0): Min.Whs/Max.Whs komen uit `STOCK.SAP`
  (`{WhsName: (MinStock, MaxStock)}`) wegens de backend-bug (§4.3);
  terugval op de LISA-waarde met een waarschuwende tooltip. Gele
  markering "Beschikbaar" per magazijn gesommeerd.
- **SAP** (`ui_sap.py` v1.1.0): zelfde gele markering, per magazijn.
- **Dimensions** (`ui_dimensions.py` v1.0.0): Veld/Waarde-tabel uit
  `MEASUREMENT_INFO`, geen extra API-call.
- **Afbeelding-upload (OITMI):** velden vooringevuld volgens
  OITMI-waarde → `vendor_hint` uit de zoekresultaat-rij → meest recente
  `RET`-record. `vendor_hint_id`/`vendor_hint_name` komen mee vanuit
  `ui_main.py`.
- LISA- en SAP-tabs zoeken ruwe veldnamen op via het **label**
  (`_raw_key_for_label()`); een gewijzigd label in `settings.py` laat de
  kleur stil verdwijnen.

### 6.3 Business Partner (`ui_bp.py` v1.2.0)

Headerpaneel + tabs Adressen, Contacten, Credit Control, Artikels.
- **Artikels** (`ui_bp_articles_tab.py` v1.5.0): enkel bij
  `CardType == "S"`; lazy load bij eerste bezoek; eigen verzamellijst;
  zoekbalk op Art.Nr./Leverancier Art.Nr./Omschrijving; sorteren op
  `LastPurPrc` en de twee afnamekolommen.
- **Credit Control** (`ui_bp_cc_detail_tab.py` v1.3.0): CC-ACCESS-1. De
  CC-fetch en de kopgegevens zijn er voor iedereen; enkel het vullen van
  de 5 detaillijsten zit achter `is_unlocked()`. Dit was ooit een echt
  datalek (data geladen maar visueel verborgen) en is twee keer hersteld.
- `ui_CcBP.py` is een **apart** Finance-scherm met eigen groep
  `GPP_Finance`; bewust los van CC-ACCESS-1.

### 6.4 Betalingsgedrag (`ui_duepayment.py` v1.5.0)

Tabs **Klanten** (Detail), **Closed** (Overview, vast gefilterd op
`Status != "Open"`), **Forecast** (open facturen met verwachte
betaaldatum, standaard daarop gesorteerd). Live zoekbalk per tab,
kolomsortering via `_SortItem`, filter "Verschil vervaldatum" op Closed,
live totaal "Openstaand (zichtbaar)", export CSV/XLSX/beide (map wordt
geopend en onthouden), invoer van Klanten wordt overgenomen naar de andere
tabs, dubbelklik op een klant → Forecast. Sneltoetsen `Ctrl+Return`,
`Ctrl+E`, `Alt+1/2/3`, `Esc`.

### 6.5 Productie Stock Overview (zoektype "Prod")

- Resultaten **inline in de hoofdtabel**, niet in een pop-up
  (`ui_prod_stock.py` wordt niet meer geïmporteerd).
- Datasetlijst wordt **asynchroon** geladen (`_ProdDatasetLoaderThread`,
  SPEED-PROD-1) zodat "Prod" als standaard zoektype de opstart niet
  blokkeert.
- Magazijnfilter en tekstfilter wijzigen enkel de weergave van de al
  opgehaalde data.
- Kleuren: Min. SAP > 0 groen · Stock vandaag < Min. SAP geel · een
  magazijnkolom < 1 rood, **enkel als Min. SAP > 0**, voor alle drie de
  magazijnkolommen (v1.17.0).
- Standaard gesorteerd op Art.Nr.; dubbelklik-sortering op Art.Nr. en
  Omschrijving. Kolombreedtes in `PROD_COLUMN_WIDTHS`;
  `setStretchLastSection(False)`.
- Datasetbeheer (`ui_prod_datasets_dialog.py` v1.5.0): eigenaar =
  ingelogde AD-gebruiker; bewerken enkel voor de eigenaar (ook bij
  benaderende naam, `difflib` ≥ 0,6) of `CGK-APP-L6`; anderen zien
  alleen-lezen. Plakken normaliseert artikelnummers zichtbaar.

### 6.6 Open Elements overview (`ui_oeoverview.py` v1.2.0)

Twee bestandskeuzes (orders, leveringen) met elk "Bladeren...";
herkenning op bestandsnaam is enkel een voorselectie. Standaardmappen uit
Instellingen, anders de laatst gebruikte. `oeoverview_info.py` v1.3.0:
CSV én Excel, slaat voettekstrijen over (`_is_data_row()` op `DocNum`),
herkent omgewisselde bestanden.

### 6.7 Peppol-controlescherm (`ui_peppol.py` v2.0.3)

Volledig herontworpen (cutover uit testbestand `ui_peppol_v2.py`):
documentinfo, statusindicator op basis van ernst (✅/⚠️/🔴/⏳), vertaalde
en gededupliceerde meldingen, detail-pop-up bij dubbelklik, onbekende
codes gemarkeerd met "Kopieer ruwe boodschap" en "Meld via GitHub
(Feature)" (opent `BugDialog` vooringevuld).

### 6.8 Updates (`updater.py` v1.3.0)

- Update-check: leest `releases/latest/version.txt` via
  `raw.githubusercontent.com` (regel 1 = versie, regel 2 = download-URL).
- "Wat is er nieuw?": release notes (`body`) van de laatste GitHub
  Release via de Releases API. Niet verwarren met `docs/changelog.md`
  (lokaal, Help → Changelog).
- **Geen token meer.** Alles is anoniem leesbaar omdat de repo publiek is.

### 6.9 Bug of feature melden (uniform feedbackpakket, sinds 15.6.0)

| Bestand | Rol |
|---|---|
| `github_feedback.py` | `GitHubFeedbackClient`: `submit_report()` (1 call, `POST /issues`, label `bug` of `enhancement`), `get_open_reports()`. Geen Qt, geen token |
| `github_feedback_config.py` | Enige app-specifieke bestand: `APP_NAME`, `GITHUB_OWNER`, `GITHUB_REPO`, `get_reporter_name()`, `get_app_version()` |
| `github_secret_local.py` | `GITHUB_TOKEN = "..."` — **niet in git** |
| `github_secret_local.example.py` | Sjabloon zonder token |
| `check_github_secret.py` | Controle: geen token in git, token aanwezig en door GitHub aanvaard |
| `bug_report_dialog.py`, `github_cases.py` | De twee schermen; aanroep ongewijzigd |

- Een melding is altijd een **Issue**. Geen branch, bestand of Pull
  Request meer.
- De kopregel van elke melding vermeldt melder, tijdstip en app-versie;
  `clean_body_text()` knipt die regel weg bij het tonen — het formaat
  "kopregel, lege regel, omschrijving" niet wijzigen.
- "Je naam" wordt ingevuld met de AD-naam en is dan read-only; zonder
  naam blijft het veld bewerkbaar.
- Bij een ongeldig token valt het **lezen** terug op anoniem; het
  verzenden geeft een Nederlandstalige melding.
- Het pakket is bedoeld voor al Barts apps; uitrol staat in
  `GITHUB_FEEDBACK_UITROL.md`.

### 6.10 Overige

- **Labels** (`label/`, `ui_labels.py`): PDF + barcode. ◦
- **Timings** (`ui_timings.py`): urenregistratie via SharePoint. ◦
- **Project** (`project_ui.py`), **VTA** (`ui_vta.py`), **PO/SO**
  (`ui_po.py`, `ui_so.py`), **ATP** (`ui_atp.py`), **Open Elements**
  (`ui_docs.py`): bestaand, niet opnieuw doorgenomen. ◦ In `ui_docs.py`
  zijn de exportknoppen ooit zonder koppeling aangetroffen.

---

## 7. Build, signing, release en deploy

### 7.1 Scripts

| Script | Rol |
|---|---|
| `build_and_publish.ps1` | Vraagt versie-bump (patch/minor/major), installer J/N, signeren J/N, publiceren J/N; zoekt het signing-certificaat en geeft de thumbprint door; roept de build en daarna `publish.ps1` aan. Geen PowerShell 7-only syntax |
| `build_installer15.bat` (v1.4.0) | `bump_version.py` → PyInstaller via `SearchArticle.spec` → kopie van losse bestanden en mappen → signeren → Inno Setup-script genereren en compileren → installer signeren en verifiëren. Niet-interactief via `AS_BUMP_PART`, `AS_MAKE_INSTALLER`, `AS_DO_SIGN`, `AS_SIGN_THUMBPRINT` |
| `SearchArticle.spec` (v1.3.0) | Draait eerst `check_github_secret.py`; stopt de build bij een fout. `Analysis(["main.py"])`, `Tree("docs")`, `Tree("assets")` |
| `publish.ps1` | Leest de versie uit `version.py`; **weigert te publiceren zonder geldige Authenticode-handtekening**; maakt/hergebruikt de GitHub Release (`gh`), uploadt de installer, schrijft `releases/latest/version.txt`, commit + pusht `version.py` en `version.txt`, en controleert de exitcode van `git push` |
| `bump_version.py` | Past enkel `version.py` lokaal aan |

**Volgorde bij een release:** gewijzigde bestanden committen (GitHub
Desktop) → `.\build_and_publish.ps1` → release notes invullen op GitHub.

### 7.2 Installer (Inno Setup, Intune)

Vaste `AppId` `{A1B2C3D4-E5F6-47A8-9023-ABCDEF123456}` (ook als `APPGUID`
in de bat — samen wijzigen), `PrivilegesRequired=admin`, installeert stil
in `C:\ArticleSearch`, `CloseApplications=force`,
`RestartApplications=no` (Intune draait als SYSTEM en mag geen GUI
starten), `OutputDir=.`. Intune-randvoorwaarden zijn niet onderhandelbaar.

### 7.3 Signing

- Zelfondertekend certificaat `CN=CGK Local Signing` uit de
  certificaatstore (thumbprint `4da652bf…532ef7`). Sinds bat v1.4.0 en de
  release-gate in `publish.ps1`: een mislukte of ongeldige handtekening
  **stopt** de build en de publicatie.
- SmartScreen op Intune-toestellen: opgelost met een **Certificate
  Indicator** (Allow) in Microsoft Defender for Endpoint, geldig voor alle
  apps met dit certificaat. Details en stappen:
  `04-smartscreen-defender-signing.md`. Open: een publiek vertrouwd
  code-signing-certificaat.

### 7.4 Wat automatisch meekomt in een build

- Elk `.py`-bestand dat (rechtstreeks of onrechtstreeks) vanuit `main.py`
  geïmporteerd wordt — geen `hiddenimports` nodig.
- De mappen `docs/` en `assets/` (bewezen betrouwbaar).
  **`Analysis(datas=...)` voor een los bestand naast de exe werkte niet op
  een geïnstalleerde pc** — nieuwe databestanden horen in `docs/`.
- `github_secret_local.py` wordt als module in de exe gebundeld.

### 7.5 Versies en changelog

- Releases (tags op GitHub): 15.0.0 t.e.m. 15.0.5 · 15.1.0 · 15.2.0 en
  15.2.1 (08-31) · 15.3.0 (08-31) · 15.4.0 (09-01) · 15.5.0 en 15.5.1
  (09-11) · **15.6.0 (10-10)**. Lokaal bestond ook 15.5.2 (niet
  gepubliceerd).
- **`docs/changelog.md` loopt sinds 15.3.0 één nummer achter op de
  releases:** release 15.3.0 (08-31, opstartsnelheid) heeft geen eigen
  entry; de entry `[15.3.0]` (09-01) is uitgebracht als 15.4.0, en
  `[15.4.0]` (09-11) als 15.5.0/15.5.1. Er ontbreekt dus weinig inhoud;
  vooral de nummering verschilt. `[15.6.0]` klopt wel.
- `docs/help.md` vermeldt nog versie 15.4.0.

---

## 8. GitHub en tokens

### 8.1 Wat er misliep (bevestigd op 2026-10-10)

GitHub trekt een token **automatisch in zodra het in een publieke repo
gepusht wordt** (Secret Scanning). Het token stond hardcoded in getrackte
bestanden van een publieke repo. De security log van het account toont
zeven intrekkingen, alle met reden `token_scan`; geen enkel token is
verlopen of manueel verwijderd.

| Aangemaakt | Ingetrokken | Levensduur |
|---|---|---|
| vóór 15/04 (3 tokens, o.a. "Article search" en "Updater token") | 04/08 14:58 | onbekend |
| 06/08 12:17 | 06/08 14:37 | 2 u 20 min |
| 06/08 14:55 | 31/08 08:57 | 25 dagen (tot de push met "Allow secret") |
| 31/08 09:36 | 31/08 10:17 | 41 min |
| 16/09 13:55 | 16/09 14:08 | 13 min — niet via deze repo; `Project_generator` werd die dag publiek |

De eerdere verklaring ("verlopen/ingetrokken, oorzaak onbekend",
sessies 20-23 en 26) is hiermee vervangen. "Allow me to expose this
secret" laat enkel de push door en beschermt het token niet.

### 8.2 Huidige opzet

- Token: fine-grained, enkel repo `articlesearch`, **Issues: Read and
  write**, Pull requests: Read-only, Metadata: Read-only (bevestigd met
  een schermafbeelding van de tokenpagina). Voorgestelde naam:
  "ArticleSearch feedback". Eén token per app.
- Staat enkel in `github_secret_local.py`.
- Het token blijft uit de geïnstalleerde app te halen; de schade is
  beperkt tot Issues aanmaken en lezen in deze ene repo. Het kan de code
  en `version.txt` niet wijzigen.

### 8.3 Regels

1. Het token staat nergens anders: geen ander `.py`-bestand, geen
   context-bestand, geen `zzz/`, `temp/` of `backup/`, ook niet
   gedeeltelijk in een versieheader.
2. Blokkeert GitHub een push (`GH013`): **nooit** "Allow me to expose
   this secret". Het token uit de commit halen.
3. Bij een 401: eerst de security log bekijken (Settings → Security log),
   dan pas een nieuw token maken. Hetzelfde token opnieuw invullen helpt
   nooit.
4. Vóór een push bij twijfel: `python check_github_secret.py`.

### 8.4 Stand van de tests op 2026-10-10

| Test | Resultaat |
|---|---|
| `check_github_secret.py` (volledig, online) | in orde |
| Bugmelding vanuit de app (lokaal) | gelukt — issue #61, label `bug` |
| Build 15.6.0 met de tokencontrole in de spec | gelukt (release staat online) |
| Push/publish 15.6.0 zonder token in de repo | bevestigd op GitHub |
| Token nog geldig ná de publish | **bevestigd** — om 13:07, 31 minuten na de push, aanvaardt GitHub het token nog (vroeger was het dan al ingetrokken) |
| Feature-melding en "Show open cases" | **nog te bevestigen** |
| Melding vanuit een geïnstalleerde 15.6.0 op een andere pc | **nog te doen** |

---

## 9. Beveiliging — aandachtspunten

1. **`config.py` staat in de publieke repo** met de (base64-gecodeerde,
   niet versleutelde) client secrets van alle API-clients en het
   fallback-wachtwoord `CC_TAB_PASSWORD`. Dit is het grootste openstaande
   punt. Opties: repo privé maken, of de secrets roteren en uit git halen
   (zelfde aanpak als het GitHub-token). Buiten scope gehouden op
   2026-10-10; beslissing ligt bij Bart.
2. **Ook getrackt in de publieke repo:** `logs/app.log` (16.994 regels;
   tokens zijn gemaskeerd, maar het bevat o.a. BP-codes en wie wanneer
   wat opzocht),
   `settings.json`, `build_log.txt`, `debug_log.txt`, `export_log.txt`.
   Voorstel: `logs/` en `*.log` in `.gitignore` en `git rm --cached`.
3. **Meldingen zijn publiek leesbaar** (Issues in een publieke repo):
   naam van de melder, en bij Peppol-meldingen factuurnummer en ruwe
   foutboodschap. Bart koos bewust voor "meldingen in de eigen repo".
4. **Het GitHub-token zit in de installer** en de installer staat publiek
   bij de Releases. Aanvaard risico, beperkt door de rechten (§8.2).
5. `CC_LOCK_DISABLED` (dev-bypass) mag in productie nooit actief zijn.
6. De ingetrokken tokens hadden scope `repo` (alle repo's, ook privé) en
   stonden telkens kort publiek. De log toont geen misbruik, maar bevat
   geen IP-adressen en registreert geen clones.
7. Bewuste, herhaalde keuze: de app moet **zonder configuratie per
   machine** werken (installer via Intune). Vandaar geen env vars.

---

## 10. Geleerde lessen

**Git en GitHub**
- Een publieke repo + een hardcoded token = automatisch ingetrokken token.
- Een mondelinge bevestiging dat een token "werkt" is geen testcall.
- `git remote -v` controleren: de remote wees ooit naar een verkeerde
  repo, waardoor pushes nergens heen gingen terwijl `gh release` wel
  werkte.
- `publish.ps1` commit enkel `version.py` en `version.txt`; alle andere
  wijzigingen vooraf committen via GitHub Desktop.
- Faalt de afsluitende `git push`: de Release staat online maar de app
  ziet de nieuwe versie niet. `git pull --rebase origin main`, dan `git push`.

**Windows en scripts**
- `.bat`/`.ps1` moeten **CRLF** hebben; LF geeft verminkte commando's.
- Geen **UTF-8 BOM** in een `.bat`.
- Haakjes in tekst binnen een `if (...)`-blok in cmd escapen: `^(` `^)`.
- In Windows PowerShell 5.1 schrijft `>>` UTF-16: gebruik
  `Add-Content -Encoding ascii` voor `.gitignore`.
- Een gedownload bestand dat met een punt begint (`.gitignore`) wordt
  door de browser vaak hernoemd en komt dus niet aan.
- Een gedownload `.ps1` is geblokkeerd tot `Unblock-File`.

**PyInstaller**
- `datas=` voor een los bestand naast de exe is onbetrouwbaar op een
  geïnstalleerde pc; gebruik de `docs/`-map.
- `SPECPATH` en `sys.executable` zijn beschikbaar in het spec-bestand; een
  `raise SystemExit` daar stopt de build netjes.

**Qt/UI**
- `setStretchLastSection(True)` overschrijft elke ingestelde breedte van
  de laatste kolom.
- `Stretch`-kolommen blokkeren slepen én dubbelklik-autofit.
- Kolomlogica op **sleutel**, nooit op vaste index.
- Sorteren op ruwe waarden (`_SortItem`, `UserRole`), niet op tekst.

**Data**
- Min.Whs geldt per magazijn: eerst sommeren per magazijn, dan vergelijken.
- HANA: kolomnamen met aanhalingstekens zijn hoofdlettergevoelig.
- `U_Message` (Peppol) kan afgekapt zijn; nooit enkel op `json.loads()`
  vertrouwen.

**Werkwijze**
- Geleverde bestanden komen niet altijd in de werkmap terecht (een
  regressie op 08-04 zette meerdere bestanden terug naar oude versies).
  Bij twijfel de versieheader controleren.
- Parallelle chats lopen uit elkaar; dat is ook hoe de context-versies
  vertakt zijn. Eén context-bestand in de Project-bronnen houden.
- Security-wijzigingen eerst afbakenen: twee keer was een fix te breed.
- MSAL met persistente cache is veilig onder Intune/Conditional Access:
  Entra ID blijft het beleid afdwingen, en de interactieve login is de
  terugval.

---

## 11. Open punten

**GitHub-token (deze sessie)**
1. ~~Bevestigen dat het token de publish overleefd heeft~~ — bevestigd
   op 2026-10-10 om 13:07 (`python check_github_secret.py`: in orde).
2. Feature-melding en "Show open cases" testen; daarna een melding vanuit
   een geïnstalleerde 15.6.0.
3. Opruimen in de repo: het losse bestand `gitignore` (zonder punt) in de
   hoofdmap, de map `temp/`, en
   `docs/articlesearch_context_sessie_2026-10-10.md` (komt nu mee in de
   installer omdat het in `docs/` staat).
4. Test-issue #61 sluiten. Optioneel: de 59 oude `bug-…`/`feature-…`-
   branches verwijderen.
5. Uitrol naar de andere apps (`GITHUB_FEEDBACK_UITROL.md`).

**Beveiliging**
6. `config.py` en de logbestanden in de publieke repo (§9, punten 1-2).

**Functioneel**
7. LISA Min.Whs/Max.Whs: backend-bug melden bij wie de stored procedure
   achter `WEZ7CY` beheert.
8. Prod Stock: "Min. SAP" per magazijn i.p.v. per artikel (backend).
9. Browser-tab blijft open na de Azure AD-login: voorstel is een eigen
   `success_template` in `acquire_token_interactive()`. QtWebEngine is
   uitgesloten (Intune/CA).
10. Peppol: exacte "in queue"-waarde van `U_TaskType`; betekenis van
    `U_ActionPerformed` per `SourceTable` (ORIN/OPOR niet getest); zoeken
    over meerdere documenttypes.
11. `ui_docs.py`: exportknoppen nakijken.
12. Kolombreedtes onthouden tussen zoekacties (nooit gevraagd, wel
    genoteerd).
13. Sorteren op "Art. nummer": oorspronkelijke vraag afgehandeld via
    SORT-1 (dubbelklik op de kolomkop).

**Documentatie**
14. `docs/help.md` bijwerken (staat op 15.4.0; "Bug of feature melden"
    beschrijft nog een issue "met logbestand").
15. Nummering van `docs/changelog.md` gelijktrekken met de releases (§7.5).
16. Nog niet doorgenomen (◦ in §3): o.a. `ui_bp_cc_lists_tab.py`,
    `cc_service.py`, `security_docs.py`, `security_cc.py`, `project_ui.py`,
    `ui_vta.py`, `ui_docs.py`, de labelmodule, `help_dialogs.py`,
    `ui_image_search.py`, `ui_timings.py`.

**Niet live bevestigd door de gebruiker** (enkel in code of losse test):
INTUNE-UPDATE-1 via een echte Intune-update · QTYKLEUR-1 in de app ·
automatische naam in BugDialog · de twee PaymentsDue-clients.

---

## 12. Werkwijze en conventies

**Code**
- Elk nieuw of gewijzigd bestand krijgt de versieheader
  `App / File / Role / Version / Author / Changes` — Author altijd
  "Bart Bossuyt", nieuwste `Changes:`-regel bovenaan, oudere blijven staan.
  MAJOR bij brekende wijziging, MINOR bij nieuwe functie, PATCH bij fix.
- **Reactief:** enkel aangeraakte bestanden krijgen een header; geen
  proactieve inventaris tenzij gevraagd.
- Altijd het **volledige bestand** leveren, als downloadbaar bestand,
  nooit een fragment. Bij elke levering de **exacte bestandsnaam en
  doelmap** vermelden.
- Bestandssplitsing `*_token.py` / `*_info.py` / `ui_*.py` /
  `*_dialog.py` / `*_helper.py`.

**Aanpak**
- Eerst de aanpak bespreken, dan pas code ("nog niks van code
  aanleveren").
- Groot werk eerst in een apart testbestand, dan overzetten.
- Werken met live API-data, geen mock-data.
- UI: keuzelijsten i.p.v. vrije tekst waar de keuze beperkt is;
  `CHANGEBY`-velden read-only; resultaten inline i.p.v. pop-ups; geen data
  bij openen; `Ctrl+E` = export, `Delete` = filter wissen.

**Documentatie bij elke wijziging**
- Dit context-bestand: versie ophogen, sessieblok toevoegen, als bestand
  leveren, vorige versie als verwijderbaar markeren.
- `docs/changelog.md`: nieuwe entry bovenaan (✨ Nieuw / 🛠 Verbeterd /
  🐞 Bugfix / 🔒 Security). Bart zet het zelf in de build-map. Entries
  uit een chat komen niet vanzelf in het project — telkens bevestigen.
- Release notes op GitHub ("Wat is er nieuw?") vult Bart zelf in.

---

## 13. Relatie met CGK_Searchtool

ArticleSearch wordt omgebouwd naar **CGK_Searchtool** (de app doet veel
meer dan artikels zoeken). Dat loopt in een aparte chat met eigen
context (`CGK_Searchtool_context_v1.md` + `v2.md`).

- **Reden:** uniforme mapstructuur voor al Barts toekomstige apps, zodat
  elke module los gebouwd en getest kan worden. Geen opkuis van secrets.
- **Structuur, geen gedrag:** logica en GUI blijven gelijk.
- **Werkmap** `C:\PY\CGK_Searchtool`, gegenereerd met de
  Project_Generator-wizard. Mappen: `app/` (main.py, version.py), `core/`
  (config, auth, data_request, token_manager, permissions_azure, settings,
  updater, paths), `ui/`, `dialogs/`, `tokens/` (niet `token/` — botst met
  de standaardmodule), `helpers/` (`*_helper.py` + `*_info.py`), `i18n/`
  (NL/EN/FR vanaf de start), `assets/`, `css/`, `data/`, `docs/`,
  `scripts/`, `tests/`.
- **Imports:** echte packages met dotted imports; `app/main.py` zet de
  projectroot op `sys.path`.
- **`ui_main.py`** (2.490 regels) is gesplitst in een schil +
  `main_window_common/_menu/_search/_update.py` (mixins). Niet-gemigreerde
  modules tonen een stub-melding.
- **Versie:** start op `26.0.0` (major = jaar); eerste release `26.1.0`;
  `bump_version.py` moet bij een jaarwissel automatisch naar `27.0.0`.
- **Repo:** een **nieuwe** repo onder hetzelfde `barremans`-account (v2
  overschrijft v1 op dit punt). `barremans/articlesearch` blijft
  zelfstandig bestaan.
- **Installatie:** naast ArticleSearch, met een nieuwe AppGuid en
  `C:\CGK_Searchtool`. ArticleSearch wordt later manueel verwijderd.
  Intune-randvoorwaarden blijven gelden.
- **Stand (2026-09-13):** het skelet draait, artikelzoek werkt live.
  Volgende stap: Peppol migreren, na een beslissing over
  `i18n/translator.py`.
- **Feedbackpakket in CGK_Searchtool:** nog niet gemigreerd. De
  pakketbestanden kunnen ongewijzigd in de **projectroot** staan (die
  staat op `sys.path`); zie `GITHUB_FEEDBACK_UITROL.md`.

---

## 14. Sessiegeschiedenis (beknopt)

| # | Datum | Onderwerp | Belangrijkste bestanden |
|---|---|---|---|
| 1 | 08-03 | DIM-1: tab Dimensions; start versieheaders en context-bestand | `ui_dimensions.py`, `ui_detail.py` |
| 2 | 08-03 | SORT-1: kolomsortering Artikel-tabel | `ui_main.py` |
| 3–9 | 08-03 | ART-BP-1: tab Artikels bij leveranciers, kolommen, zoekbalk | `artbp_*.py`, `ui_bp_articles_tab.py`, `ui_bp.py` |
| 10–13 | 08-03/04 | CC-ACCESS-1, L6-fix in `main.py`, datalek gedicht (met correctie) | `ui_bp_cc_detail_tab.py`, `main.py`, `ui_bp.py` |
| 14 | 08-04 | Bugfix "Standaard"/"Artikel" | `ui_main.py`, `settings.py`, `settings_dialog.py` |
| 15 | 08-04 | MINWHS-KLEUR-1, KOLOMBREEDTE-1; vaste workflow in de Project-instructies | `ui_main.py` |
| 16 | 08-04 | WHATSNEW-1 | `updater.py`, `ui_main.py` |
| 17–18 | 08-04 | Changelog bijgewerkt → entry 15.0.0 | `docs/changelog.md` |
| 19 | 08-04 | Build/publish herbouwd (Networkmap-patroon), git-remote hersteld, bestandsregressie hersteld; eerste release 15.0.0 | `build_installer15.bat`, `publish.ps1`, `build_and_publish.ps1` |
| 20 | 08-06 | Peppol-scherm herontworpen en live gezet (15.0.2) | `ui_peppol.py`, `pep_errors.json`, `SearchArticle.spec` |
| 21–23 | 08-06 | 401-fouten: updater zonder auth, tokens vervangen | `updater.py`, `github_cases.py`, `bug_report_dialog.py` |
| 24 | 08-26/27, vervolg 09-01 | PaymentsDue (3 tabs incl. Forecast), OITMI-voorinvulling, LISA-workaround, Prod rood-regel | `duepayment_*.py`, `ui_duepayment.py`, `ui_detail.py`, `ui_lisa.py`, `config.py` |
| 25 | 08-28 | Productie Stock Overview | `prod_*.py`, `ui_prod_datasets_dialog.py`, `ui_main.py`, `settings*.py` |
| 26 | 08-31 | INTUNE-UPDATE-1, push-blokkade (GH013), token vervangen, QTYKLEUR-1, naam in BugDialog | `build_installer15.bat`, `ui_main.py`, `ui_lisa.py`, `ui_sap.py`, `permissions_azure.py` |
| 27–28 | 08-31 | Opstartsnelheid: MSAL-cache, asynchrone Prod-datasetlijst | `permissions_azure.py`, `ui_main.py`, `requirements.txt` |
| — | 09-11 | Open Elements overview; Instellingen in tabbladen; eigenaarschap datasets (15.5.0/15.5.1) | `oeoverview_info.py`, `ui_oeoverview.py`, `settings_dialog.py`, `ui_prod_datasets_dialog.py` |
| — | 09-13 | Start migratie naar CGK_Searchtool (aparte chat) | zie §13 |
| — | 09-17 | Signing: thumbprint, verificatie, release-gate; Defender-indicator | `build_installer15.bat`, `build_and_publish.ps1`, `publish.ps1` |
| — | 10-10 | GitHub-token: oorzaak gevonden, uniform feedbackpakket, release 15.6.0, dit geconsolideerde bestand | zie §6.9 en §8 |

---

## 15. Hoe dit bestand te gebruiken

- Houd **één** context-bestand in de Project-bronnen. Een nieuwe versie
  vervangt de vorige.
- Bij een wijziging: lever het betrokken bestand aan; de versieheader in
  de code is de waarheid, dit bestand de kaart.
- Wordt het sessie-overzicht te lang, dan opnieuw consolideren zoals hier.
