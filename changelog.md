# 📝 Changelog

## [v4.2.3] – 2025-06-25
- 📋 Verbeterd: kopieerfunctie van verzamellijst (ART/VTA) exporteert nu ook **Outlook- en Word-compatibele HTML-tabellen**
- 🧾 HTML bevat nette randen, padding, Arial-lettertype en correcte encoding
- 📤 Geoptimaliseerd voor plakken in e-mails, Word-documenten en browsers

## [v4.2.2] – 2025-06-24
- ➕ Toegevoegd: kolommen **MD_SupplNbr** en **MD_Suppl** aan *PRJ Art.*-tab (VTA)
- 📋 Deze tonen respectievelijk het masterdata leveranciersnummer en -naam per artikel
- 🔄 Gegevens worden opgehaald uit `LART[0]` binnen elk VTA-item

## [v4.2.1] – 2025-06-21
- 📏 Max en min size ingesteld op detail- en projectvenster
- 🖱️ Dubbelklik op itemcode of omschrijving opent detailvenster

## [v1.4.1] – 2025-06-14
- ➕ Toegevoegd: verzamelknop, leeg-knop en “Selecteer alles” bij Project ART-tab
- 📋 Verzamelde rijen kunnen worden gekopieerd naar klembord in TSV + HTML
- ❌ Leeg-knop deselecteert alle checkboxes in ART-tab
- 🪄 Zelfde verzamel-functionaliteit als in standaard zoekresultaten
- ♻️ Code opgeschoond en uitgelijnd met hoofdvenster

## [v1.4.0] – 2025-06-14
- 🔍 Nieuw zoektype 'Project' met aangepaste UI
- 🧠 Tooltip past zich aan op zoektype
- 🧼 Verbergt zoekmodus en voorraad-opties bij projectmodus
- 📄 Changelog zichtbaar in menu → Help → Changelog
- 🧾 `help.md` en `changelog.md` verplaatst naar submap `/docs`
- 📁 FileEditorDialog hergebruikt voor changelog- en helpbestanden

## [v1.3.2] – 2025-06-14
- 🆕 Nieuw: dropdown in instellingen om standaard zoektype te kiezen
- 🛠️ Verbeterd: artikeltabel toont nu correcte kolommen voor projecten
- 🐛 Fix: crash opgelost bij dubbele klik zonder selectie

## [v1.3.1] – 2025-06-12
- 🐞 Bug opgelost in labelweergave
- ⚙️ Verbeterde instellingsdialoog

## [v1.3.0] – 2025-06-01
- 🆕 Nieuw: tabblad VTA toegevoegd aan projectweergave
- 🎨 Verbeterd: labels in zoekvenster herschikt

## [v1.2.0] – 2025-05-20
- 🚀 Initieel projectzoekvenster toegevoegd
- 📦 Basis ondersteuning voor ART-gegevens
