from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_CHANNEL, DATA_COORDINATOR, DOMAIN
from .coordinator import GoSmsDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up GoSMS balance sensor based on a config entry."""
    coordinator: GoSmsDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([GoSmsBalanceSensor(coordinator, entry)])


class GoSmsBalanceSensor(CoordinatorEntity[GoSmsDataUpdateCoordinator], SensorEntity):
    """GoSMS balance sensor."""

    _attr_has_entity_name = False
    _attr_name = "GoSMS Balance"
    _attr_device_class = SensorDeviceClass.MONETARY

    def __init__(self, coordinator: GoSmsDataUpdateCoordinator, entry: ConfigEntry) -> None:
        """Initialize balance sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_balance"

    @property
    def native_value(self) -> float | None:
        """Return current balance value."""
        data = self.coordinator.data or {}
        balance = data.get("balance")
        if isinstance(balance, (int, float)):
            return float(balance)
        return None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return currency code when available."""
        data = self.coordinator.data or {}
        currency = data.get("currency")
        if isinstance(currency, str) and currency.strip():
            return currency.strip()
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return safe additional attributes."""
        data = self.coordinator.data or {}
        attrs: dict[str, Any] = {
            "channel": self._entry.data.get(CONF_CHANNEL),
        }

        invoicing_type = data.get("invoicing_type")
        if isinstance(invoicing_type, str) and invoicing_type.strip():
            attrs["invoicing_type"] = invoicing_type

        return attrs
