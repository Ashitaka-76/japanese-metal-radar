#!/usr/bin/env python3
"""
Setup autenticazione per YouTube Music tramite headers del browser.
Esegui questo script UNA SOLA VOLTA in locale. Non serve Google Cloud.

IMPORTANTE: devi copiare gli header da una richiesta POST all'API di YouTube
Music, non da una richiesta normale di pagina.
"""

import json
import sys
from pathlib import Path

try:
    import ytmusicapi
    from ytmusicapi import YTMusic
except ImportError:
    print("Installa prima le dipendenze: pip install -r requirements.txt")
    sys.exit(1)

AUTH_FILE = "browser.json"

GUIDE = """
Segui questi passi ESATTI nel browser:

  1. Apri https://music.youtube.com e assicurati di essere LOGGATO
     (deve comparire il tuo profilo in alto a destra)

  2. Premi F12 per aprire gli Strumenti sviluppatore

  3. Clicca sulla scheda "Network" (o "Rete")
     Attiva il filtro "Fetch/XHR" (pulsante nella barra dei filtri)

  4. Premi F5 per ricaricare la pagina

  5. Nell'elenco delle richieste cerca una che si chiama "browse"
     oppure "next" oppure "home" — deve essere una richiesta POST

  6. Clicca su quella richiesta

  7. Nel pannello di destra vai su "Headers" → sezione "Request Headers"

  8. SELEZIONA E COPIA TUTTO il testo degli header
     (deve contenere righe come: cookie: ..., authorization: ...,
      x-goog-authuser: ..., x-youtube-client-name: ...)

  Poi torna qui e incolla (Ctrl+V).
  Quando hai finito scrivi "fine" su una riga vuota e premi Invio.
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

    # Controlla che gli header contengano almeno cookie o authorization
    headers_lower = headers_raw.lower()
    if "cookie" not in headers_lower and "authorization" not in headers_lower:
        print()
        print("ATTENZIONE: Gli header incollati non contengono 'cookie' né 'authorization'.")
        print("Assicurati di aver copiato gli header da una richiesta POST autenticata.")
        print("Vedi le istruzioni sopra (punto 5: cerca 'browse' con metodo POST).")
        sys.exit(1)

    try:
        ytmusicapi.setup(filepath=AUTH_FILE, headers_raw=headers_raw)
    except Exception as e:
        print(f"\nErrore durante il setup: {e}")
        sys.exit(1)

    print(f"\nCredenziali salvate in: {AUTH_FILE}")
    print()

    # Test lettura
    print("Test connessione (ricerca)...")
    try:
        yt = YTMusic(AUTH_FILE)
        results = yt.search("BABYMETAL", filter="artists", limit=1)
        if results:
            print(f"  OK — trovato: {results[0].get('artist') or results[0].get('title')}")
        else:
            print("  OK (nessun risultato, ma la connessione funziona)")
    except Exception as e:
        print(f"  ERRORE lettura: {e}")
        print("  Riprova il setup con header aggiornati.")
        sys.exit(1)

    # Test scrittura (crea e cancella subito una playlist di prova)
    print("Test permessi scrittura (crea playlist di prova)...")
    try:
        test_id = yt.create_playlist("__radar_test__", "test")
        yt.delete_playlist(test_id)
        print("  OK — permessi di scrittura confermati")
    except Exception as e:
        print(f"  ERRORE scrittura: {e}")
        print()
        print("  Gli header funzionano per la lettura ma non per la scrittura.")
        print("  Assicurati di copiare gli header da una richiesta POST (es. 'browse')")
        print("  e non da una richiesta GET normale.")
        sys.exit(1)

    print()
    print("─" * 60)
    print("Setup completato con successo!")
    print()
    print("Per usare questo progetto su GitHub Actions:")
    print("  1. Repo → Settings → Secrets → Actions → New secret")
    print("  2. Nome: YTMUSIC_AUTH")
    print(f"  3. Valore: il contenuto completo di {AUTH_FILE} (vedi sotto)")
    print()

    try:
        with open(AUTH_FILE, "r") as f:
            content = json.load(f)
        print(f"Contenuto di {AUTH_FILE}:")
        print("─" * 60)
        print(json.dumps(content, indent=2))
    except Exception:
        print(f"Leggi manualmente: {Path(AUTH_FILE).absolute()}")


if __name__ == "__main__":
    main()
