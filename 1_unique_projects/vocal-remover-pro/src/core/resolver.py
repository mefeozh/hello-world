"""
VocalRemover Pro - Music Discovery Resolver

Pipeline:
  1. Detect input type (Spotify URL, YouTube URL, plain text)
  2. Direct Song Search (iTunes entity=song / Deezer track search) -> Instant Spotify-style track results
  3. Artist Discovery & Disambiguation (iTunes + Deezer)
  4. Full Album Explorer & Tracklist Fetcher (supports up to 200 albums, deduplication, & Deezer fallback)
"""
import re
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.config import (
    ITUNES_SEARCH_URL, ITUNES_LOOKUP_URL,
    DEEZER_SEARCH_URL, DEEZER_TOP_URL,
    COMMON_HEADERS,
)
from src.utils.normalizer import normalize_artist_name

logger = logging.getLogger("resolver")

# ─── Robust Request Session with Retries ──────────────────────────────────────
session = requests.Session()
retries = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
session.mount("http://", HTTPAdapter(max_retries=retries))
session.mount("https://", HTTPAdapter(max_retries=retries))


# ─── Input Type Detection ──────────────────────────────────────────────────────

def detect_input_type(user_input: str) -> str:
    """Return 'spotify', 'spotify_playlist', 'youtube', 'youtube_playlist', or 'text'."""
    s = user_input.strip().lower()
    if "spotify.com" in s:
        if "/playlist/" in s:
            return "spotify_playlist"
        return "spotify"
    if "youtube.com" in s or "youtu.be" in s:
        if "list=" in s:
            return "youtube_playlist"
        return "youtube"
    return "text"


# ─── Spotify oEmbed (no auth) ─────────────────────────────────────────────────

def resolve_spotify_url(url: str) -> dict | None:
    """Use Spotify's public oEmbed endpoint to extract track/artist metadata."""
    try:
        r = session.get(
            "https://open.spotify.com/oembed",
            params={"url": url},
            headers=COMMON_HEADERS,
            timeout=8,
        )
        if r.status_code == 200:
            data = r.json()
            raw_title = data.get("title", "")
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                title  = parts[0].strip()
                artist = normalize_artist_name(parts[1].strip())
            else:
                title  = raw_title
                artist = normalize_artist_name(data.get("provider_name", ""))
            return {
                "type":        "track",
                "artist":      artist,
                "title":       title,
                "full_title":  f"{artist} - {title}",
                "artwork_url": data.get("thumbnail_url"),
                "query":       f"{artist} - {title}",
            }
    except requests.RequestException as exc:
        logger.warning("Spotify oEmbed failed: %s", exc)
    return None

def resolve_spotify_playlist(url: str) -> dict | None:
    """Extract playlist metadata and resolve track titles & artists via Web API anonymous token."""
    playlist_id_match = re.search(r'playlist/([a-zA-Z0-9]+)', url)
    if not playlist_id_match:
        return None
    playlist_id = playlist_id_match.group(1)
    
    try:
        r_token = session.get("https://open.spotify.com/get_access_token?reason=transport&productType=web_player", headers=COMMON_HEADERS, timeout=8)
        if r_token.status_code == 200:
            token = r_token.json().get("accessToken")
            headers = COMMON_HEADERS.copy()
            headers["Authorization"] = f"Bearer {token}"
            
            r_api = session.get(f"https://api.spotify.com/v1/playlists/{playlist_id}", headers=headers, timeout=10)
            if r_api.status_code == 200:
                data = r_api.json()
                playlist_title = data.get("name", "Spotify Playlist")
                tracks = []
                for idx, item in enumerate(data.get("tracks", {}).get("items", []), 1):
                    track_obj = item.get("track")
                    if not track_obj:
                        continue
                    artist_name = track_obj.get("artists", [{}])[0].get("name", "Unknown Artist")
                    artist_name = normalize_artist_name(artist_name)
                    title = track_obj.get("name", "Unknown Track")
                    duration_ms = track_obj.get("duration_ms", 0)
                    images = track_obj.get("album", {}).get("images", [])
                    art_url = images[0].get("url") if images else None
                    
                    tracks.append({
                        "artist": artist_name,
                        "title": title,
                        "full_title": f"{artist_name} - {title}",
                        "track_num": idx,
                        "duration": _ms_to_str(duration_ms),
                        "artwork_url": art_url,
                        "query": f"{artist_name} - {title}"
                    })
                return {
                    "type": "spotify_playlist",
                    "playlist_title": playlist_title,
                    "tracks": tracks
                }
    except Exception as exc:
        logger.warning("Spotify playlist extraction failed: %s", exc)
    return None



# ─── YouTube direct URL ────────────────────────────────────────────────────────

def resolve_youtube_url(url: str) -> dict:
    """Wrap a YouTube URL as a direct download track dict."""
    return {
        "type":   "youtube_direct",
        "artist": "YouTube Import",
        "title":  "Direct YouTube Audio",
        "full_title": url,
        "query":  url,
    }

def resolve_youtube_playlist(url: str) -> dict | None:
    """Resolve YouTube Playlist entries using yt_dlp flat extraction."""
    import yt_dlp
    ydl_opts = {
        'extract_flat': True,
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                return None
            
            playlist_title = info.get("title", "YouTube Playlist")
            entries = info.get("entries", [])
            tracks = []
            for idx, entry in enumerate(entries, 1):
                if entry:
                    title = entry.get("title", "Unknown")
                    uploader = entry.get("uploader", "Unknown Artist")
                    tracks.append({
                        "artist": normalize_artist_name(uploader),
                        "title": title,
                        "full_title": f"{uploader} - {title}",
                        "track_num": idx,
                        "duration": _ms_to_str(entry.get("duration", 0) * 1000) if entry.get("duration") else "N/A",
                        "artwork_url": entry.get("thumbnail") if entry.get("thumbnail") else None,
                        "query": entry.get("url") or f"https://www.youtube.com/watch?v={entry.get('id')}",
                    })
            return {
                "type": "youtube_playlist",
                "playlist_title": playlist_title,
                "tracks": tracks
            }
    except Exception as exc:
        logger.warning("YouTube playlist extraction failed: %s", exc)
    return None


# ─── Direct Song Search (Spotify-style Search Results) ─────────────────────────

def search_songs(query: str, limit: int = 10) -> list[dict]:
    """Search for songs directly like Spotify/Apple Music."""
    if not query or len(query.strip()) < 2:
        return []
        
    try:
        r = session.get(
            ITUNES_SEARCH_URL,
            params={"term": query.strip(), "entity": "song", "limit": limit},
            headers=COMMON_HEADERS,
            timeout=8,
        )
        if r.status_code == 200:
            results = r.json().get("results", [])
            tracks = []
            for item in results:
                try:
                    if item.get("wrapperType") == "track":
                        artist = normalize_artist_name(item.get("artistName", "Unknown Artist"))
                        title  = item.get("trackName", "Unknown Track")
                        tracks.append({
                            "artist":      artist,
                            "title":       title,
                            "full_title":  f"{artist} - {title}",
                            "duration":    _ms_to_str(item.get("trackTimeMillis")),
                            "artwork_url": _hd_artwork(item.get("artworkUrl100")),
                            "source":      "itunes",
                        })
                except (KeyError, TypeError, ValueError):
                    continue
            if tracks:
                return tracks
    except requests.RequestException as exc:
        logger.warning("iTunes song search failed: %s", exc)

    try:
        r = session.get(
            "https://api.deezer.com/search",
            params={"q": query.strip(), "limit": limit},
            headers=COMMON_HEADERS,
            timeout=8,
        )
        if r.status_code == 200:
            items = r.json().get("data", [])
            tracks = []
            for item in items:
                try:
                    artist = normalize_artist_name(item.get("artist", {}).get("name", "Unknown Artist"))
                    title  = item.get("title", "Unknown Track")
                    tracks.append({
                        "artist":      artist,
                        "title":       title,
                        "full_title":  f"{artist} - {title}",
                        "duration":    _ms_to_str(item.get("duration", 0) * 1000),
                        "artwork_url": item.get("album", {}).get("cover_medium"),
                        "source":      "deezer",
                    })
                except (KeyError, TypeError, ValueError):
                    continue
            return tracks
    except requests.RequestException as exc:
        logger.warning("Deezer song search failed: %s", exc)

    return []


# ─── iTunes & Deezer Artist Search (Disambiguation) ───────────────────────────

def search_artists_itunes(query: str, limit: int = 10) -> list[dict]:
    """Fuzzy-search for artists on iTunes."""
    try:
        r = session.get(
            ITUNES_SEARCH_URL,
            params={"term": query, "entity": "musicArtist", "limit": limit},
            headers=COMMON_HEADERS,
            timeout=8,
        )
        if r.status_code == 200:
            results = r.json().get("results", [])
            artists = []
            for item in results:
                try:
                    if item.get("wrapperType") == "artist":
                        name = normalize_artist_name(item.get("artistName", ""))
                        genre = item.get("primaryGenreName", "Music")
                        artists.append({
                            "itunes_id": item["artistId"],
                            "name":      name,
                            "display":   f"{name} ({genre})",
                            "genre":     genre,
                            "art_url":   None,
                            "source":    "itunes",
                        })
                except (KeyError, TypeError, ValueError):
                    continue
            return artists
    except requests.RequestException as exc:
        logger.warning("iTunes artist search failed: %s", exc)
    return []


def search_artists_deezer(query: str, limit: int = 10) -> list[dict]:
    """Fuzzy-search for artists on Deezer."""
    try:
        r = session.get(
            DEEZER_SEARCH_URL,
            params={"q": query},
            headers=COMMON_HEADERS,
            timeout=8,
        )
        if r.status_code == 200:
            items = r.json().get("data", [])[:limit]
            artists = []
            for item in items:
                try:
                    name = normalize_artist_name(item.get("name", ""))
                    artists.append({
                        "deezer_id": item["id"],
                        "name":      name,
                        "display":   f"{name} [Deezer]",
                        "genre":     "Artist",
                        "art_url":   item.get("picture_medium"),
                        "source":    "deezer",
                    })
                except (KeyError, TypeError, ValueError):
                    continue
            return artists
    except requests.RequestException as exc:
        logger.warning("Deezer artist search failed: %s", exc)
    return []


def search_artists(query: str, limit: int = 10) -> list[dict]:
    results = search_artists_itunes(query, limit)
    deezer_res = search_artists_deezer(query, limit)
    
    seen = set()
    combined = []
    for a in results + deezer_res:
        k = a["name"].lower()
        if k not in seen:
            seen.add(k)
            combined.append(a)
            
    return combined[:limit]


# ─── Comprehensive Album Explorer & Tracklist Fetcher ───────────────────────

def get_artist_albums(artist: dict, limit: int = 200) -> list[dict]:
    """Fetch ALL official studio albums and singles for an artist."""
    albums = []
    seen_titles = set()

    artist_id = artist.get("itunes_id")
    if artist_id:
        try:
            r = session.get(
                ITUNES_LOOKUP_URL,
                params={"id": artist_id, "entity": "album", "limit": limit},
                headers=COMMON_HEADERS,
                timeout=10,
            )
            if r.status_code == 200:
                items = r.json().get("results", [])
                for item in items:
                    try:
                        if item.get("wrapperType") == "collection":
                            alb_name = item.get("collectionName", "").strip()
                            norm_title = re.sub(r'[\(\[\{].*?[\)\]\}]', '', alb_name).strip().lower()
                            if norm_title not in seen_titles:
                                seen_titles.add(norm_title)
                                rel_year = item.get("releaseDate", "")[:4]
                                albums.append({
                                    "album_id":     item.get("collectionId"),
                                    "album_name":   alb_name,
                                    "artist_name":  normalize_artist_name(item.get("artistName", artist.get("name", ""))),
                                    "release_year": rel_year if rel_year else "N/A",
                                    "track_count":  item.get("trackCount", 0),
                                    "artwork_url":  _hd_artwork(item.get("artworkUrl100")),
                                    "genre":        item.get("primaryGenreName", ""),
                                    "source":       "itunes",
                                })
                    except (KeyError, TypeError, ValueError):
                        continue
        except requests.RequestException as exc:
            logger.warning("iTunes full album fetch failed: %s", exc)

    deezer_id = artist.get("deezer_id")
    if len(albums) < 3 and deezer_id:
        try:
            r = session.get(
                f"https://api.deezer.com/artist/{deezer_id}/albums",
                params={"limit": 100},
                headers=COMMON_HEADERS,
                timeout=10,
            )
            if r.status_code == 200:
                items = r.json().get("data", [])
                for item in items:
                    try:
                        alb_name = item.get("title", "").strip()
                        norm_title = re.sub(r'[\(\[\{].*?[\)\]\}]', '', alb_name).strip().lower()
                        if norm_title not in seen_titles:
                            seen_titles.add(norm_title)
                            rel_year = item.get("release_date", "")[:4]
                            albums.append({
                                "album_id":     item.get("id"),
                                "album_name":   alb_name,
                                "artist_name":  artist.get("name", ""),
                                "release_year": rel_year if rel_year else "N/A",
                                "track_count":  item.get("nb_tracks", 0),
                                "artwork_url":  item.get("cover_medium"),
                                "genre":        "Album",
                                "source":       "deezer",
                            })
                    except (KeyError, TypeError, ValueError):
                        continue
        except requests.RequestException as exc:
            logger.warning("Deezer album fetch failed: %s", exc)

    return sorted(albums, key=lambda x: x["release_year"], reverse=True)


def get_album_tracks(album: dict, artist_name: str) -> list[dict]:
    """Fetch all tracks for an album."""
    album_id = album.get("album_id")
    source   = album.get("source", "itunes")
    
    if not album_id:
        return []
        
    if source == "itunes":
        try:
            r = session.get(
                ITUNES_LOOKUP_URL,
                params={"id": album_id, "entity": "song"},
                headers=COMMON_HEADERS,
                timeout=10,
            )
            if r.status_code == 200:
                items = r.json().get("results", [])
                tracks = []
                for item in items:
                    try:
                        if item.get("wrapperType") == "track":
                            artist = normalize_artist_name(item.get("artistName", artist_name))
                            title  = item.get("trackName", "Unknown Track")
                            tracks.append({
                                "artist":       artist,
                                "title":        title,
                                "full_title":   f"{artist} - {title}",
                                "track_num":    item.get("trackNumber", 0),
                                "duration":     _ms_to_str(item.get("trackTimeMillis")),
                                "artwork_url":  _hd_artwork(item.get("artworkUrl100")),
                                "album_name":   item.get("collectionName", ""),
                            })
                    except (KeyError, TypeError, ValueError):
                        continue
                return tracks
        except requests.RequestException as exc:
            logger.warning("iTunes album tracks failed: %s", exc)

    elif source == "deezer":
        try:
            r = session.get(
                f"https://api.deezer.com/album/{album_id}/tracks",
                headers=COMMON_HEADERS,
                timeout=10,
            )
            if r.status_code == 200:
                items = r.json().get("data", [])
                tracks = []
                for idx, item in enumerate(items, 1):
                    try:
                        artist = normalize_artist_name(item.get("artist", {}).get("name", artist_name))
                        title  = item.get("title", "Unknown Track")
                        tracks.append({
                            "artist":       artist,
                            "title":        title,
                            "full_title":   f"{artist} - {title}",
                            "track_num":    idx,
                            "duration":     _ms_to_str(item.get("duration", 0) * 1000),
                            "artwork_url":  album.get("artwork_url"),
                            "album_name":   album.get("album_name", ""),
                        })
                    except (KeyError, TypeError, ValueError):
                        continue
                return tracks
        except requests.RequestException as exc:
            logger.warning("Deezer album tracks failed: %s", exc)

    return []


# ─── Top Tracks Fetch ─────────────────────────────────────────────────────────

def get_top_tracks_itunes(artist: dict, limit: int = 25) -> list[dict]:
    artist_id = artist.get("itunes_id")
    if not artist_id:
        return []
    try:
        r = session.get(
            ITUNES_LOOKUP_URL,
            params={"id": artist_id, "entity": "song", "limit": limit + 5},
            headers=COMMON_HEADERS,
            timeout=10,
        )
        if r.status_code == 200:
            items = r.json().get("results", [])
            tracks = []
            for item in items:
                try:
                    if item.get("wrapperType") == "track":
                        artist_name = normalize_artist_name(item.get("artistName", artist["name"]))
                        title       = item.get("trackName", "Unknown")
                        tracks.append({
                            "artist":      artist_name,
                            "title":       title,
                            "full_title":  f"{artist_name} - {title}",
                            "duration":    _ms_to_str(item.get("trackTimeMillis")),
                            "artwork_url": _hd_artwork(item.get("artworkUrl100")),
                            "genre":       item.get("primaryGenreName", ""),
                            "source":      "itunes",
                        })
                except (KeyError, TypeError, ValueError):
                    continue
            return tracks[:limit]
    except requests.RequestException as exc:
        logger.warning("iTunes top tracks failed: %s", exc)
    return []


def get_top_tracks_deezer(artist: dict, limit: int = 25) -> list[dict]:
    artist_id = artist.get("deezer_id")
    if not artist_id:
        return []
    try:
        r = session.get(
            DEEZER_TOP_URL.format(artist_id=artist_id),
            params={"limit": limit},
            headers=COMMON_HEADERS,
            timeout=10,
        )
        if r.status_code == 200:
            items = r.json().get("data", [])
            tracks = []
            for item in items:
                try:
                    artist_name = normalize_artist_name(
                        item.get("artist", {}).get("name", artist["name"])
                    )
                    title = item.get("title", "Unknown")
                    tracks.append({
                        "artist":      artist_name,
                        "title":       title,
                        "full_title":  f"{artist_name} - {title}",
                        "duration":    _ms_to_str(item.get("duration", 0) * 1000),
                        "artwork_url": item.get("album", {}).get("cover_medium"),
                        "genre":       "",
                        "source":      "deezer",
                    })
                except (KeyError, TypeError, ValueError):
                    continue
            return tracks
    except requests.RequestException as exc:
        logger.warning("Deezer top tracks failed: %s", exc)
    return []


def get_top_tracks(artist: dict, limit: int = 25) -> list[dict]:
    if artist.get("source") == "itunes":
        tracks = get_top_tracks_itunes(artist, limit)
        if tracks:
            return tracks
    if artist.get("source") == "deezer" or not artist.get("itunes_id"):
        return get_top_tracks_deezer(artist, limit)
    return get_top_tracks_itunes(artist, limit) or get_top_tracks_deezer(artist, limit)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _hd_artwork(url: str) -> str | None:
    """Upgrade iTunes 100x100 artwork URL to high-res 600x600."""
    if not url:
        return None
    return url.replace("100x100bb", "600x600bb")


def _ms_to_str(ms) -> str:
    if not ms:
        return "N/A"
    total_sec = int(ms) // 1000
    return f"{total_sec // 60}:{total_sec % 60:02d}"
