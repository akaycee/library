"""Location-name normalization and validation.

Deliberately broader than usernames: location names may contain spaces (e.g.,
"Main Room", "Shelf A-2"). Do NOT reuse the username validator here.
"""

from __future__ import annotations

import re
import unicodedata

# Letters, digits, spaces, and . _ -  (Unicode word chars via \w include letters,
# digits, and underscore).
_ALLOWED_RE = re.compile(r"^[\w .\-]+$", re.UNICODE)
_MAX_LEN = 100


class LocationNameError(ValueError):
    """Raised when a location name fails validation."""


def _collapse_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())


def validate_location_name(raw: str) -> tuple[str, str]:
    """Return (display, normalized).

    - display: trimmed, NFKC-normalized, repeated spaces collapsed (case preserved)
    - normalized: case-folded display, used for sibling-uniqueness checks
    """
    if raw is None:
        raise LocationNameError("name required")
    display = _collapse_spaces(unicodedata.normalize("NFKC", raw))
    if not display:
        raise LocationNameError("name must not be empty")
    if len(display) > _MAX_LEN:
        raise LocationNameError(f"name must be at most {_MAX_LEN} characters")
    if not _ALLOWED_RE.match(display):
        raise LocationNameError("name may only contain letters, digits, spaces, and . _ -")
    return display, display.casefold()
