# ArticleSearch — sessieblok 2026-10-10 (in te voegen in het context-bestand)

_Dit is GEEN volledig context-bestand. Het is het nieuwe sessieblok + de
aanpassingen aan §3, §5 en §7, klaar om bovenaan het laatste
`articlesearch_context_vX.md` te zetten. Reden: het recentste context-
bestand in de Project-bronnen is v26 (2026-08-31), terwijl de code intussen
verder staat (o.a. `docs/changelog.md` t.e.m. 15.4.0, `version.py` 15.5.1,
`ui_oeoverview.py`). Op basis van v26 een "v27" maken zou botsen met de
latere versies die lokaal bestaan. Lever het laatste context-bestand aan,
dan wordt dit blok erin verwerkt tot een volledige nieuwe versie._

---

> **Sessie 2026-10-10 — GitHub-token: echte oorzaak van de 401-fouten
> gevonden (Secret Scanning) + uniform feedbackpakket (optie A):**
>
> **Aanleiding:** "Bug of feature melden" gaf opnieuw `401 Client Error:
> Unauthorized for url: .../git/ref/heads/main` (screenshot). Gebruiker
> meldde hetzelfde probleem in zijn andere Python-apps.
>
> **Oorzaak — bevestigd met de security log van het GitHub-account
> (`barremans`, export 2026-04-15 → 2026-10-10):** GitHub trekt een token
> automatisch in zodra het in een publieke repo of gist gepusht wordt
> (Secret Scanning). `barremans/articlesearch` is publiek en het token
> stond hardcoded in getrackte bestanden. De eerdere conclusie uit
> sessies 20-23 en 26 ("verlopen/ingetrokken, oorzaak onbekend") is
> hiermee vervangen. Elk token sinds augustus is door de scanner
> ingetrokken (`token_scan`), geen enkel is verlopen of manueel verwijderd:
>
> | Aangemaakt | Ingetrokken | Levensduur |
> |---|---|---|
> | vóór 15/04 (klassiek) | 04/08 14:58 | onbekend |
> | vóór 15/04 ("Article search") | 04/08 14:58 | onbekend |
> | vóór 15/04 ("Updater token") | 04/08 14:58 | onbekend |
> | 06/08 12:17 | 06/08 14:37 | 2 u 20 min |
> | 06/08 14:55 | 31/08 08:57 | 25 dagen |
> | 31/08 09:36 | 31/08 10:17 | 41 min |
> | 16/09 13:55 | 16/09 14:08 | 13 min |
>
> - Een token leeft tot de eerste push waarin het zit. Het token van 25
>   dagen stierf op de dag van de push met "Allow me to expose this
>   secret" (sessie 26): die knop laat enkel de push door, ze beschermt
>   het token niet.
> - Na 16/09 14:08 bestond er geen geldig token meer.
> - Het token van 16/09 staat niet in `articlesearch` (laatste commit op
>   GitHub: 15/09) en is dus via een andere app gelekt. Op 16/09 13:47 is
>   `barremans/Project_generator` van privé naar publiek gezet.
> - Alle ingetrokken tokens hadden de scope `repo` (lezen/schrijven op
>   álle repo's, ook de privé-repo's). De log toont geen verdachte
>   wijzigingen, maar bevat geen IP-adressen en registreert geen clones.
>
> **Beslissingen (gebruiker):**
> - **Optie A**: token in een apart, niet-getrackt bestand
>   (`github_secret_local.py`, via `.gitignore`), meegebundeld door
>   PyInstaller. Het voorstel uit sessie 26 is hiermee doorgevoerd.
> - **Uniform pakket** voor al zijn apps (alle PySide6).
> - Meldingen blijven **per app in de eigen repo** (geen centrale
>   feedback-repo).
> - **Eén token per app.**
> - **Enkel Issues** (voorstel "A1"): een melding is voortaan altijd een
>   Issue; geen branch, `.md`-bestand of Pull Request meer. Reden: de
>   installer staat publiek bij de Releases, dus het token is eruit te
>   halen; met schrijfrechten op de code kon iemand
>   `releases/latest/version.txt` aanpassen (bepaalt wat "Update nu"
>   opent). Met enkel "Issues" kan dat niet. **Niet expliciet bevestigd
>   door gebruiker** — volgt uit zijn keuze voor het uniforme pakket; te
>   bevestigen bij de eerste test.
>
> **Nieuwe bestanden (uniform pakket):**
> - **`github_feedback.py`** (v1.0.0) — `GitHubFeedbackClient`:
>   `submit_report()` (1 API-call: `POST /issues`, label `bug` of
>   `enhancement`) en `get_open_reports()` (`GET /issues?state=open`,
>   opgesplitst in bugs/features; oude open PR's tellen als feature).
>   Geen Qt, geen token. Leest het token via `load_token()` uit
>   `github_secret_local.py`; ontbreekt dat, dan blijft de app werken en
>   geeft enkel het verzenden een nette melding. Bij een ingetrokken token
>   valt het lezen terug op anoniem (publieke repo). Fouten komen als
>   `GitHubFeedbackError` met Nederlandse tekst.
> - **`github_feedback_config.py`** (v1.0.0) — het enige bestand dat per
>   app verschilt: `APP_NAME`, `GITHUB_OWNER`, `GITHUB_REPO`,
>   `get_reporter_name()` (hier: AD-naam via `permissions_azure`),
>   `get_app_version()` (hier: `version.__version__`). Geen app-imports
>   bovenaan (wordt ook tijdens de build gelezen).
> - **`github_secret_local.example.py`** (v1.0.0) — sjabloon zonder token.
> - **`check_github_secret.py`** (v1.0.0) — controle: `.gitignore`-regel
>   aanwezig, secret-bestand niet getrackt, geen token in getrackte
>   bestanden, geen token in nog niet gepushte commits, token aanwezig en
>   door GitHub aanvaard. Opties `--skip-token`, `--skip-online`. Toont
>   nooit een volledig token.
>
> **Aangepaste bestanden:**
> - **`bug_report_dialog.py`** (v1.4.0 → v2.0.0): token en klasse
>   `GitHubClient` verwijderd; gebruikt `GitHubFeedbackClient`. Regel
>   "Bestandsnaam" uit de voorvertoning. Wachtcursor tijdens verzenden.
>   `BugDialog(parent, initial_type, initial_description)` ongewijzigd —
>   `ui_main.py` en `ui_peppol.py` hoeven niet aangepast.
> - **`github_cases.py`** (v1.3.0 → v2.0.0): token en klasse
>   `GitHubCasesClient` verwijderd. Rubrieken heten nu "Open
>   bugmeldingen" / "Open feature-aanvragen". Tekst wordt ge-escaped vóór
>   weergave als HTML. `show_github_cases(parent)` ongewijzigd.
> - **`updater.py`** (v1.2.0 → v1.3.0): `TOKEN` verwijderd;
>   `_headers_api()` stuurt geen Authorization-header meer (repo is
>   Public). Update-check via raw-URL en "Wat is er nieuw?" ongewijzigd.
> - **`SearchArticle.spec`** (v1.2.0 → v1.3.0): roept vóór de build
>   `check_github_secret.py` aan en stopt bij een fout;
>   `github_feedback_config` en `github_secret_local` toegevoegd aan
>   `hiddenimports`. **Gebaseerd op de versie op GitHub (15/09), niet op
>   een lokaal aangeleverd bestand.**
> - **`.gitignore`**: regel `*_secret_local.py` toegevoegd.
> - **`docs/changelog.md`**: entry `[15.6.0] - 2026-10-10`. Het
>   versienummer is een voorstel (minor-bump bij de build).
>
> **Niet aangepast:** `build_installer15.bat`, `build_and_publish.ps1`,
> `publish.ps1`, `ui_main.py`, `ui_peppol.py`, `config.py`.
>
> **Getest in deze sessie (niet op Windows, niet tegen het echte GitHub):**
> - Client tegen een nagebootste GitHub-API: 28 controles (bug/feature,
>   labels, titel, foutcodes 401/403/404/410/422/500, ingetrokken token,
>   offline, lezen zonder token).
> - Beide schermen in PySide6 6.12 zonder beeldscherm: 17 controles
>   (aanroep vanuit `ui_main.py` en `ui_peppol.py`, naam read-only,
>   fallback zonder naam, foutpad).
> - `check_github_secret.py` op een kopie van de repo: de huidige stand
>   faalt (3 tokens gevonden), na het toepassen van het pakket slaagt hij;
>   ook token in een getrackt bestand, in een niet-gepushte commit en een
>   geforceerd toegevoegd secret-bestand worden gevonden.
> - PyInstaller 6.22 (Linux) met een mini-app en het controleblok uit de
>   spec: build stopt zonder secret-bestand; mét secret-bestand zit
>   `github_secret_local` in de exe en leest de gebouwde exe het token.
>
> **Nog te doen (stap voor stap met gebruiker):**
> 1. Bestanden plaatsen, `python check_github_secret.py --skip-token`,
>    committen en pushen **zonder token**.
> 2. Fine-grained token aanmaken (enkel repo `articlesearch`; Issues =
>    Read and write; Pull requests = Read-only) en enkel in
>    `github_secret_local.py` zetten.
> 3. Lokaal testen: bug melden, feature melden, open cases.
> 4. Build + publish; daarna in de security log nakijken dat het token
>    niet ingetrokken is; testen op een geïnstalleerde machine.
> 5. Zelfde pakket uitrollen in de andere apps.
>
> **Regels vanaf nu:**
> - Het token staat enkel in `github_secret_local.py`. Niet in een ander
>   `.py`-bestand, niet in dit context-bestand, niet in `zzz/` of `temp/`,
>   ook niet gedeeltelijk in een versieheader.
> - Blokkeert GitHub een push (`GH013`): nooit "Allow me to expose this
>   secret" gebruiken. Het token uit de commit halen.
> - Bij een 401: eerst de security log bekijken (reden van intrekking),
>   dan pas een nieuw token maken.
>
> **Aangepaste/nieuwe bestanden deze sessie (alle volledig, als
> downloadbaar bestand):** `github_feedback.py` (v1.0.0, nieuw),
> `github_feedback_config.py` (v1.0.0, nieuw),
> `github_secret_local.example.py` (v1.0.0, nieuw),
> `check_github_secret.py` (v1.0.0, nieuw), `bug_report_dialog.py`
> (v2.0.0), `github_cases.py` (v2.0.0), `updater.py` (v1.3.0),
> `SearchArticle.spec` (v1.3.0), `.gitignore`, `docs/changelog.md`.

---

## Aanpassingen aan de vaste secties

### §3 Bestandsstructuur — te wijzigen/toe te voegen regels

```
bug_report_dialog.py          # v2.0.0 — BugDialog; verzendt via GitHubFeedbackClient, geen token meer in dit bestand
github_cases.py                # v2.0.0 — show_github_cases(); leest via GitHubFeedbackClient, geen token meer
github_feedback.py             # v1.0.0 — GitHubFeedbackClient (Issue aanmaken + open meldingen ophalen), uniform pakket
github_feedback_config.py      # v1.0.0 — app-specifiek: APP_NAME, GITHUB_OWNER/REPO, naam melder, app-versie
github_secret_local.example.py # v1.0.0 — sjabloon voor github_secret_local.py (dat laatste staat NIET in git)
check_github_secret.py         # v1.0.0 — controle "geen token in git" + "token aanwezig en geldig"; aangeroepen vanuit de spec
SearchArticle.spec            # v1.3.0 — PyInstaller build-spec, met tokencontrole vóór de build
updater.py                    # v1.3.0 — geen token meer; update-check en release notes werken anoniem
```

### §5 Nog te documenteren / open punten

- Punt 12 (GitHub-token-nasleep, sessie 26): **vervangen** door "Nog te
  doen" hierboven. Het voorstel `github_secret_local.py` is doorgevoerd.
- **Nieuw — `config.py` in de publieke repo:** `config.py` met de
  API-client-secrets staat in `barremans/articlesearch` (publiek).
  Buiten scope van deze sessie gehouden; te beslissen door gebruiker.
- **Nieuw — meldingen zijn publiek leesbaar:** Issues in een publieke
  repo bevatten de naam van de melder en bij Peppol-meldingen het
  factuurnummer en de ruwe foutboodschap. Gebruiker koos bewust voor
  "eigen repo"; een privé feedback-repo blijft een optie.
- **Nieuw — oude branches:** op GitHub staan 59 branches van eerdere
  meldingen (23 `bug-…`, 36 `feature-…`). Er komen er geen meer bij.
  Opruimen is optioneel.
- **Nieuw — `docs/changelog.md` mist 15.5.0 en 15.5.1:** de laatste entry
  vóór deze sessie was 15.4.0, terwijl `version.py` op 15.5.1 staat.
  Niet aangevuld (inhoud niet gekend).

### §7 Beveiliging — toe te voegen

**Update 2026-10-10:** de terugkerende 401-fouten kwamen door GitHub
Secret Scanning, niet door verlopen tokens. Hardcoded GitHub-tokens zijn
uit `bug_report_dialog.py`, `github_cases.py` en `updater.py` gehaald. Het
token staat nu in `github_secret_local.py` (niet in git) en is bedoeld als
fine-grained token voor één repo met enkel het recht "Issues". Wat dit
**niet** oplost: het token blijft uit de geïnstalleerde app te halen; de
schade daarvan is beperkt tot het aanmaken en lezen van Issues in die ene
repo. De bewuste keuze "moet werken zonder configuratie per machine"
blijft dus overeind.
