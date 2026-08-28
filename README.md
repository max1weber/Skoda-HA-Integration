# Škoda Connect for Home Assistant

A multi-language [Home Assistant](https://www.home-assistant.io/) custom integration for
Škoda vehicles, built on the official public MySkoda API
([public.api.connect.skoda-auto.cz](https://public.api.connect.skoda-auto.cz/docs)) via the
actively maintained [`myskoda`](https://github.com/skodaconnect/myskoda) Python client.

> **Unofficial project.** This integration is not affiliated with, endorsed by, or associated
> with Škoda Auto. It uses the same public API as the official MySkoda app. Use at your own risk.

## Features

Built following Home Assistant's current integration best practices: a UI-only config flow,
a `DataUpdateCoordinator` for efficient polling, entity descriptions, per-entity translations,
an options flow, reauthentication support, and a diagnostics download.

| Platform | Entities |
|---|---|
| `sensor` | Battery level, charging power, charging rate, remaining charging time, battery/total range, fuel level, AdBlue range, mileage, outside/target temperature, software version |
| `binary_sensor` | Doors, windows, trunk, bonnet, lights, charging, charging cable plugged in |
| `lock` | Central locking (requires S-PIN) |
| `device_tracker` | Last known vehicle GPS position |
| `climate` | Remote air conditioning (on/off, ventilation, target temperature) |
| `switch` | Window heating, charging, battery care mode, reduced charging current |
| `button` | Honk & flash, flash lights, wake up vehicle |
| `number` | AC charge limit (state of charge) |

Sensors and controls are only created for the data your specific vehicle actually reports, so
the entity list automatically adapts to your car's capabilities (EV, PHEV, or combustion).

A **read-only mode** can be enabled in the integration options to disable all remote controls
(locking, climate, charging, buttons) while keeping all sensors active.

## Supported languages

The integration ships translations for its config flow, options flow, and entity names in:

- English (`en`)
- Nederlands (`nl`)
- Deutsch (`de`)
- Français (`fr`)
- Čeština (`cs`)
- Slovenčina (`sk`)

Home Assistant automatically picks the translation matching your instance's language setting,
falling back to English. Contributions for additional languages are welcome — add a new file
under `custom_components/skoda_connect/translations/`.

## Installation

### HACS (recommended)

1. In HACS, go to **Integrations** → menu (⋮) → **Custom repositories**.
2. Add this repository URL with category **Integration**.
3. Install "Škoda Connect" and restart Home Assistant.

### Manual

1. Copy `custom_components/skoda_connect` into your Home Assistant `config/custom_components/`
   directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration** and search for "Škoda Connect".
2. Enter the email address and password you use for the MySkoda app.
3. Optionally enter your S-PIN — this is required for the lock entity to work.
4. After setup, open the integration's **Configure** dialog to change the polling interval
   (1–1440 minutes, default 30) or enable read-only mode.

Credentials are stored in your Home Assistant config entry storage, the same way as most other
account-based integrations. If your session expires, Home Assistant will prompt you to
reauthenticate.

## Notes on the API

This integration deliberately depends on the community-maintained `myskoda` PyPI package rather
than re-implementing the Škoda OAuth2/REST/MQTT client from scratch, so it benefits from
upstream fixes and coverage of the public API's evolving vehicle capabilities. Data is refreshed
by polling only — MQTT push notifications from the API are not used, keeping the integration
simple and avoiding an extra point of failure.

## Disclaimer

Provided as-is, without warranty. Škoda Auto may change its API at any time, which can break
this integration. Use of the MySkoda public API is subject to Škoda's own terms of service.
