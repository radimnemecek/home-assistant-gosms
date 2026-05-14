from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GoSmsApiClient, GoSmsAuthError, GoSmsError
from .const import (
    CONF_BALANCE_UPDATE_INTERVAL_MINUTES,
    CONF_CHANNEL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DEFAULT_BALANCE_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_BALANCE_UPDATE_INTERVAL_MINUTES,
    MIN_BALANCE_UPDATE_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class GoSmsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GoSMS."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Return the options flow for this config entry."""
        return GoSmsOptionsFlowHandler(config_entry)

    async def _async_validate_credentials(self, user_input: dict[str, Any]) -> str | None:
        """Validate GoSMS credentials and return an error key when invalid."""
        client = GoSmsApiClient(
            session=async_get_clientsession(self.hass),
            client_id=user_input[CONF_CLIENT_ID],
            client_secret=user_input[CONF_CLIENT_SECRET],
            channel=user_input[CONF_CHANNEL],
        )

        try:
            await client.async_get_access_token()
        except GoSmsAuthError:
            return "auth"
        except GoSmsError:
            return "cannot_connect"
        except Exception:
            _LOGGER.exception("Unexpected error while validating GoSMS credentials")
            return "unknown"

        return None

    @staticmethod
    def _build_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
        """Build a schema for credential input."""
        defaults = defaults or {}
        channel_default = defaults.get(CONF_CHANNEL, vol.UNDEFINED)

        channel_field: vol.Marker
        if channel_default is vol.UNDEFINED:
            channel_field = vol.Required(CONF_CHANNEL)
        else:
            channel_field = vol.Required(CONF_CHANNEL, default=channel_default)

        return vol.Schema(
            {
                vol.Required(CONF_CLIENT_ID, default=defaults.get(CONF_CLIENT_ID, "")): str,
                vol.Required(
                    CONF_CLIENT_SECRET,
                    default=defaults.get(CONF_CLIENT_SECRET, ""),
                ): str,
                channel_field: vol.All(vol.Coerce(int), vol.Range(min=1)),
            }
        )

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            if error_key := await self._async_validate_credentials(user_input):
                errors["base"] = error_key
            else:
                await self.async_set_unique_id(str(user_input[CONF_CHANNEL]))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"GoSMS channel {user_input[CONF_CHANNEL]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._build_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle reconfiguration of an existing entry."""
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        if user_input is not None:
            if error_key := await self._async_validate_credentials(user_input):
                errors["base"] = error_key
            else:
                for configured_entry in self._async_current_entries():
                    if (
                        configured_entry.entry_id != entry.entry_id
                        and configured_entry.data.get(CONF_CHANNEL) == user_input[CONF_CHANNEL]
                    ):
                        errors["base"] = "already_configured"
                        break

                if not errors:
                    return self.async_update_reload_and_abort(
                        entry,
                        data_updates=user_input,
                    )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._build_schema(entry.data),
            errors=errors,
        )


class GoSmsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle GoSMS options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage GoSMS options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_value = self._config_entry.options.get(
            CONF_BALANCE_UPDATE_INTERVAL_MINUTES,
            DEFAULT_BALANCE_UPDATE_INTERVAL_MINUTES,
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BALANCE_UPDATE_INTERVAL_MINUTES,
                        default=current_value,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(
                            min=MIN_BALANCE_UPDATE_INTERVAL_MINUTES,
                            max=MAX_BALANCE_UPDATE_INTERVAL_MINUTES,
                        ),
                    ),
                }
            ),
        )
