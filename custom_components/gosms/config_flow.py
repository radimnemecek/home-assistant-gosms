from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GoSmsApiClient, GoSmsAuthError, GoSmsError
from .const import CONF_CHANNEL, CONF_CLIENT_ID, CONF_CLIENT_SECRET, DOMAIN


class GoSmsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GoSMS."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = GoSmsApiClient(
                session=async_get_clientsession(self.hass),
                client_id=user_input[CONF_CLIENT_ID],
                client_secret=user_input[CONF_CLIENT_SECRET],
                channel=user_input[CONF_CHANNEL],
            )

            try:
                await client.async_get_access_token()
            except GoSmsAuthError:
                errors["base"] = "auth"
            except GoSmsError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(str(user_input[CONF_CHANNEL]))
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"GoSMS channel {user_input[CONF_CHANNEL]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CLIENT_ID): str,
                    vol.Required(CONF_CLIENT_SECRET): str,
                    vol.Required(CONF_CHANNEL): int,
                }
            ),
            errors=errors,
        )