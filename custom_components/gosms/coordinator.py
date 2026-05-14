from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GoSmsApiClient, GoSmsError
from .const import (
    DEFAULT_BALANCE_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
    MAX_BALANCE_UPDATE_INTERVAL_MINUTES,
    MIN_BALANCE_UPDATE_INTERVAL_MINUTES,
)

_LOGGER = logging.getLogger(__name__)


class GoSmsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for GoSMS account-level data."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: GoSmsApiClient,
        update_interval_minutes: int,
    ) -> None:
        """Initialize coordinator."""
        self.client = client
        try:
            parsed_interval = int(update_interval_minutes)
        except (TypeError, ValueError):
            parsed_interval = DEFAULT_BALANCE_UPDATE_INTERVAL_MINUTES

        if not parsed_interval:
            parsed_interval = DEFAULT_BALANCE_UPDATE_INTERVAL_MINUTES

        safe_interval = max(
            MIN_BALANCE_UPDATE_INTERVAL_MINUTES,
            min(parsed_interval, MAX_BALANCE_UPDATE_INTERVAL_MINUTES),
        )
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_balance",
            update_interval=timedelta(minutes=safe_interval),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch organization details from GoSMS."""
        try:
            return await self.client.async_get_organization_detail()
        except GoSmsError as err:
            raise UpdateFailed("Failed to fetch GoSMS balance data") from err
        except Exception as err:
            raise UpdateFailed("Unexpected error while fetching GoSMS balance data") from err
