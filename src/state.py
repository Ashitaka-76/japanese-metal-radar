import json
from datetime import datetime, timezone
from pathlib import Path

STATE_FILE = Path(__file__).parent.parent / "data" / "state.json"


def load_state() -> dict:
    if STATE_FILE.exists():
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"playlist_id": None, "artists": {}, "last_run": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def mark_last_run(state: dict) -> None:
    state["last_run"] = datetime.now(timezone.utc).isoformat()


def get_artist_state(state: dict, name: str) -> dict:
    return state["artists"].setdefault(name, {"browse_id": None, "known_album_ids": []})


def record_album_ids(state: dict, name: str, album_ids: list[str]) -> None:
    artist = get_artist_state(state, name)
    known = set(artist["known_album_ids"])
    known.update(album_ids)
    artist["known_album_ids"] = sorted(known)
