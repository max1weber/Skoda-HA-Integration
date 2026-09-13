"""Constants for the Škoda Connect integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "skoda_connect"

CONF_SPIN: Final = "spin"
CONF_READ_ONLY: Final = "read_only"

# Each poll fetches ~10-13 separate endpoints per vehicle (info, maintenance, and one
# request per reported capability), and the public API enforces a strict per-account
# request quota. MIN_SCAN_INTERVAL_MINUTES is a hard floor so the options flow can't be
# set to a value that all but guarantees rate limiting - see the "Notes on the API"
# section in the README before lowering it further.
DEFAULT_SCAN_INTERVAL_MINUTES: Final = 15
MIN_SCAN_INTERVAL_MINUTES: Final = 15
MAX_SCAN_INTERVAL_MINUTES: Final = 1440

MANUFACTURER: Final = "Škoda"
