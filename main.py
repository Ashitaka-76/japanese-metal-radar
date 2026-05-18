#!/usr/bin/env python3
"""
Japanese Metal Radar
Monitora le uscite discografiche di artisti giapponesi e le sincronizza
automaticamente nella playlist YouTube Music "Playlist Giappone".

Utilizzo:
  python main.py                        # controlla nuove uscite
  python main.py --first-run            # importa TUTTO (primo avvio)
  python main.py --add-artist "Nome"    # aggiunge un artista alla lista
"""

import argparse
import sys

from src.radar import add_artist, run_first_time, run_update


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Japanese Metal Radar — sync automatico su YouTube Music",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--first-run",
        action="store_true",
        help="Importa TUTTI i brani esistenti e crea la playlist (da eseguire una sola volta)",
    )
    parser.add_argument(
        "--add-artist",
        metavar="NOME_ARTISTA",
        help="Aggiunge un nuovo artista alla lista di monitoraggio",
    )
    parser.add_argument(
        "--auth",
        default="oauth.json",
        metavar="FILE",
        help="Percorso al file OAuth di ytmusicapi (default: oauth.json)",
    )

    args = parser.parse_args()

    if args.add_artist:
        add_artist(args.add_artist)
        sys.exit(0)

    if args.first_run:
        run_first_time(args.auth)
    else:
        run_update(args.auth)


if __name__ == "__main__":
    main()
