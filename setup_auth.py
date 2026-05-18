#!/usr/bin/env python3
"""
Setup OAuth per YouTube Music.
Esegui questo script UNA SOLA VOLTA in locale per ottenere le credenziali.

Prerequisiti (5 minuti):
  1. Vai su https://console.cloud.google.com/
  2. Crea un nuovo progetto (es. "japanese-metal-radar")
  3. Abilita l'API: "YouTube Data API v3"
  4. Vai su "Credenziali" → "Crea credenziali" → "ID client OAuth 2.0"
  5. Tipo applicazione: "App desktop"
  6. Copia Client ID e Client Secret
  7. In "Schermata consenso OAuth" aggiungiti come utente di test
"""

import json
import sys
from pathlib import Path

try:
    import ytmusicapi
except ImportError:
    print("Installa prima le dipendenze: pip install -r requirements.txt")
    sys.exit(1)


GUIDE = """
Prima di continuare devi creare delle credenziali OAuth su Google Cloud.
Segui questi passi (circa 5 minuti):

  1. Apri: https://console.cloud.google.com/
  2. Crea un nuovo progetto → dagli un nome qualsiasi
  3. Menu laterale → "API e servizi" → "Libreria"
     Cerca "YouTube Data API v3" → Abilita
  4. Menu laterale → "API e servizi" → "Credenziali"
     → "Crea credenziali" → "ID client OAuth 2.0"
     → Tipo: "App desktop" → Crea
  5. Copia il CLIENT ID e il CLIENT SECRET mostrati
  6. Menu → "Schermata consenso OAuth" → "Utenti di test"
     → Aggiungi il tuo indirizzo Gmail
"""


def main() -> None:
    print("=" * 60)
    print("  YouTube Music — Setup autenticazione OAuth")
    print("=" * 60)
    print(GUIDE)

    client_id = input("Incolla il CLIENT ID: ").strip()
    if not client_id:
        print("Client ID non inserito. Uscita.")
        sys.exit(1)

    client_secret = input("Incolla il CLIENT SECRET: ").strip()
    if not client_secret:
        print("Client Secret non inserito. Uscita.")
        sys.exit(1)

    oauth_path = "oauth.json"
    print()
    print("Il browser si aprirà per completare l'autenticazione...")

    try:
        ytmusicapi.setup_oauth(
            client_id=client_id,
            client_secret=client_secret,
            filepath=oauth_path,
            open_browser=True,
        )
    except Exception as e:
        print(f"\nErrore durante il setup OAuth: {e}")
        sys.exit(1)

    print()
    print(f"Credenziali salvate in: {oauth_path}")
    print()
    print("─" * 60)
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
        print("─" * 60)
        print(json.dumps(content, indent=2))
    except Exception:
        print(f"Leggi manualmente il file: {Path(oauth_path).absolute()}")


if __name__ == "__main__":
    main()
