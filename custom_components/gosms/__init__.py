from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GoSmsApiClient, GoSmsError
from .const import (
    ATTR_MESSAGE,
    ATTR_RECIPIENT,
    CONF_CHANNEL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DOMAIN,
    SERVICE_SEND_SMS,
)

PLATFORMS: list[Platform] = []


SEND_SMS_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_RECIPIENT): cv.string,
        vol.Required(ATTR_MESSAGE): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GoSMS from a config entry."""
    client = GoSmsApiClient(
        session=async_get_clientsession(hass),
        client_id=entry.data[CONF_CLIENT_ID],
        client_secret=entry.data[CONF_CLIENT_SECRET],
        channel=entry.data[CONF_CHANNEL],
    )

    async def async_send_sms(call: ServiceCall) -> None:
        """Send SMS using GoSMS."""
        recipient = call.data[ATTR_RECIPIENT]
        message = call.data[ATTR_MESSAGE]

        try:
            await client.async_send_sms(recipient=recipient, message=message)
        except GoSmsError as exception:
            raise HomeAssistantError("Failed to send SMS via GoSMS.") from exception

    hass.services.async_register(
        DOMAIN,
        SERVICE_SEND_SMS,
        async_send_sms,
        schema=SEND_SMS_SCHEMA,
    )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload GoSMS config entry."""
    hass.services.async_remove(DOMAIN, SERVICE_SEND_SMS)
    return True