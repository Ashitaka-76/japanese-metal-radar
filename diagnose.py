#!/usr/bin/env python3
"""
Diagnostica: mostra lo stato di browser.json e fa un test API diretto.

Uso: python diagnose.py
"""

import json
import sys
from pathlib import Path

AUTH_FILE = "browser.json"

# Chiave pubblica usata da ytmusicapi internamente
YTM_API_KEY = "AIzaSyC9XL3ZjWddXya6X74dJoCTL-KLET5YdCE"
YTM_SEARCH_URL = f"https://music.youtube.com/youtubei/v1/search?key={YTM_API_KEY}"


def main() -> None:
    print("=" * 60)
    print("  Japanese Metal Radar — Diagnostica auth")
    print("=" * 60)
    print()

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

    important = [
        "cookie", "authorization", "x-goog-authuser",
        "x-youtube-client-name", "x-youtube-client-version",
        "user-agent", "origin", "x-origin",
    ]
    for key in important:
        val = auth.get(key, "")
        if val:
            preview = val[:80] + "..." if len(val) > 80 else val
            print(f"  [OK] {key}: {preview}")
        else:
            print(f"  [!!] {key}: MANCANTE")

    # Conta i cookie
    cookie_str = auth.get("cookie", "")
    cookie_names = [c.split("=")[0].strip() for c in cookie_str.split(";") if "=" in c]
    print(f"\n  Cookie presenti ({len(cookie_names)}): {', '.join(cookie_names)}")

    # Controlla cookie chiave per l'autenticazione
    for needed in ("SAPISID", "__Secure-1PSID", "__Secure-3PSID", "SID"):
        if needed in cookie_names:
            print(f"  [OK] Cookie di sessione trovato: {needed}")
            break
    else:
        print("  [!!] ATTENZIONE: nessun cookie di sessione principale trovato")
        print("       (SAPISID, __Secure-1PSID, __Secure-3PSID o SID)")
        print("       La richiesta copiata era probabilmente anonima.")

    print()

    # Test HTTP diretto (senza ytmusicapi)
    print("Test HTTP diretto (senza ytmusicapi)...")
    try:
        import urllib.request

        client_version = auth.get("x-youtube-client-version", "1.20250101.01.00")
        body = json.dumps({
            "context": {
                "client": {
                    "clientName": "WEB_REMIX",
                    "clientVersion": client_version,
                    "hl": "en",
                }
            },
            "query": "BABYMETAL",
        }).encode()

        req_headers = {
            "Content-Type": "application/json",
            "User-Agent": auth.get("user-agent", "Mozilla/5.0"),
            "Cookie": auth.get("cookie", ""),
        }
        if auth.get("authorization"):
            req_headers["Authorization"] = auth["authorization"]
        if auth.get("x-goog-authuser"):
            req_headers["X-Goog-AuthUser"] = auth["x-goog-authuser"]
        if auth.get("origin"):
            req_headers["Origin"] = auth["origin"]

        req = urllib.request.Request(YTM_SEARCH_URL, data=body, headers=req_headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            status = resp.status
            content_type = resp.headers.get("Content-Type", "")
            raw = resp.read()

        print(f"  HTTP status: {status}")
        print(f"  Content-Type: {content_type}")
        print(f"  Body length: {len(raw)} bytes")

        if len(raw) == 0:
            print("  [ERRORE] Risposta vuota — YouTube sta rifiutando la richiesta")
            print("  Causa probabile: cookie di sessione non validi o scaduti")
        else:
            try:
                data = json.loads(raw)
                if "contents" in data or "estimatedResults" in data:
                    print("  [OK] Risposta JSON valida con risultati di ricerca")
                elif "error" in data:
                    err = data["error"]
                    print(f"  [ERRORE API] {err.get('status')}: {err.get('message')}")
                else:
                    keys = list(data.keys())[:5]
                    print(f"  [OK] Risposta JSON ricevuta. Chiavi: {keys}")
            except Exception:
                preview = raw[:200].decode("utf-8", errors="replace")
                print(f"  [WARN] Risposta non-JSON: {preview}")

    except Exception as e:
        print(f"  [ERRORE] {e}")

    print()

    # Test ytmusicapi
    print("Test con ytmusicapi...")
    try:
        import ytmusicapi
        print(f"  ytmusicapi versione: {ytmusicapi.__version__}")
        from ytmusicapi import YTMusic
        yt = YTMusic(AUTH_FILE)
        results = yt.search("BABYMETAL", filter="artists", limit=1)
        if results:
            name = results[0].get("artist") or results[0].get("title")
            print(f"  [OK] Ricerca funziona — trovato: {name}")
        else:
            print("  [OK] Ricerca OK (0 risultati)")
    except Exception as e:
        print(f"  [ERRORE] ytmusicapi: {e}")
        print()
        print("  Se il test HTTP diretto ha funzionato ma ytmusicapi no,")
        print("  prova: pip install ytmusicapi==1.7.0")
        sys.exit(1)

    print()
    print("Test scrittura (crea/cancella playlist temporanea)...")
    try:
        from ytmusicapi import YTMusic
        yt = YTMusic(AUTH_FILE)
        tid = yt.create_playlist("__radar_diag__", "diag")
        yt.delete_playlist(tid)
        print("  [OK] Scrittura funziona")
    except Exception as e:
        print(f"  [ERRORE] Scrittura: {e}")
        sys.exit(1)

    print()
    print("[OK] Tutto funziona. Puoi eseguire: python main.py --first-run")


if __name__ == "__main__":
    main()
