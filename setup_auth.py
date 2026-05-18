#!/usr/bin/env python3
"""
Setup autenticazione per YouTube Music tramite headers del browser.
Esegui questo script UNA SOLA VOLTA in locale. Non serve Google Cloud.

Istruzioni:
  1. Apri music.youtube.com nel browser (accedi con il tuo account)
  2. Apri gli Strumenti sviluppatore (F12)
  3. Vai nella scheda "Network" (Rete)
  4. Ricarica la pagina (F5)
  5. Clicca su una qualsiasi richiesta verso music.youtube.com
  6. Nella sezione "Request Headers", seleziona e copia TUTTI gli header
  7. Incollali qui sotto quando richiesto
"""

import sys
from pathlib import Path

try:
    import ytmusicapi
except ImportError:
    print("Installa prima le dipendenze: pip install -r requirements.txt")
    sys.exit(1)

AUTH_FILE = "browser.json"

GUIDE = """
Segui questi passi nel browser:

  1. Apri: https://music.youtube.com  (assicurati di essere loggato)
  2. Premi F12 per aprire gli Strumenti sviluppatore
  3. Clicca sulla scheda "Network" (o "Rete")
  4. Premi F5 per ricaricare la pagina
  5. Nell'elenco delle richieste, clicca sulla prima voce
     (di solito chiamata "/" o "browse")
  6. Nel pannello di destra, clicca su "Headers"
  7. Scorri fino a "Request Headers"
  8. Seleziona e copia TUTTO il testo degli header
     (da "accept:" fino all'ultimo header della lista)

Poi torna qui e incolla (Ctrl+V) seguito da INVIO e poi da una
riga contenente solo la parola:  fine
"""


def main() -> None:
    print("=" * 60)
    print("  YouTube Music — Setup autenticazione (browser headers)")
    print("=" * 60)
    print(GUIDE)

    print("Incolla gli header qui sotto, poi scrivi 'fine' su una riga vuota:")
    print("─" * 60)

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().lower() == "fine":
            break
        lines.append(line)

    if not lines:
        print("Nessun header inserito. Uscita.")
        sys.exit(1)

    headers_raw = "\n".join(lines)

    try:
        ytmusicapi.setup(filepath=AUTH_FILE, headers_raw=headers_raw)
    except Exception as e:
        print(f"\nErrore durante il setup: {e}")
        print("\nAssicurati di aver copiato gli header da music.youtube.com")
        print("e di essere loggato con il tuo account YouTube Music.")
        sys.exit(1)

    print()
    print(f"Credenziali salvate in: {AUTH_FILE}")
    print()
    print("─" * 60)
    print("Test di connessione...")
    try:
        from ytmusicapi import YTMusic
        yt = YTMusic(AUTH_FILE)
        results = yt.search("BABYMETAL", filter="artists", limit=1)
        if results:
            print("Connessione riuscita!")
        else:
            print("Connessione OK (nessun risultato di test, ma le credenziali sono valide)")
    except Exception as e:
        print(f"Attenzione: test fallito ({e})")
        print("Le credenziali sono state salvate ma potrebbero non funzionare.")

    print()
    print("─" * 60)
    print("Per usare questo progetto su GitHub Actions:")
    print()
    print("  1. Vai su: GitHub repo → Settings → Secrets → Actions")
    print("  2. Crea un nuovo secret chiamato:  YTMUSIC_AUTH")
    print(f"  3. Incolla il contenuto COMPLETO di {AUTH_FILE} come valore")
    print()

    try:
        import json
        with open(AUTH_FILE, "r") as f:
            content = json.load(f)
        print(f"Contenuto di {AUTH_FILE} (copia come valore del secret YTMUSIC_AUTH):")
        print("─" * 60)
        print(json.dumps(content, indent=2))
    except Exception:
        print(f"Leggi manualmente il file: {Path(AUTH_FILE).absolute()}")


if __name__ == "__main__":
    main()
