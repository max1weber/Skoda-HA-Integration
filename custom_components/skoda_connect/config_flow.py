"""Config flow for the Škoda Connect integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
)

from myskoda import AuthorizationFailedError, MySkoda

from .const import (
    CONF_READ_ONLY,
    CONF_SPIN,
    DEFAULT_SCAN_INTERVAL_MINUTES,
    DOMAIN,
    MAX_SCAN_INTERVAL_MINUTES,
    MIN_SCAN_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_SPIN): str,
    }
)


async def _validate_login(hass, email: str, password: str) -> list[str]:
    """Validate credentials against the MySkoda API and return the account's VINs."""
    session = async_get_clientsession(hass)
    myskoda = MySkoda(session, mqtt_enabled=False)
    try:
        await myskoda.connect(email, password)
        vins = await myskoda.list_vehicle_vins()
    finally:
        await myskoda.disconnect()
    return vins


class SkodaConnectConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Škoda Connect."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._reauth_entry: ConfigEntry | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step, asking for MySkoda account credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            email = user_input[CONF_EMAIL]
            await self.async_set_unique_id(email.lower())
            self._abort_if_unique_id_configured()

            try:
                vins = await _validate_login(
                    self.hass, email, user_input[CONF_PASSWORD]
                )
            except AuthorizationFailedError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating Škoda Connect login")
                errors["base"] = "cannot_connect"
            else:
                if not vins:
                    errors["base"] = "no_vehicles"
                else:
                    return self.async_create_entry(
                        title=email,
                        data={
                            CONF_EMAIL: email,
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                            CONF_SPIN: user_input.get(CONF_SPIN),
                        },
                    )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_reauth(
        self, entry_data: dict[str, Any]
    ) -> ConfigFlowResult:
        """Handle reauthentication triggered by an expired/invalid session."""
        self._reauth_entry = self.hass.config_entries.async_get_entry(
            self.context["entry_id"]
        )
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask for a new password for an existing account."""
        errors: dict[str, str] = {}
        assert self._reauth_entry is not None

        if user_input is not None:
            try:
                await _validate_login(
                    self.hass,
                    self._reauth_entry.data[CONF_EMAIL],
                    user_input[CONF_PASSWORD],
                )
            except AuthorizationFailedError:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error validating Škoda Connect login")
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    self._reauth_entry,
                    data={
                        **self._reauth_entry.data,
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    },
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(CONF_PASSWORD): str}),
            errors=errors,
            description_placeholders={"email": self._reauth_entry.data[CONF_EMAIL]},
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> SkodaConnectOptionsFlow:
        """Return the options flow for this handler."""
        return SkodaConnectOptionsFlow()


class SkodaConnectOptionsFlow(OptionsFlow):
    """Handle options for an existing Škoda Connect entry."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage polling interval and read-only mode."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        current_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL_MINUTES
        )
        current_read_only = self.config_entry.options.get(CONF_READ_ONLY, False)

        schema = vol.Schema(
            {
                vol.Required(
                    CONF_SCAN_INTERVAL, default=current_interval
                ): NumberSelector(
                    NumberSelectorConfig(
                        min=MIN_SCAN_INTERVAL_MINUTES,
                        max=MAX_SCAN_INTERVAL_MINUTES,
                        mode=NumberSelectorMode.BOX,
                        unit_of_measurement="min",
                    )
                ),
                vol.Required(CONF_READ_ONLY, default=current_read_only): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
