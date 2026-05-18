import json
import time
from pathlib import Path

from src.state import (
    get_artist_state,
    load_state,
    mark_last_run,
    record_album_ids,
    save_state,
)
from src.ytmusic_client import YTMusicClient

CONFIG_PATH = Path(__file__).parent.parent / "config" / "artists.json"
PLAYLIST_NAME = "Playlist Giappone"
PLAYLIST_DESCRIPTION = "Brani sincronizzati automaticamente da Japanese Metal Radar"


# ------------------------------------------------------------------
# Config helpers
# ------------------------------------------------------------------

def load_config(path: Path = CONFIG_PATH) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(config: dict, path: Path = CONFIG_PATH) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------

def _ensure_playlist(client: YTMusicClient, state: dict) -> str:
    if state.get("playlist_id"):
        return state["playlist_id"]
    print(f'Creo la playlist "{PLAYLIST_NAME}"...')
    playlist_id = client.create_playlist(PLAYLIST_NAME, PLAYLIST_DESCRIPTION)
    state["playlist_id"] = playlist_id
    print(f"  Playlist creata: {playlist_id}")
    return playlist_id


def _resolve_browse_id(
    client: YTMusicClient, name: str, state: dict
) -> str | None:
    artist_state = get_artist_state(state, name)
    if artist_state.get("browse_id"):
        return artist_state["browse_id"]

    print(f"  Cerco browse_id per '{name}'...")
    browse_id = client.find_artist_browse_id(name)
    if browse_id:
        artist_state["browse_id"] = browse_id
        print(f"  Trovato: {browse_id}")
    else:
        print(f"  ATTENZIONE: browse_id non trovato per '{name}'")
    return browse_id


# ------------------------------------------------------------------
# Public commands
# ------------------------------------------------------------------

def run_first_time(auth_file: str = "oauth.json") -> None:
    print("=" * 55)
    print("  Japanese Metal Radar — PRIMO AVVIO")
    print("  Importazione di tutti i brani esistenti...")
    print("=" * 55)

    client = YTMusicClient(auth_file)
    state = load_state()
    config = load_config()

    playlist_id = _ensure_playlist(client, state)
    existing_ids = client.get_playlist_video_ids(playlist_id)
    print(f"Brani già in playlist: {len(existing_ids)}\n")

    total_added = 0

    for artist in config["artists"]:
        name = artist["name"]
        print(f"▶ {name}")

        browse_id = _resolve_browse_id(client, name, state)
        if not browse_id:
            print()
            continue

        releases = client.get_artist_releases(browse_id)
        print(f"  Release trovate: {len(releases)}")

        known_albums = set(get_artist_state(state, name).get("known_album_ids", []))
        new_vids, new_album_ids = client.collect_tracks(releases, known_albums, existing_ids)

        if new_vids:
            added = client.add_tracks(playlist_id, new_vids)
            existing_ids.update(new_vids)
            total_added += added
            print(f"  → Aggiunti {added} brani")
        else:
            print(f"  → Nessun brano nuovo da aggiungere")

        record_album_ids(state, name, new_album_ids)
        save_state(state)
        print()
        time.sleep(1)

    mark_last_run(state)
    save_state(state)
    print("=" * 55)
    print(f'  Completato! {total_added} brani aggiunti a "{PLAYLIST_NAME}"')
    print("=" * 55)


def run_update(auth_file: str = "oauth.json") -> None:
    print("=" * 55)
    print("  Japanese Metal Radar — AGGIORNAMENTO")
    print("=" * 55)

    client = YTMusicClient(auth_file)
    state = load_state()
    config = load_config()

    if not state.get("playlist_id"):
        print("Nessuna playlist trovata. Esegui prima con --first-run.")
        return

    playlist_id = state["playlist_id"]
    existing_ids = client.get_playlist_video_ids(playlist_id)
    print(f"Brani in playlist: {len(existing_ids)}\n")

    total_added = 0

    for artist in config["artists"]:
        name = artist["name"]
        print(f"▶ {name}")

        browse_id = _resolve_browse_id(client, name, state)
        if not browse_id:
            print()
            continue

        releases = client.get_artist_releases(browse_id)
        known_albums = set(get_artist_state(state, name).get("known_album_ids", []))

        new_releases = [
            r for r in releases
            if r.get("browseId") and r["browseId"] not in known_albums
        ]

        if not new_releases:
            print("  Nessuna nuova uscita\n")
            continue

        print(f"  Nuove uscite: {len(new_releases)}")
        new_vids, new_album_ids = client.collect_tracks(new_releases, known_albums, existing_ids)

        if new_vids:
            added = client.add_tracks(playlist_id, new_vids)
            existing_ids.update(new_vids)
            total_added += added
            print(f"  → Aggiunti {added} brani")

        record_album_ids(state, name, new_album_ids)
        save_state(state)
        print()
        time.sleep(1)

    mark_last_run(state)
    save_state(state)
    print("=" * 55)
    print(f"  Completato! {total_added} nuovi brani aggiunti.")
    print("=" * 55)


def add_artist(name: str) -> None:
    config = load_config()
    existing = {a["name"].lower() for a in config["artists"]}
    if name.lower() in existing:
        print(f"'{name}' è già nella lista degli artisti monitorati.")
        return
    config["artists"].append({"name": name})
    save_config(config)
    print(f"'{name}' aggiunto alla lista degli artisti.")
    print("Esegui con --first-run per importare i brani esistenti di questo artista.")
