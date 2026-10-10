# =============================================================================
# GitHub-feedbackpakket (uniform — identiek in elke app)
# File:    github_secret_local.example.py
# Role:    SJABLOON voor github_secret_local.py. Dit sjabloon bevat geen
#          token en mag in git. Het echte bestand NIET.
# Version: 1.0.0
# Author:  Bart Bossuyt
# Changes: 1.0.0 — Eerste versie.
# =============================================================================
#
# Gebruik:
#   1. Kopieer dit bestand naar  github_secret_local.py  (zelfde map).
#   2. Plak het token tussen de aanhalingstekens hieronder, in die kopie.
#   3. Controleer:  python check_github_secret.py
#
# github_secret_local.py staat in .gitignore ("*_secret_local.py") en komt
# daardoor nooit op GitHub. PyInstaller bundelt het wel mee in de exe.
# Zet het token NERGENS anders: niet in dit sjabloon, niet in een ander
# .py-bestand, niet in het context-bestand, niet in zzz/ of temp/.
# GitHub trekt een token automatisch in zodra het in een publieke repo staat.

GITHUB_TOKEN = ""
