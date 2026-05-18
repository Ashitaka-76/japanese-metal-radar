import json
import time
from ytmusicapi import YTMusic

CHUNK_SIZE = 50
REQUEST_DELAY = 0.4  # seconds between album fetches to avoid rate limiting


class YTMusicClient:
    def __init__(self, auth_file: str = "browser.json"):
        self.yt = YTMusic(auth_file)
        self._patch_session(auth_file)

    # Header che non devono mai essere riusati tra richieste diverse:
    # content-length varia per ogni body, sec-* sono solo per il browser.
    _STRIP_HEADERS = {
        "content-length",
        "content-type",
        "accept-encoding",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "sec-fetch-site",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
        "te",
        "referer",
        "connection",
    }

    def _patch_session(self, auth_file: str) -> None:
        """
        ytmusicapi 1.7.x passa tutti gli header di browser.json per ogni
        richiesta (via _input_dict / base_headers). Se il browser.json
        contiene content-length dell'originale, YouTube risponde 400 perché
        il nuovo body ha dimensione diversa. Rimuoviamo gli header problematici.
        """
        input_dict = getattr(self.yt, "_input_dict", None)
        if input_dict is None:
            return

        stripped = []
        for h in self._STRIP_HEADERS:
            if input_dict.pop(h, None) is not None:
                stripped.append(h)

        if stripped:
            # Invalida la cache degli header già formati
            self.yt._headers = None
            self.yt._base_headers = None

    # ------------------------------------------------------------------
    # Artist lookup
    # ------------------------------------------------------------------

    def find_artist_browse_id(self, artist_name: str) -> str | None:
        results = self.yt.search(artist_name, filter="artists", limit=10)
        name_lower = artist_name.lower()

        # Prefer an exact-ish name match
        for r in results:
            candidate = (r.get("artist") or r.get("title") or "").lower()
            if name_lower == candidate or name_lower in candidate or candidate in name_lower:
                return r["browseId"]

        # Fall back to the first artist result
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

            # Try to load the full list if "see all" params exist
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
        playlist_id = self.yt.create_playlist(title, description)
        return playlist_id

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
        deduped = list(dict.fromkeys(video_ids))  # preserve order, remove dupes
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
    # Helper to fetch all tracks for a list of releases
    # ------------------------------------------------------------------

    def collect_tracks(
        self,
        releases: list[dict],
        skip_album_ids: set[str],
        skip_video_ids: set[str],
    ) -> tuple[list[str], list[str]]:
        """
        Returns (new_video_ids, new_album_browse_ids) for releases not in skip sets.
        """
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
