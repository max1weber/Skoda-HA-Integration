"""Constants for the Škoda Connect integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "skoda_connect"

CONF_SPIN: Final = "spin"
CONF_READ_ONLY: Final = "read_only"

# Each poll fetches ~10-13 separate endpoints per vehicle (info, maintenance, and one
# request per reported capability), and the public API enforces a strict per-account
# request quota. These defaults are set conservatively to avoid triggering rate
# limiting (or worse, an account lockout) - see the "Notes on the API" section in the
# README before lowering them.
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 60
MIN_SCAN_INTERVAL_MINUTES: Final = 15
MAX_SCAN_INTERVAL_MINUTES: Final = 1440

MANUFACTURER: Final = "Škoda"
