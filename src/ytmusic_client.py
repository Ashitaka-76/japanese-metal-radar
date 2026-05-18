import json
import time
import urllib.request
import urllib.error
from typing import Any

from ytmusicapi import YTMusic
from ytmusicapi.helpers import get_authorization, sapisid_from_cookie

CHUNK_SIZE = 50
REQUEST_DELAY = 0.4

# Chiave di accesso pubblica YouTube Music (ignorata quando si usano i cookie)
_YTM_KEY = "AIzaSyC9XL3ZjWddXya6X74dJoCTL-KLET5YdCE"
_YTM_BASE = "https://music.youtube.com/youtubei/v1/"


class YTMusicClient:
    def __init__(self, auth_file: str = "browser.json"):
        with open(auth_file, encoding="utf-8") as f:
            self._auth = json.load(f)

        self.yt = YTMusic(auth_file)
        self._override_send_request()

    # ------------------------------------------------------------------
    # Core request override
    # ------------------------------------------------------------------

    def _make_headers(self) -> dict[str, str]:
        """Costruisce gli header per ogni richiesta con hash SAPISIDHASH fresco."""
        auth = self._auth
        cookie = auth.get("cookie", "")
        origin = auth.get("origin") or auth.get("x-origin") or "https://music.youtube.com"

        try:
            sapisid = sapisid_from_cookie(cookie)
            fresh_auth = get_authorization(sapisid + " " + origin)
        except Exception:
            fresh_auth = auth.get("authorization", "")

        return {
            "Content-Type": "application/json",
            "Cookie": cookie,
            "Authorization": fresh_auth,
            "X-Goog-AuthUser": auth.get("x-goog-authuser", "0"),
            "User-Agent": auth.get("user-agent", "Mozilla/5.0"),
            "Origin": origin,
            "X-Origin": auth.get("x-origin", origin),
            "X-YouTube-Client-Name": auth.get("x-youtube-client-name", "67"),
            "X-YouTube-Client-Version": auth.get("x-youtube-client-version", ""),
        }

    def _raw_post(self, endpoint: str, body: dict, extra_params: str = "") -> Any:
        """Esegue una POST all'API interna di YouTube Music."""
        url = f"{_YTM_BASE}{endpoint}?key={_YTM_KEY}{extra_params}"
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=self._make_headers())
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())

    def _override_send_request(self) -> None:
        """
        Sostituisce _send_request di ytmusicapi con la nostra implementazione
        urllib che funziona con i cookie di sessione. Mantiene intatto tutto il
        parsing delle risposte di ytmusicapi.
        """
        client = self

        def patched(endpoint: str, body: dict, additionalParams: str = "") -> dict:
            body.update(client.yt.context)
            return client._raw_post(endpoint, body, additionalParams)

        self.yt._send_request = patched

    # ------------------------------------------------------------------
    # Artist lookup
    # ------------------------------------------------------------------

    def find_artist_browse_id(self, artist_name: str) -> str | None:
        results = self.yt.search(artist_name, filter="artists", limit=10)
        name_lower = artist_name.lower()

        for r in results:
            candidate = (r.get("artist") or r.get("title") or "").lower()
            if name_lower == candidate or name_lower in candidate or candidate in name_lower:
                return r["browseId"]

        for r in results:
            if r.get("resultType") == "artist":
                return r["browseId"]

        return None

    # ------------------------------------------------------------------
    # Release fetching
    # ------------------------------------------------------------------

    def get_artist_releases(self, browse_id: str) -> list[dict]:
        releases: list[dict] = []
        try:
            data = self.yt.get_artist(browse_id)
        except Exception as e:
            print(f"    [error] get_artist({browse_id}): {e}")
            return releases

        for section_key in ("albums", "singles"):
            section = data.get(section_key)
            if not section:
                continue
            results = section.get("results", [])

            if section.get("browseId") and section.get("params"):
                try:
                    all_items = self.yt.get_artist_albums(
                        section["browseId"], section["params"]
                    )
                    if all_items:
                        results = all_items
                except Exception as e:
                    print(f"    [warn] get_artist_albums: {e}")

            releases.extend(results)

        return releases

    def get_album_tracks(self, browse_id: str) -> list[str]:
        try:
            album = self.yt.get_album(browse_id)
            return [
                t["videoId"]
                for t in album.get("tracks", [])
                if t.get("videoId")
            ]
        except Exception as e:
            print(f"    [error] get_album({browse_id}): {e}")
            return []

    # ------------------------------------------------------------------
    # Playlist management
    # ------------------------------------------------------------------

    def create_playlist(self, title: str, description: str = "") -> str:
        return self.yt.create_playlist(title, description)

    def get_playlist_video_ids(self, playlist_id: str) -> set[str]:
        try:
            playlist = self.yt.get_playlist(playlist_id, limit=10000)
            return {t["videoId"] for t in playlist.get("tracks", []) if t.get("videoId")}
        except Exception as e:
            print(f"    [error] get_playlist: {e}")
            return set()

    def add_tracks(self, playlist_id: str, video_ids: list[str]) -> int:
        if not video_ids:
            return 0
        added = 0
        deduped = list(dict.fromkeys(video_ids))
        for i in range(0, len(deduped), CHUNK_SIZE):
            chunk = deduped[i : i + CHUNK_SIZE]
            try:
                self.yt.add_playlist_items(playlist_id, chunk, duplicates=False)
                added += len(chunk)
                if i + CHUNK_SIZE < len(deduped):
                    time.sleep(1)
            except Exception as e:
                print(f"    [error] add_playlist_items (chunk {i}): {e}")
        return added

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------

    def collect_tracks(
        self,
        releases: list[dict],
        skip_album_ids: set[str],
        skip_video_ids: set[str],
    ) -> tuple[list[str], list[str]]:
        new_video_ids: list[str] = []
        new_album_ids: list[str] = []

        for release in releases:
            album_browse_id = release.get("browseId")
            if not album_browse_id or album_browse_id in skip_album_ids:
                continue

            title = release.get("title", album_browse_id)
            tracks = self.get_album_tracks(album_browse_id)
            fresh = [vid for vid in tracks if vid not in skip_video_ids]

            print(f"    {title!r}: {len(tracks)} tracks, {len(fresh)} new")
            new_video_ids.extend(fresh)
            new_album_ids.append(album_browse_id)
            time.sleep(REQUEST_DELAY)

        return new_video_ids, new_album_ids
