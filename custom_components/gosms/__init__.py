from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GoSmsApiClient, GoSmsError
from .coordinator import GoSmsDataUpdateCoordinator
from .const import (
    ATTR_MESSAGE,
    ATTR_RECIPIENT,
    ATTR_RECIPIENTS,
    CONF_CHANNEL,
    CONF_CLIENT_ID,
    CONF_CLIENT_SECRET,
    DATA_CLIENT,
    DATA_COORDINATOR,
    DOMAIN,
    SERVICE_PREVIEW_SMS,
    SERVICE_SEND_SMS,
)

PLATFORMS: list[Platform] = [Platform.SENSOR]


SEND_SMS_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_RECIPIENT): cv.string,
        vol.Optional(ATTR_RECIPIENTS): vol.Any(cv.string, [cv.string]),
        vol.Required(ATTR_MESSAGE): cv.string,
    }
)


def _parse_recipients_from_text(value: str) -> list[str]:
    """Parse recipients from comma/newline separated text."""
    return [
        item.strip()
        for raw_line in value.splitlines()
        for item in raw_line.split(",")
        if item.strip()
    ]


def _normalize_recipients(
    recipient: str | None,
    recipients: str | list[str] | None,
) -> list[str]:
    """Build a normalized recipients list from service data."""
    normalized: list[str] = []

    # Keep backward compatibility: when both are provided, combine both inputs.
    if recipient is not None:
        single = recipient.strip()
        if single:
            normalized.append(single)

    if recipients is not None:
        if isinstance(recipients, str):
            normalized.extend(_parse_recipients_from_text(recipients))
        else:
            normalized.extend(item.strip() for item in recipients if item.strip())

    deduped: list[str] = []
    for phone in normalized:
        if phone not in deduped:
            deduped.append(phone)

    return deduped


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up GoSMS from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    client = GoSmsApiClient(
        session=async_get_clientsession(hass),
        client_id=entry.data[CONF_CLIENT_ID],
        client_secret=entry.data[CONF_CLIENT_SECRET],
        channel=entry.data[CONF_CHANNEL],
    )
    coordinator = GoSmsDataUpdateCoordinator(hass, client)

    hass.data[DOMAIN][entry.entry_id] = {
        DATA_CLIENT: client,
        DATA_COORDINATOR: coordinator,
    }

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_SMS):

        async def async_send_sms(call: ServiceCall) -> None:
            """Send SMS using GoSMS."""
            recipient = call.data.get(ATTR_RECIPIENT)
            recipients = call.data.get(ATTR_RECIPIENTS)
            message = call.data[ATTR_MESSAGE]

            normalized_recipients = _normalize_recipients(recipient, recipients)
            if not normalized_recipients:
                raise HomeAssistantError(
                    "Either recipient or recipients must contain at least one phone number."
                )

            domain_data = hass.data.get(DOMAIN, {})
            if not domain_data:
                raise HomeAssistantError("GoSMS integration is not loaded.")

            first_entry_data = next(iter(domain_data.values()))
            active_client: GoSmsApiClient = first_entry_data[DATA_CLIENT]

            try:
                await active_client.async_send_sms(
                    recipients=normalized_recipients,
                    message=message,
                )
            except GoSmsError as exception:
                raise HomeAssistantError("Failed to send SMS via GoSMS.") from exception

        hass.services.async_register(
            DOMAIN,
            SERVICE_SEND_SMS,
            async_send_sms,
            schema=SEND_SMS_SCHEMA,
        )

    if not hass.services.has_service(DOMAIN, SERVICE_PREVIEW_SMS):

        async def async_preview_sms(call: ServiceCall) -> dict[str, object | None]:
            """Preview SMS details without sending the message."""
            recipient = call.data.get(ATTR_RECIPIENT)
            recipients = call.data.get(ATTR_RECIPIENTS)
            message = call.data[ATTR_MESSAGE]

            normalized_recipients = _normalize_recipients(recipient, recipients)
            if not normalized_recipients:
                raise HomeAssistantError(
                    "Either recipient or recipients must contain at least one phone number."
                )

            domain_data = hass.data.get(DOMAIN, {})
            if not domain_data:
                raise HomeAssistantError("GoSMS integration is not loaded.")

            first_entry_data = next(iter(domain_data.values()))
            active_client: GoSmsApiClient = first_entry_data[DATA_CLIENT]

            try:
                return await active_client.async_preview_sms(
                    recipients=normalized_recipients,
                    message=message,
                )
            except GoSmsError as exception:
                raise HomeAssistantError("Failed to preview SMS via GoSMS.") from exception

        hass.services.async_register(
            DOMAIN,
            SERVICE_PREVIEW_SMS,
            async_preview_sms,
            schema=SEND_SMS_SCHEMA,
            supports_response=SupportsResponse.ONLY,
        )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    hass.async_create_task(coordinator.async_refresh())

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload GoSMS config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
            hass.services.async_remove(DOMAIN, SERVICE_SEND_SMS)
            hass.services.async_remove(DOMAIN, SERVICE_PREVIEW_SMS)

    return unload_ok
