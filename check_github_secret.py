# =============================================================================
# GitHub-feedbackpakket (uniform — identiek in elke app)
# File:    check_github_secret.py
# Role:    Controle vóór elke commit/push en vóór elke build:
#            1. staat het GitHub-token nergens in een bestand dat naar
#               GitHub gaat (getrackte bestanden + nog niet gepushte
#               commits)?
#            2. is github_secret_local.py aanwezig, genegeerd door git en
#               gevuld met een token dat GitHub nog aanvaardt?
#          Wordt automatisch aangeroepen vanuit het .spec-bestand, zodat
#          een build zonder (geldig) token stopt i.p.v. een installer af te
#          leveren waarin "Bug of feature melden" niet werkt.
#          Gebruikt enkel de standaardbibliotheek en bevat geen Qt.
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Eerste versie.
# =============================================================================
#
# Gebruik (vanuit de map van de app):
#     python check_github_secret.py                volledige controle
#     python check_github_secret.py --skip-token   enkel "geen token in git"
#                                                  (zolang er nog geen
#                                                  token aangemaakt is)
#     python check_github_secret.py --skip-online  token niet bij GitHub
#                                                  testen (bv. zonder internet)
# Exitcode 0 = in orde, 1 = minstens één fout.

from __future__ import annotations

import argparse
import json
import os
import re
import runpy
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
SECRET_FILE = "github_secret_local.py"
CONFIG_FILE = "github_feedback_config.py"

# Volledige tokens: klassiek (ghp_...) en verwante types, en fine-grained
# (github_pat_...). Korte, afgekapte vermeldingen in oude commentaarregels
# (bv. "ghp_Abc12345...") vallen hier bewust buiten.
TOKEN_PATTERN = r"gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}"
TOKEN_RE = re.compile(TOKEN_PATTERN)
MAX_UNPUSHED_COMMITS = 200

_errors: list[str] = []
_warnings: list[str] = []


def _out(tag: str, text: str) -> None:
    print(f"[{tag}] {text}")


def ok(text: str) -> None:
    _out("OK", text)


def fail(text: str) -> None:
    _errors.append(text)
    _out("FOUT", text)


def warn(text: str) -> None:
    _warnings.append(text)
    _out("LET OP", text)


def mask(text: str) -> str:
    """Toont nooit een volledig token op het scherm of in een logbestand."""
    return TOKEN_RE.sub(lambda m: m.group(0)[:10] + "...[verborgen]", text)


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")


def git_available() -> bool:
    try:
        return git("rev-parse", "--is-inside-work-tree").returncode == 0
    except OSError:
        return False


# ----------------------------------------------------------------- controles
def check_ignored() -> None:
    # --no-index: beoordeel enkel de .gitignore-regels, ook als het bestand
    # (per ongeluk) al door git gevolgd wordt.
    if git("check-ignore", "-q", "--no-index", SECRET_FILE).returncode == 0:
        ok(f"{SECRET_FILE} wordt genegeerd door git (.gitignore).")
    else:
        fail(f"{SECRET_FILE} staat NIET in .gitignore. Voeg de regel "
             f"'*_secret_local.py' toe aan .gitignore.")

    if git("ls-files", "--error-unmatch", SECRET_FILE).returncode == 0:
        fail(f"{SECRET_FILE} wordt door git gevolgd (staat in de repo). Haal het eruit met: "
             f"git rm --cached {SECRET_FILE}  — en maak daarna een NIEUW token aan.")
    else:
        ok(f"{SECRET_FILE} staat niet in de repo.")


def check_tracked_files() -> None:
    res = git("grep", "-I", "-n", "-E", TOKEN_PATTERN)
    if res.returncode == 1:
        ok("Geen token gevonden in de bestanden die naar GitHub gaan.")
    elif res.returncode == 0:
        hits = [ln for ln in res.stdout.splitlines() if ln.strip()]
        fail(f"Token gevonden in {len(hits)} regel(s) van getrackte bestanden. "
             f"NIET committen of pushen:")
        for ln in hits[:20]:
            print("        " + mask(ln)[:160])
    else:
        warn(f"Kon de getrackte bestanden niet doorzoeken: {res.stderr.strip()[:200]}")


def check_unpushed_commits() -> None:
    upstream = git("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}")
    if upstream.returncode != 0:
        warn("Geen upstream-branch ingesteld: nog niet gepushte commits zijn niet gecontroleerd.")
        return
    revs = [r for r in git("rev-list", f"--max-count={MAX_UNPUSHED_COMMITS}", "@{u}..HEAD").stdout.split() if r]
    if not revs:
        ok("Geen nog niet gepushte commits.")
        return
    bad: list[str] = []
    for rev in revs:
        res = git("grep", "-I", "-l", "-E", TOKEN_PATTERN, rev)
        if res.returncode == 0:
            files = sorted({ln.split(":", 1)[1] for ln in res.stdout.splitlines() if ":" in ln})
            bad.append(f"{rev[:8]}: {', '.join(files)[:120]}")
    if bad:
        fail(f"Token gevonden in {len(bad)} nog niet gepushte commit(s). NIET pushen — het token "
             f"zit in de geschiedenis, ook als het bestand intussen aangepast is:")
        for ln in bad[:20]:
            print("        " + ln)
        print("        Oplossing: die commits ongedaan maken (bv. 'git reset --soft @{u}') "
              "en opnieuw committen zonder token.")
    else:
        ok(f"Geen token in de {len(revs)} nog niet gepushte commit(s).")


def load_token() -> str | None:
    path = os.path.join(ROOT, SECRET_FILE)
    if not os.path.isfile(path):
        fail(f"{SECRET_FILE} ontbreekt. Kopieer github_secret_local.example.py naar "
             f"{SECRET_FILE} en zet er het token in.")
        return None
    try:
        token = str(runpy.run_path(path).get("GITHUB_TOKEN", "") or "").strip()
    except Exception as exc:
        fail(f"{SECRET_FILE} kan niet gelezen worden: {exc.__class__.__name__}: {exc}")
        return None
    if not token:
        fail(f"GITHUB_TOKEN in {SECRET_FILE} is leeg.")
        return None
    if not TOKEN_RE.fullmatch(token):
        fail(f"GITHUB_TOKEN in {SECRET_FILE} ziet er niet uit als een GitHub-token "
             f"(verwacht: begint met 'github_pat_' of 'ghp_', zonder spaties).")
        return None
    if token.startswith("github_pat_"):
        ok(f"{SECRET_FILE} bevat een fine-grained token.")
    else:
        warn(f"{SECRET_FILE} bevat een klassiek token (ghp_...). Dat geeft toegang tot AL je "
             f"repo's; een fine-grained token voor enkel deze repo is veiliger.")
    return token


def load_repo() -> tuple[str, str] | None:
    path = os.path.join(ROOT, CONFIG_FILE)
    if not os.path.isfile(path):
        fail(f"{CONFIG_FILE} ontbreekt.")
        return None
    try:
        cfg = runpy.run_path(path)
        owner, repo = str(cfg["GITHUB_OWNER"]).strip(), str(cfg["GITHUB_REPO"]).strip()
    except Exception as exc:
        fail(f"{CONFIG_FILE} kan niet gelezen worden: {exc.__class__.__name__}: {exc}")
        return None
    if not owner or not repo:
        fail(f"GITHUB_OWNER/GITHUB_REPO in {CONFIG_FILE} zijn niet ingevuld.")
        return None
    return owner, repo


def check_online(token: str, owner: str, repo: str, api_root: str) -> None:
    url = f"{api_root}/repos/{owner}/{repo}/issues?state=open&per_page=1"
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "check_github_secret",
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            json.loads(resp.read().decode("utf-8", errors="replace") or "[]")
            ok(f"GitHub aanvaardt het token voor {owner}/{repo} (Issues leesbaar).")
            print("        Niet getest: of het token ook Issues mag AANMAKEN. Test dat één keer "
                  "in de app zelf (Rapporteren > Bug of feature melden).")
    except urllib.error.HTTPError as exc:
        if exc.code == 401:
            fail("GitHub WEIGERT het token (401): het is ongeldig of ingetrokken. Maak een nieuw "
                 "token aan — hetzelfde token opnieuw invullen helpt nooit.")
        elif exc.code in (403, 404):
            fail(f"Het token heeft geen toegang tot {owner}/{repo} of mist het recht 'Issues' "
                 f"(HTTP {exc.code}). Controleer 'Repository access' en 'Permissions' van het token.")
        else:
            warn(f"Onverwacht antwoord van GitHub (HTTP {exc.code}); token niet bevestigd.")
    except Exception as exc:
        warn(f"GitHub niet bereikbaar ({exc.__class__.__name__}); token niet online getest.")


# ----------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Controle van het GitHub-token (feedbackpakket).")
    parser.add_argument("--skip-token", action="store_true",
                        help="github_secret_local.py niet controleren (enkel 'geen token in git').")
    parser.add_argument("--skip-online", action="store_true",
                        help="het token niet bij GitHub testen.")
    parser.add_argument("--api-root", default="https://api.github.com", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass

    print("=== Controle GitHub-token ===")
    if git_available():
        check_ignored()
        check_tracked_files()
        check_unpushed_commits()
    else:
        warn("git niet gevonden of dit is geen git-map: de controles 'geen token in git' zijn overgeslagen.")

    if args.skip_token:
        print("[--] Controle van github_secret_local.py overgeslagen (--skip-token).")
    else:
        token = load_token()
        repo = load_repo()
        if token and repo and not args.skip_online:
            check_online(token, repo[0], repo[1], args.api_root.rstrip("/"))
        elif token and repo:
            print("[--] Online test overgeslagen (--skip-online).")

    print()
    if _errors:
        print(f"RESULTAAT: {len(_errors)} fout(en) - eerst oplossen.")
        return 1
    if _warnings:
        print(f"RESULTAAT: in orde, met {len(_warnings)} aandachtspunt(en).")
    else:
        print("RESULTAAT: in orde.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
