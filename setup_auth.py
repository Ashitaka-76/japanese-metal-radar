#!/usr/bin/env python3
"""
Setup autenticazione YouTube Music.

Salva gli header in un file di testo e poi esegui questo script.
Vedi le istruzioni stampate a schermo.
"""

import json
import re
import sys
from pathlib import Path

try:
    import ytmusicapi
    from ytmusicapi import YTMusic
except ImportError:
    print("Installa prima le dipendenze: pip install -r requirements.txt")
    sys.exit(1)

AUTH_FILE = "browser.json"
HEADERS_FILE = "headers.txt"

GUIDE = f"""
Segui questi passi:

  1. Apri https://music.youtube.com — assicurati di essere LOGGATO

  2. Premi F12 → scheda "Network" → attiva filtro "Fetch/XHR"

  3. Premi F5 per ricaricare la pagina

  4. Nell'elenco cerca una riga con nome "browse" e metodo POST
     (oppure "next" o "search" — qualsiasi POST verso music.youtube.com)

  5. Clicca su quella riga → pannello destro → "Headers"
     → sezione "Request Headers"

  6. Fai click destro sugli header → "Copy" (o seleziona tutto con Ctrl+A
     e copia con Ctrl+C)

  7. Apri il Blocco Note (o qualsiasi editor di testo)
     Incolla il testo e salvalo come:
        {Path(HEADERS_FILE).absolute()}

  8. Torna qui e premi INVIO per continuare.
"""


def load_headers_from_file(path: str) -> str:
    p = Path(path)
    if not p.exists():
        print(f"File non trovato: {p.absolute()}")
        print(f"Crea il file {path} con gli header copiati dal browser.")
        sys.exit(1)
    return p.read_text(encoding="utf-8", errors="replace")


def sanitize_headers(raw: str) -> str:
    """Rimuove pseudo-header HTTP/2 (:authority, :method, ecc.) e righe vuote."""
    lines = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith(":"):  # pseudo-header HTTP/2
            continue
        lines.append(stripped)
    return "\n".join(lines)


def check_required_fields(raw: str) -> list[str]:
    missing = []
    lower = raw.lower()
    if "cookie" not in lower:
        missing.append("cookie")
    if "authorization" not in lower and "x-goog-authuser" not in lower:
        missing.append("authorization / x-goog-authuser")
    return missing


def main() -> None:
    print("=" * 60)
    print("  YouTube Music — Setup autenticazione")
    print("=" * 60)
    print(GUIDE)

    input("Premi INVIO quando hai salvato il file headers.txt...")
    print()

    raw = load_headers_from_file(HEADERS_FILE)
    raw = sanitize_headers(raw)

    missing = check_required_fields(raw)
    if missing:
        print(f"ATTENZIONE: gli header non contengono: {', '.join(missing)}")
        print("Assicurati di copiare da una richiesta POST autenticata (filtro Fetch/XHR).")
        print("Gli header devono includere 'cookie:' e 'authorization:'.")
        sys.exit(1)

    print(f"Header caricati ({raw.count(chr(10)) + 1} righe). Configuro ytmusicapi...")

    try:
        ytmusicapi.setup(filepath=AUTH_FILE, headers_raw=raw)
    except Exception as e:
        print(f"Errore setup: {e}")
        sys.exit(1)

    print(f"Credenziali salvate in: {AUTH_FILE}")
    print()

    # Test lettura
    print("Test lettura...")
    try:
        yt = YTMusic(AUTH_FILE)
        results = yt.search("BABYMETAL", filter="artists", limit=1)
        name = results[0].get("artist") or results[0].get("title") if results else "?"
        print(f"  OK — trovato: {name}")
    except Exception as e:
        print(f"  ERRORE: {e}")
        print("  Gli header potrebbero essere scaduti o non validi.")
        sys.exit(1)

    # Test scrittura
    print("Test scrittura (crea/cancella playlist temporanea)...")
    try:
        tid = yt.create_playlist("__radar_test__", "test")
        yt.delete_playlist(tid)
        print("  OK — permessi di scrittura confermati")
    except Exception as e:
        print(f"  ERRORE scrittura: {e}")
        print("  Prova a copiare gli header da un'altra richiesta POST.")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  Setup completato con successo!")
    print("=" * 60)
    print()
    print("Per GitHub Actions:")
    print("  Repo → Settings → Secrets → Actions → New secret")
    print("  Nome: YTMUSIC_AUTH")
    print(f"  Valore: contenuto completo di {AUTH_FILE}")
    print()

    try:
        with open(AUTH_FILE, "r") as f:
            content = json.load(f)
        print(f"--- Contenuto di {AUTH_FILE} ---")
        print(json.dumps(content, indent=2))
    except Exception:
        print(f"Leggi manualmente: {Path(AUTH_FILE).absolute()}")


if __name__ == "__main__":
    main()
