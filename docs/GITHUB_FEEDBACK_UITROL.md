# GitHub-feedbackpakket — uitrolhandleiding voor alle apps

> **Versie:** 1.0.0 — 2026-10-10
> **Pakketversie:** `github_feedback.py` 1.0.0 · `bug_report_dialog.py` 2.0.0 · `github_cases.py` 2.0.0 · `check_github_secret.py` 1.0.0
> **Referentie-app:** ArticleSearch 15.6.0 (`C:\searcharticle_code`) — daar is het pakket voor het eerst uitgerold en getest.
> **Voor wie:** Bart Bossuyt, voor elke bestaande en nieuwe Python-app met "Bug of feature melden".

---

## 1. Waarom dit pakket bestaat

**Het probleem.** GitHub trekt een token automatisch in zodra het in een
publieke repo gepusht wordt. Elk token dat hardcoded in een `.py`-bestand
stond, stierf dus bij de eerstvolgende push — soms na 13 minuten. Omdat
meerdere apps hetzelfde token deelden, vielen ze samen uit.

**De oplossing.** Het token staat in één bestand dat nooit in git komt
(`github_secret_local.py`). PyInstaller bundelt dat bestand wel mee in de
exe, dus eindgebruikers hoeven niets te configureren.

**Wat het pakket doet**
- Een bug of feature melden als GitHub **Issue** (label `bug` of
  `enhancement`).
- De open meldingen tonen.
- Controleren dat er geen token naar GitHub gaat, en dat het token nog
  werkt — automatisch vóór elke build.

**Wat het niet doet**
- Het maakt het token niet onvindbaar: wie de installer uitpakt, kan het
  eruit halen. Daarom krijgt het token zo weinig rechten als mogelijk
  (enkel Issues in één repo).
- Het regelt geen auto-update voor een **privé**-repo (zie §5.5).

**Tijd per app:** reken op 30 tot 45 minuten, build inbegrepen.

---

## 2. De bestanden

| Bestand | Per app aanpassen? | In git? | Rol |
|---|---|---|---|
| `github_feedback.py` | nee — identiek | ja | Verstuurt de melding, haalt open meldingen op. Geen Qt, geen token |
| `bug_report_dialog.py` | nee — identiek | ja | Het meldscherm (`BugDialog`) |
| `github_cases.py` | nee — identiek | ja | Het scherm met open meldingen (`show_github_cases`) |
| `check_github_secret.py` | nee — identiek | ja | De controle vóór push en build |
| `github_secret_local.example.py` | nee — identiek | ja | Sjabloon, zonder token |
| `github_feedback_config.py` | **ja** | ja | App-naam, repo, naam van de melder, app-versie |
| `github_secret_local.py` | **ja** | **NEE** | Het token. Maak je zelf aan, per app |

Daarnaast pas je in elke app twee bestaande bestanden aan: `.gitignore`
(één regel) en het `.spec`-bestand (één blok + twee regels).

**Bron van de identieke bestanden:** kopieer ze altijd uit
`C:\searcharticle_code`. Pas ze niet per app aan; een verbetering doe je
in de referentie-app en rol je daarna opnieuw uit (§7.4).

**Vereiste:** de Python-module `requests` moet in de venv van de app
staan (`pip install requests`, en opnemen in `requirements.txt`).

---

## 3. Vóór je begint: inventaris per app

Vul dit per app in. De antwoorden bepalen welke varianten uit §5 je nodig
hebt.

| Vraag | Hoe nakijken | Gevolg |
|---|---|---|
| Naam van de repo en eigenaar | `git remote -v` | Komt in `github_feedback_config.py` en in het token |
| Publiek of privé? | Repo-pagina op GitHub | Privé: zie §5.5 |
| PySide6 of PyQt6? | `Select-String -Path *.py -Pattern "from PyQt6","from PySide6" -List` | PyQt6: zie §5.1 |
| Platte map of mappenstructuur? | Staat `main.py` in de hoofdmap of in `app\`? | Mappen: zie §5.2 |
| Heeft de app al een meldscherm? | Zoek `BugDialog`, `GitHubClient`, `api.github.com` | Nee: zie §5.4 |
| Heeft de app Azure AD-login? | Bestaat `permissions_azure.py`? | Nee: zie §5.3 |
| Waar staat de versie? | `version.py` in de hoofdmap, of `app\version.py`? | Bepaalt `get_app_version()` |
| Hoe heet het `.spec`-bestand? | `Get-ChildItem *.spec` | Stap 7 |
| Gebruikt de updater een token? | Zoek `TOKEN` in `updater.py` | Stap 6c |

De apps die in de security log van het account voorkwamen:
`articlesearch` (klaar), `Project_generator`, `capacitor_esr_validator`,
`Biesse2Csv`, `WVB` (alle publiek), `easee_middleware`,
`OpenElements2Csv` (privé). Begin met de publieke: daar wordt een token
effectief ingetrokken.

---

## 4. Stappenplan voor een bestaande app

Alle commando's draai je in **PowerShell**, in de hoofdmap van de app,
met de venv actief. Vervang `C:\PY\MijnApp` door de map van de app.

```powershell
cd C:\PY\MijnApp
.\.venv\Scripts\Activate.ps1
```

### Stap 1 — Werkmap in orde brengen

**Wat:** zorgen dat je vertrekt van een schone, bijgewerkte map.

```powershell
git status --short
git pull
git remote -v
```

**Controle:** `git status --short` toont niets (of enkel wijzigingen die
je kent). `git remote -v` wijst naar de juiste repo.

**Waarom:** in ArticleSearch wees de remote ooit naar een verkeerde repo,
waardoor pushes nergens heen gingen. Eén keer nakijken per app.

### Stap 2 — Zoeken waar het oude token staat

**Wat:** de controle gebruiken als zoekmachine.

```powershell
Copy-Item C:\searcharticle_code\check_github_secret.py .
python check_github_secret.py --skip-token
```

**Verwacht op dit moment (dit is goed nieuws, geen fout):**

```
[FOUT] github_secret_local.py staat NIET in .gitignore. ...
[FOUT] Token gevonden in 2 regel(s) van getrackte bestanden. NIET committen of pushen:
        bug_report_dialog.py:68:        self.token = "ghp_FZlpfb...[verborgen]"
        ...
```

Noteer elk bestand en regelnummer: daar moet het token straks weg. Het
script toont nooit een volledig token.

Zoek ook naar de oude code zelf:

```powershell
Select-String -Path *.py -Pattern "api.github.com","GitHubClient","GitHubCasesClient","BugDialog","show_github_cases" | Select-Object Filename, LineNumber, Line
```

### Stap 3 — De regel in `.gitignore` (eerst dit, dan pas de rest)

```powershell
Add-Content -Path .gitignore -Value "", "# Geheimen: het GitHub-token mag NOOIT in git.", "*_secret_local.py" -Encoding ascii
git check-ignore -v --no-index github_secret_local.py
```

**Controle:** het tweede commando antwoordt met een regel die eindigt op
`*_secret_local.py	github_secret_local.py`.

**Let op**
- Gebruik `Add-Content`, niet `>>`. In Windows PowerShell 5.1 schrijft
  `>>` een andere tekencodering en leest git het bestand niet meer correct.
- Download **geen** kant-en-klare `.gitignore`: de browser hernoemt een
  bestand dat met een punt begint, en dan komt het niet aan. Dat ging in
  ArticleSearch mis.
- Bestaat er nog geen `.gitignore`? Het commando maakt hem aan.

### Stap 4 — De pakketbestanden kopiëren

```powershell
$bron = "C:\searcharticle_code"
Copy-Item "$bron\github_feedback.py", "$bron\bug_report_dialog.py", "$bron\github_cases.py", "$bron\check_github_secret.py", "$bron\github_secret_local.example.py", "$bron\github_feedback_config.py" . -Force
```

**Let op:** bestaan `bug_report_dialog.py` en `github_cases.py` al in
deze app, dan worden ze overschreven. Dat is de bedoeling: de oude
versies bevatten het token. Heet het oude meldscherm anders, verwijder
dat bestand dan in stap 6.

Kopieer **niet** `github_secret_local.py` uit ArticleSearch: elke app
krijgt een eigen token.

### Stap 5 — `github_feedback_config.py` aanpassen

Open het bestand en pas deze drie regels aan:

```python
APP_NAME = "MijnApp"
GITHUB_OWNER = "barremans"
GITHUB_REPO = "mijnapp"          # exact zoals in de URL van de repo
```

Pas ook de eerste regel van de header aan (`# ArticleSearch` →
`# MijnApp`).

De twee functies onderaan:
- `get_reporter_name()` — heeft de app Azure AD-login via
  `permissions_azure.py`, laat de functie dan zoals ze is. Zo niet: §5.3.
- `get_app_version()` — staat de versie in `version.py` in de hoofdmap,
  laat de functie dan zoals ze is. Staat ze in `app\version.py`: §5.2.

**Regel:** zet bovenaan dit bestand geen `import` van app-modules. De
controle leest dit bestand ook tijdens de build, buiten de app om.
Imports horen binnen de functies, zoals nu.

### Stap 6 — De oude code opruimen

**a. Oude meldbestanden.** Heette het oude scherm anders dan
`bug_report_dialog.py`/`github_cases.py`, verwijder dat bestand dan met
`git rm <bestand>` en pas de imports aan naar:

```python
from bug_report_dialog import BugDialog
from github_cases import show_github_cases
```

**b. De aanroepen blijven gelijk.**

```python
BugDialog(self).exec()                       # melden
BugDialog(parent, initial_type="Feature-aanvraag", initial_description="...").exec()   # vooringevuld
show_github_cases(self)                      # open meldingen
```

De klassen `GitHubClient` en `GitHubCasesClient` bestaan niet meer.
Gebruikt de app ze ergens rechtstreeks, vervang dat door
`GitHubFeedbackClient` uit `github_feedback.py`.

**c. De updater.** Staat er in `updater.py` een `TOKEN`, dan:
- **publieke repo:** token weghalen en geen `Authorization`-header meer
  meesturen. Lezen van `version.txt` en releases werkt anoniem. Neem
  `updater.py` v1.3.0 van ArticleSearch als voorbeeld.
- **privé-repo:** zie §5.5.

**d. Alle andere plaatsen** uit stap 2 (ook `config.py`, testscripts,
mappen als `zzz\`, `temp\`, `backup\`): token weghalen.

### Stap 7 — Het `.spec`-bestand aanpassen

**a. Het controleblok.** Plak dit bovenaan, ná de bestaande `import`-
regels en vóór `Analysis(...)`. `import os` moet erboven al aanwezig
zijn; zo niet, zet het erbij.

```python
# --- GitHub-token: controle vóór de build ---
# SPECPATH = de map van dit .spec-bestand (door PyInstaller gezet).
import subprocess
import sys

_secret_check = os.path.join(SPECPATH, "check_github_secret.py")
if subprocess.call([sys.executable, _secret_check]) != 0:
    raise SystemExit("[FOUT] Build gestopt: de controle van het GitHub-token is mislukt (zie hierboven).")
```

**b. Twee regels in `hiddenimports`** van `Analysis(...)`:

```python
    hiddenimports=[
        ...bestaande regels...
        "github_feedback_config",
        "github_secret_local",
    ],
```

Heeft de `Analysis` nog geen `hiddenimports=`, voeg dan
`hiddenimports=["github_feedback_config", "github_secret_local"],` toe.

**Waarom:** met dit blok kan er geen installer meer gebouwd worden zonder
werkend token, en kan er geen token meer ongemerkt in een commit zitten.
De build stopt met een duidelijke melding.

Verhoog de versie in de header van het spec-bestand en zet er een
`Changes:`-regel bij.

### Stap 8 — Controleren zonder token

```powershell
python check_github_secret.py --skip-token
python -m py_compile github_feedback.py github_feedback_config.py bug_report_dialog.py github_cases.py check_github_secret.py
```

**Verwacht:**

```
[OK] github_secret_local.py wordt genegeerd door git (.gitignore).
[OK] github_secret_local.py staat niet in de repo.
[OK] Geen token gevonden in de bestanden die naar GitHub gaan.
[OK] Geen nog niet gepushte commits.
[--] Controle van github_secret_local.py overgeslagen (--skip-token).

RESULTAAT: in orde.
```

Start daarna de app. "Show open cases" werkt al (bij een publieke repo);
verzenden geeft de melding dat deze versie geen token bevat. Dat klopt.

### Stap 9 — Committen en pushen, nog zónder token

1. Commit in GitHub Desktop. Je ziet de gewijzigde bestanden en de
   nieuwe pakketbestanden; `github_secret_local.py` bestaat nog niet.
2. Push.
3. Blokkeert GitHub de push met een melding over een secret (`GH013`):
   klik **niet** op "Allow me to expose this secret". Het token zit dan
   nog in een commit; ga terug naar stap 2.

**Waarom eerst pushen:** zo weet je zeker dat de repo schoon is vóór er
een nieuw token bestaat.

### Stap 10 — Het token aanmaken

Aangemeld op GitHub als de **eigenaar van de repo**.

1. **Settings** (je profiel) → **Developer settings** → **Personal
   access tokens** → **Fine-grained tokens** → **Generate new token**.
2. **Token name:** `MijnApp feedback`.
3. **Expiration:** "No expiration". Met een vervaldatum stopt het melden
   op die dag in elke geïnstalleerde versie, tot er een nieuwe release is.
4. **Repository access:** "Only select repositories" → enkel de repo van
   deze app.
5. **Permissions → Repository permissions:**
   - **Issues:** Read and write
   - **Pull requests:** Read-only (enkel nodig als er nog oude
     feature-aanvragen als Pull Request openstaan; anders mag dit weg)
   - **Metadata:** Read-only (komt er vanzelf bij)
   - al de rest: No access
6. **Generate token** en meteen kopiëren. Je ziet het maar één keer.

Kijk ook even in de repo zelf:
- **Settings → General → Features → Issues** staat aan.
- **Issues → Labels:** `bug` en `enhancement` bestaan (standaard is dat zo).

**Eén token per app.** Zo legt een probleem met één token maar één app
plat, en zie je op GitHub per token wanneer het laatst gebruikt is.

### Stap 11 — Het token plaatsen en controleren

```powershell
Set-Content -Path github_secret_local.py -Value 'GITHUB_TOKEN = ""' -Encoding ascii
notepad github_secret_local.py
```

Plak het token tussen de aanhalingstekens, zodat er staat:

```python
GITHUB_TOKEN = "github_pat_...jouw token..."
```

Opslaan, sluiten, en dan:

```powershell
python check_github_secret.py
git status --short
```

**Verwacht:** zes regels `[OK]`, waaronder
`[OK] GitHub aanvaardt het token voor <owner>/<repo> (Issues leesbaar).`
en `RESULTAAT: in orde.` — en `git status --short` toont
`github_secret_local.py` **niet**.

Het token komt nergens anders: niet in de chat, niet in een
context-bestand, niet in een ander `.py`-bestand.

### Stap 12 — Testen in de app

```powershell
python main.py
```

1. Meld een **bug** met tekst `TEST - mag gesloten worden`. Verwacht:
   "Bugmelding verzonden:" met een link naar `.../issues/<nummer>`.
2. Meld een **feature**. De link gaat ook naar `.../issues/...`.
3. Open **Show open cases**: de bug staat onder "Open bugmeldingen", de
   feature onder "Open feature-aanvragen".
4. Op GitHub: de bug heeft label `bug`, de feature `enhancement`; de
   eerste regel vermeldt je naam en de app-versie. Sluit beide.

Bij een publieke repo zijn meldingen publiek leesbaar: houd testtekst
neutraal.

### Stap 13 — Build en publish

```powershell
Unblock-File .\build_and_publish.ps1, .\publish.ps1
.\build_and_publish.ps1
```

- `Unblock-File` is enkel nodig als PowerShell meldt dat het script "not
  digitally signed" is.
- Tijdens de build verschijnt `=== Controle GitHub-token ===`, eindigend
  op `RESULTAAT: in orde`. Stopt de build met `[FOUT] Build gestopt`,
  los dan eerst op wat erboven staat.
- In ArticleSearch weigert `publish.ps1` een installer zonder geldige
  handtekening. Gebruikt de app hetzelfde script, kies dan "signeren: J".

**De eigenlijke proef**, vijf minuten na de publish:

```powershell
python check_github_secret.py
```

Staat er nog `[OK] GitHub aanvaardt het token`, dan heeft het token de
push overleefd.

### Stap 14 — De geïnstalleerde versie testen

Installeer de nieuwe versie op een andere pc (of via Intune) en verstuur
daar één testmelding. Dat bewijst dat het token correct in de installer
zit. Sluit het test-issue.

### Stap 15 — Administratie

- Vul het tokenregister in (§7.1).
- Werk het context-bestand en de changelog van de app bij.
- Vul op GitHub de release notes in.

---

## 5. Varianten

### 5.1 De app gebruikt PyQt6 in plaats van PySide6

De twee schermen zijn geschreven voor PySide6. Voor PyQt6 zet je ze na
het kopiëren (stap 4) om met dit ene commando:

```powershell
foreach ($f in 'bug_report_dialog.py','github_cases.py') {
    (Get-Content $f -Raw -Encoding UTF8) `
        -replace 'from PySide6\.', 'from PyQt6.' `
        -replace 'QMessageBox\.(Yes|No)\b', 'QMessageBox.StandardButton.$1' `
        -replace 'Qt\.WaitCursor', 'Qt.CursorShape.WaitCursor' |
        Set-Content $f -Encoding UTF8
}
python -m py_compile bug_report_dialog.py github_cases.py
Select-String -Path bug_report_dialog.py, github_cases.py -Pattern "PySide6" | Where-Object { $_.Line -notmatch '^\s*#' }
```

Het laatste commando mag niets tonen. Deze omzetting is getest met
PyQt6 (dezelfde 17 schermcontroles als bij PySide6).

`github_feedback.py` en `check_github_secret.py` bevatten geen Qt en
blijven ongewijzigd. Na een update van het pakket (§7.4) herhaal je de
omzetting.

### 5.2 De app heeft een mappenstructuur (Project_Generator, CGK_Searchtool)

Zet **alle pakketbestanden in de projectroot**, naast het `.spec`-bestand
— dus niet in `dialogs\`, `core\` of `helpers\`. Redenen:
- de bestanden blijven identiek aan die van elke andere app;
- `app\main.py` zet de projectroot al op `sys.path`, dus
  `from bug_report_dialog import BugDialog` werkt overal;
- `check_github_secret.py` en het token horen naast het `.spec`-bestand.

Pas in `github_feedback_config.py` enkel de imports binnen de functies
aan:

```python
def get_reporter_name() -> str:
    try:
        from core.permissions_azure import get_current_user_display_name
        return (get_current_user_display_name() or "").strip()
    except Exception:
        return ""


def get_app_version() -> str:
    try:
        from app.version import __version__
        return str(__version__)
    except Exception:
        return ""
```

In het spec-bestand (`Analysis(["app/main.py"], pathex=["."], ...)`)
blijven het controleblok en de twee `hiddenimports` zoals in stap 7.

**Nog niet in de praktijk getest** in een app met mappenstructuur. Doe
bij de eerste zo'n app stap 8, 12 en 14 extra zorgvuldig. Wil je het
pakket liever in een eigen map (`feedback\`), dan vraagt dat een
aangepaste pakketversie; meld het, dan wordt dat versie 1.1.

### 5.3 De app heeft geen Azure AD-login

Laat `get_reporter_name()` de Windows-gebruikersnaam teruggeven:

```python
def get_reporter_name() -> str:
    import getpass
    try:
        return getpass.getuser()
    except Exception:
        return ""
```

Het veld "Je naam" is dan vooringevuld en read-only. Wil je dat de
gebruiker zijn naam zelf typt, geef dan `""` terug.

### 5.4 De app heeft nog geen meldscherm

Voeg in het hoofdvenster, waar de menubalk opgebouwd wordt, toe:

```python
from bug_report_dialog import BugDialog
from github_cases import show_github_cases
```

```python
report_menu = menubar.addMenu("&Rapporteren")
report_menu.addAction("🐞 &Bug of feature melden...").triggered.connect(lambda: BugDialog(self).exec())
report_menu.addSeparator()
report_menu.addAction("Show open cases").triggered.connect(lambda: show_github_cases(self))
```

Stap 2 en 6 vallen dan grotendeels weg (er is geen oud token), maar draai
stap 2 toch: het bewijst dat de repo schoon is.

### 5.5 De repo is privé

- **Melden en open meldingen:** werkt identiek. Het lezen valt bij een
  ongeldig token niet terug op anoniem (dat kan enkel bij een publieke
  repo); je krijgt dan een nette foutmelding.
- **In een privé-repo trekt GitHub een token niet automatisch in.** Maar
  wordt de repo later publiek gezet (zoals `Project_generator` op 16/09),
  dan scant GitHub de volledige geschiedenis en kan een token dat er ooit
  in stond alsnog ingetrokken worden. Volg dus overal dezelfde regels.
- **Auto-update:** een app in een privé-repo kan `version.txt` en de
  releases niet anoniem lezen. Daarvoor is een token met "Contents:
  Read-only" nodig, en dat maakt de broncode leesbaar voor wie het token
  uit de installer haalt. Dit pakket regelt dat niet. Bespreek het per
  app; de opties zijn: de update-check via een andere weg (bv. een
  bestand op een interne share), of dat extra leesrecht bewust aanvaarden.

### 5.6 De app wordt niet met een `.spec`-bestand gebouwd

Roep de controle dan aan in het buildscript, vóór PyInstaller:

```bat
"%PYEXE%" check_github_secret.py || exit /b 1
```

en geef PyInstaller mee: `--hidden-import github_secret_local --hidden-import github_feedback_config`.

---

## 6. Nieuwe apps

### 6.1 Vanaf dag één

Bij een nieuwe app doe je dezelfde stappen, maar in deze volgorde, vóór
de eerste commit:

1. `.gitignore` met de regel `*_secret_local.py` (stap 3).
2. De pakketbestanden kopiëren (stap 4) en `github_feedback_config.py`
   invullen (stap 5).
3. Het menu toevoegen (§5.4).
4. Het controleblok en de `hiddenimports` in het `.spec`-bestand (stap 7).
5. `requests` in `requirements.txt`.
6. Eerste commit en push. Daarna pas het token (stap 10 en 11).

Een nieuwe app heeft dus nooit een token in zijn geschiedenis.

### 6.2 Structureel: in de Project_Generator

Nieuwe apps komen uit de Project_Generator-wizard. De duurzame oplossing
is het pakket in de sjablonen van de wizard op te nemen
(`core/default_templates.py`, `core/generator.py`), zodat elke
gegenereerde app automatisch krijgt:
- de vijf identieke bestanden in de projectroot;
- een ingevulde `github_feedback_config.py` (app-naam uit de wizard;
  imports voor de mappenstructuur, §5.2);
- de regel in `.gitignore`;
- het controleblok en de `hiddenimports` in het gegenereerde spec-bestand;
- het menu "Rapporteren" in het gegenereerde hoofdvenster.

Dat is een aparte, kleine klus in het Project_Generator-project. Nodig:
de huidige `core/default_templates.py` en `core/generator.py`, en de
keuze of gegenereerde apps PySide6 of PyQt6 gebruiken (§5.1).

Het token blijft ook dan handwerk per app (stap 10 en 11): dat kan en mag
geen wizard doen.

### 6.3 Eén bron van waarheid

Tot de wizard het pakket levert, is `C:\searcharticle_code` de bron.
Noteer in het context-bestand van elke app welke pakketversie erin zit
(de `Version:` in de header van `github_feedback.py`).

---

## 7. Beheer

### 7.1 Tokenregister

Houd deze tabel bij op een plek buiten git (niet in een repo). Zet er
**nooit** het token zelf in.

| App | Repo | Publiek? | Tokennaam op GitHub | Aangemaakt | Vervalt | Pakketversie | Laatste release met dit token |
|---|---|---|---|---|---|---|---|
| ArticleSearch | barremans/articlesearch | ja | _(naam die je koos)_ | 2026-10-10 | _(zelf invullen)_ | 1.0.0 | 15.6.0 |
| | | | | | | | |

Op GitHub zie je per token wanneer het laatst gebruikt is: Settings →
Developer settings → Fine-grained tokens.

### 7.2 Een token vervangen

1. Maak een nieuw token (stap 10) en zet het in `github_secret_local.py`.
2. `python check_github_secret.py`.
3. Build en publish.
4. Verwijder het **oude** token op GitHub pas als iedereen de nieuwe
   versie heeft: oudere installaties gebruiken het oude token nog. Is het
   oude token gelekt, verwijder het dan meteen en aanvaard dat melden in
   oude versies tijdelijk niet werkt.

### 7.3 Als er toch een 401 opduikt

1. Kijk eerst **waarom**: GitHub → Settings → Security log → zoek op
   `token_scan` en `oauth_authorization.destroy`. Staat het token er met
   reden `token_scan`, dan stond het ergens publiek.
2. Zoek waar: `python check_github_secret.py --skip-token` in elke app
   die een token gebruikt.
3. Los dat op (stap 2 tot 9) en maak dan pas een nieuw token.

Hetzelfde token opnieuw invullen helpt nooit: een ingetrokken token komt
niet terug.

### 7.4 Een nieuwe pakketversie uitrollen

1. Pas het bestand aan in de referentie-app en verhoog de versie in de
   header.
2. Test daar (stap 8 en 12).
3. Kopieer de identieke bestanden opnieuw naar elke app (stap 4, zonder
   `github_feedback_config.py`), herhaal bij PyQt6-apps §5.1, en doe
   stap 8, 12 en 13.

### 7.5 Wat je nooit doet

- Het token in een getrackt bestand zetten, ook niet tijdelijk, ook niet
  gedeeltelijk in een commentaarregel.
- "Allow me to expose this secret" aanklikken bij een geblokkeerde push.
- Eén token delen tussen apps.
- Een klassiek token (`ghp_...`) met scope `repo` gebruiken: dat geeft
  toegang tot al je repo's, ook de privé-repo's.
- `github_secret_local.py` kopiëren naar `zzz\`, `temp\`, `backup\`, een
  USB-export die in git komt, of een Claude Project.
- Het token in een chat plakken.

---

## 8. Problemen oplossen

| Wat je ziet | Oorzaak | Oplossing |
|---|---|---|
| `[FOUT] github_secret_local.py staat NIET in .gitignore` | De regel ontbreekt of de nieuwe `.gitignore` is niet aangekomen | Stap 3 opnieuw, met `Add-Content` |
| `[FOUT] Token gevonden in ... getrackte bestanden` | Er staat nog een token in de code | Weghalen op de getoonde regel (stap 6) |
| `[FOUT] Token gevonden in ... nog niet gepushte commit(s)` | Het token zit in een lokale commit, ook al is het bestand intussen aangepast | `git reset --soft "@{u}"` en opnieuw committen zonder token |
| `[FOUT] github_secret_local.py wordt door git gevolgd` | Het bestand is ooit toegevoegd | `git rm --cached github_secret_local.py`, committen, en een **nieuw** token maken |
| `[FOUT] github_secret_local.py ontbreekt` | Nog niet aangemaakt | Stap 11 |
| `[FOUT] GITHUB_TOKEN ... is leeg` of `ziet er niet uit als een GitHub-token` | Niet geplakt, of met spaties/aanhalingstekens fout | Het bestand openen; exact `GITHUB_TOKEN = "github_pat_..."` |
| `[FOUT] GitHub WEIGERT het token (401)` | Ingetrokken of verkeerd gekopieerd | §7.3 |
| `[FOUT] Het token heeft geen toegang ... (HTTP 403/404)` | Verkeerde repo gekozen bij het token, of "Issues" staat niet op Read and write | Het token bewerken op GitHub; of `GITHUB_REPO` in de config nakijken |
| `[LET OP] GitHub niet bereikbaar` | Geen internet of een proxy | Later opnieuw; de build gaat wel door |
| `[LET OP] ... klassiek token (ghp_...)` | Oud type token | Vervangen door een fine-grained token (stap 10) |
| In de app: "Deze versie bevat geen GitHub-token" | `github_secret_local.py` ontbreekt (bij een start vanuit de broncode) | Stap 11. In een gebouwde versie kan dit niet voorkomen: de build stopt zonder token |
| In de app: "…ongeldig of ingetrokken" | Token ingetrokken | §7.3 |
| In de app: "…Issues staan uitgeschakeld" | Issues uit in de repo | Repo → Settings → Features → Issues aanzetten |
| Melding komt aan zonder label | Het label bestaat niet in de repo, of het token hoort bij een account zonder schrijfrechten op de repo (GitHub negeert labels dan stil) | Repo → Issues → Labels: `bug` en `enhancement` aanmaken; het token aanmaken als eigenaar van de repo |
| `ModuleNotFoundError: github_feedback_config` | Bestand niet gekopieerd of in de verkeerde map | Stap 4; bij een mappenstructuur in de projectroot (§5.2) |
| `ModuleNotFoundError: No module named 'requests'` | Niet in de venv | `pip install requests` + `requirements.txt` |
| `cannot be loaded ... not digitally signed` bij een `.ps1` | Script gemarkeerd als afkomstig van internet | `Unblock-File .\build_and_publish.ps1, .\publish.ps1` |
| `[FOUT] Build gestopt: de controle van het GitHub-token is mislukt` | Eén van de controles hierboven faalde tijdens de build | De `[FOUT]`-regel erboven lezen en oplossen |
| `NameError: name 'SPECPATH' is not defined` | Het controleblok staat niet in het spec-bestand maar in een gewoon script | Het blok hoort enkel in het `.spec`-bestand |
| Push geblokkeerd met `GH013` | Er zit een token in een commit | Niet toelaten; stap 2 en de tabelregel over "nog niet gepushte commits" |

---

## 9. Naslag

### 9.1 Wat de controle precies nakijkt

| # | Controle | Faalt de build? |
|---|---|---|
| 1 | `.gitignore` negeert `github_secret_local.py` | ja |
| 2 | `github_secret_local.py` wordt niet door git gevolgd | ja |
| 3 | Geen volledig token in getrackte bestanden | ja |
| 4 | Geen volledig token in nog niet gepushte commits | ja |
| 5 | `github_secret_local.py` bestaat, is gevuld, heeft de vorm van een token | ja (niet met `--skip-token`) |
| 6 | GitHub aanvaardt het token voor deze repo | ja bij 401/403/404; enkel een waarschuwing als GitHub onbereikbaar is (niet met `--skip-online`) |

Niet getest door de controle: of het token Issues mag **aanmaken**. Dat
bewijst stap 12.

Opties: `--skip-token` (enkel 1–4, voor zolang er nog geen token is) en
`--skip-online` (zonder internet).

### 9.2 Wat er naar GitHub gaat bij een melding

Eén aanroep: `POST /repos/<owner>/<repo>/issues` met
- **titel:** `🐞 Bug: ` of `✨ Feature: ` + de eerste regel van de
  omschrijving (maximaal 50 tekens);
- **tekst:** `Automatisch gegenereerde <type> door <naam> op <datum> (<App> <versie>):`,
  een lege regel, en dan de omschrijving;
- **label:** `bug` of `enhancement`.

Dat formaat (kopregel, lege regel, omschrijving) niet wijzigen: het
scherm met open meldingen knipt de kopregel weg.

### 9.3 Getest

| Wat | Hoe | Resultaat |
|---|---|---|
| Client | 28 controles tegen een nagebootste GitHub-API | geslaagd |
| Schermen, PySide6 | 17 controles zonder beeldscherm | geslaagd |
| Schermen, PyQt6 (na de omzetting uit §5.1) | dezelfde 17 controles | geslaagd |
| Controle-script | op een kopie van de ArticleSearch-repo, 10 scenario's | geslaagd |
| PyInstaller | mini-app: build stopt zonder token; met token zit het in de exe | geslaagd (Linux) |
| ArticleSearch, echt | bugmelding (issue #61), build en publish 15.6.0 | geslaagd |
| Mappenstructuur (§5.2), privé-repo (§5.5) | — | nog niet in de praktijk getest |
