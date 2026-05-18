#!/usr/bin/env python3
"""
Setup OAuth per YouTube Music.
Esegui questo script UNA SOLA VOLTA in locale per ottenere le credenziali.
Segui le istruzioni a schermo.
"""

import json
import sys
from pathlib import Path

try:
    from ytmusicapi import YTMusic
except ImportError:
    print("Installa prima le dipendenze: pip install -r requirements.txt")
    sys.exit(1)


def main() -> None:
    print("=" * 55)
    print("  YouTube Music — Setup autenticazione OAuth")
    print("=" * 55)
    print()
    print("Questo script aprirà il browser per autenticarti.")
    print("Le credenziali verranno salvate in oauth.json")
    print()

    oauth_path = "oauth.json"

    try:
        YTMusic.setup_oauth(filepath=oauth_path, open_browser=True)
    except Exception as e:
        print(f"Errore durante il setup OAuth: {e}")
        sys.exit(1)

    print()
    print(f"Credenziali salvate in: {oauth_path}")
    print()
    print("─" * 55)
    print("Per usare questo progetto su GitHub Actions:")
    print()
    print("  1. Vai su: GitHub repo → Settings → Secrets → Actions")
    print("  2. Crea un nuovo secret chiamato:  YTMUSIC_OAUTH")
    print("  3. Incolla il contenuto COMPLETO di oauth.json come valore")
    print()

    try:
        with open(oauth_path, "r") as f:
            content = json.load(f)
        print("Contenuto di oauth.json (copia come valore del secret):")
        print("─" * 55)
        print(json.dumps(content, indent=2))
    except Exception:
        print(f"Leggi manualmente il file: {Path(oauth_path).absolute()}")


if __name__ == "__main__":
    main()
