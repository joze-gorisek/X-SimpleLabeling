"""Derive default labels from image filenames.

Images follow the naming schema
``<plant>_<field>_<days since sowing>_<nnn>_rgb.png``, e.g.
``Maize_F12_21_003_rgb.png``. The lowercase ``<plant>`` is used as the
default label for new polygons, with diacritics ("šumniki") replaced by
plain letters (š -> s, č -> c, ž -> z, ć -> c, đ -> d).
"""

import os.path as osp
import re
import unicodedata
from typing import Optional

# Letters that don't decompose into base letter + combining mark.
_EXTRA_ASCII = str.maketrans({"đ": "d", "Đ": "D"})


def strip_diacritics(text: str) -> str:
    """Replace accented letters with their plain counterparts."""
    decomposed = unicodedata.normalize("NFD", text.translate(_EXTRA_ASCII))
    return "".join(c for c in decomposed if not unicodedata.combining(c))

_IMAGE_NAME_PATTERN = re.compile(
    r"^(?P<plant>[^_]+)_(?P<field>.+)_(?P<days>\d+)_(?P<nnn>\d+)_rgb\.png$",
    re.IGNORECASE,
)


def plant_label_from_filename(filename: Optional[str]) -> Optional[str]:
    """Return the lowercase plant name, or None if the name doesn't match."""
    if not filename:
        return None
    # Filenames from macOS can arrive decomposed (NFD); normalize first.
    basename = unicodedata.normalize("NFC", osp.basename(filename))
    match = _IMAGE_NAME_PATTERN.match(basename)
    if not match:
        return None
    return strip_diacritics(match.group("plant")).lower()
