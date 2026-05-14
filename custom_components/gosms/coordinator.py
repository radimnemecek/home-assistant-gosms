from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import GoSmsApiClient, GoSmsError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class GoSmsDataUpdateCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for GoSMS account-level data."""

    def __init__(self, hass: HomeAssistant, client: GoSmsApiClient) -> None:
        """Initialize coordinator."""
        self.client = client
        super().__init__(
            hass,
            logger=_LOGGER,
            name=f"{DOMAIN}_balance",
            update_interval=timedelta(minutes=30),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch organization details from GoSMS."""
        try:
            return await self.client.async_get_organization_detail()
        except GoSmsError as err:
            raise UpdateFailed("Failed to fetch GoSMS balance data") from err
        except Exception as err:
            raise UpdateFailed("Unexpected error while fetching GoSMS balance data") from err
