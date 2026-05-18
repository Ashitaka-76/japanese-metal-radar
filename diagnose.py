#!/usr/bin/env python3
"""
Diagnostica: mostra lo stato di browser.json e fa un test API diretto.
Utile per capire perché l'autenticazione non funziona.

Uso: python diagnose.py
"""

import json
import sys
from pathlib import Path

AUTH_FILE = "browser.json"


def main() -> None:
    print("=" * 60)
    print("  Japanese Metal Radar — Diagnostica auth")
    print("=" * 60)
    print()

    # 1. Controlla browser.json
    p = Path(AUTH_FILE)
    if not p.exists():
        print(f"[MANCANTE] {AUTH_FILE} non trovato.")
        print("Esegui prima: python setup_auth.py")
        sys.exit(1)

    try:
        auth = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"[ERRORE] Impossibile leggere {AUTH_FILE}: {e}")
        sys.exit(1)

    print(f"[OK] {AUTH_FILE} trovato con {len(auth)} campi")
    print()
    print("Campi presenti:")
    important = ["cookie", "authorization", "x-goog-authuser",
                 "x-youtube-client-name", "x-youtube-client-version",
                 "user-agent", "origin", "x-origin"]
    for key in important:
        val = auth.get(key, "")
        if val:
            preview = val[:60] + "..." if len(val) > 60 else val
            print(f"  [OK] {key}: {preview}")
        else:
            print(f"  [!]  {key}: MANCANTE")

    print()

    # 2. Test ytmusicapi
    try:
        from ytmusicapi import YTMusic
    except ImportError:
        print("[ERRORE] ytmusicapi non installato: pip install -r requirements.txt")
        sys.exit(1)

    print("Test con ytmusicapi...")
    try:
        yt = YTMusic(AUTH_FILE)
        results = yt.search("BABYMETAL", filter="artists", limit=1)
        if results:
            name = results[0].get("artist") or results[0].get("title")
            print(f"  [OK] Ricerca funziona — trovato: {name}")
        else:
            print("  [OK] Ricerca OK (0 risultati)")
    except Exception as e:
        print(f"  [ERRORE] Ricerca fallita: {e}")
        print()
        print("Possibili cause:")
        print("  - Gli header in browser.json sono scaduti (rifai setup_auth.py)")
        print("  - Il campo 'cookie' non contiene una sessione valida")
        print("  - La richiesta copiata era anonima (non autenticata)")
        sys.exit(1)

    print()
    print("Test creazione playlist...")
    try:
        tid = yt.create_playlist("__radar_diag__", "diag")
        yt.delete_playlist(tid)
        print("  [OK] Scrittura funziona")
    except Exception as e:
        print(f"  [ERRORE] Scrittura fallita: {e}")
        sys.exit(1)

    print()
    print("[OK] Tutto funziona. Puoi eseguire: python main.py --first-run")


if __name__ == "__main__":
    main()
