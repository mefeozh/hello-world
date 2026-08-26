"""
VocalRemover Pro - Artist & Filename Normalization Utilities
"""
import re
import os

# Markers that indicate a featured / secondary artist
_FEAT_PATTERN = re.compile(
    r'\s*[\(\[]?\s*(?:ft\.?|feat\.?|featuring|with|vs\.?|x)\s+.+[\)\]]?\s*$',
    re.IGNORECASE
)
_STRIP_CHARS = re.compile(r'[^\w\s\.\-]')   # keep alphanum, space, dot, hyphen
_MULTI_SPACE  = re.compile(r'\s{2,}')


def normalize_artist_name(raw: str) -> str:
    """Strip featured markers, unicode quotes, and illegal path chars.
    Returns a clean Title-Cased primary artist name.

    Examples:
        "Lil Uzi Vert feat. Playboi Carti" → "Lil Uzi Vert"
        "TRAVIS SCOTT" → "Travis Scott"
        "billie eilish" → "Billie Eilish"
    """
    if not raw:
        return "Unknown Artist"
    s = str(raw)
    # Normalize unicode quotes
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u201c", '"').replace("\u201d", '"')
    # Remove featured artist suffixes
    s = _FEAT_PATTERN.sub('', s).strip()
    # Also split on comma / ampersand — keep only first artist
    s = re.split(r'\s*[,&]\s*', s, maxsplit=1)[0].strip()
    # Strip illegal filesystem characters
    s = _STRIP_CHARS.sub('', s)
    s = _MULTI_SPACE.sub(' ', s).strip()
    # Normalize case
    if s.isupper() or s.islower():
        s = s.title()
    return s if s else "Unknown Artist"


def sanitize_filename(name: str) -> str:
    """Convert a string into a safe filename (no path separators or illegal chars)."""
    if not name:
        return "audio"
    s = re.sub(r'[<>:"/\\|?*]', '', str(name))
    s = _MULTI_SPACE.sub(' ', s).strip()
    return s[:200] if s else "audio"   # cap at 200 chars


def artist_library_paths(library_base: str, artist_name: str) -> dict:
    """Return and create the 4-tier folder structure for one artist."""
    safe = normalize_artist_name(artist_name)
    base = os.path.join(library_base, safe)
    paths = {
        "artist":          base,
        "downloaded":      os.path.join(base, "1_Downloaded"),
        "raw_vocal":       os.path.join(base, "2_Raw_Vocal"),
        "dereverbed":      os.path.join(base, "3_DeReverbed"),
        "final_acapella":  os.path.join(base, "4_Final_Acapella"),
    }
    for p in paths.values():
        os.makedirs(p, exist_ok=True)
    return paths
