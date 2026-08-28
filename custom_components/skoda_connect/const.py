"""Constants for the Škoda Connect integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "skoda_connect"

CONF_SPIN: Final = "spin"
CONF_READ_ONLY: Final = "read_only"

DEFAULT_SCAN_INTERVAL_MINUTES: Final = 30
MIN_SCAN_INTERVAL_MINUTES: Final = 1
MAX_SCAN_INTERVAL_MINUTES: Final = 1440

MANUFACTURER: Final = "Škoda"
