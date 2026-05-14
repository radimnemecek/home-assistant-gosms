from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

TOKEN_URL = "https://app.gosms.eu/oauth/v2/token"
MESSAGES_URL = "https://app.gosms.eu/api/v1/messages"
ORGANIZATION_DETAIL_URL = "https://app.gosms.eu/api/v1"


class GoSmsError(Exception):
    """Base GoSMS error."""


class GoSmsAuthError(GoSmsError):
    """GoSMS authentication error."""


class GoSmsApiClient:
    """Small API client for GoSMS."""

    def __init__(
        self,
        session: aiohttp.ClientSession,
        client_id: str,
        client_secret: str,
        channel: int,
    ) -> None:
        self._session = session
        self._client_id = client_id
        self._client_secret = client_secret
        self._channel = channel

    async def async_get_access_token(self) -> str:
        """Get OAuth access token."""
        params = {
            "grant_type": "client_credentials",
            "client_id": self._client_id,
            "client_secret": self._client_secret,
        }

        async with self._session.get(TOKEN_URL, params=params) as response:
            data: dict[str, Any] = await response.json(content_type=None)

            if response.status >= 400:
                raise GoSmsAuthError("Unable to authenticate with GoSMS.")

            access_token = data.get("access_token")

            if not access_token:
                raise GoSmsAuthError("GoSMS response did not contain access token.")

            return str(access_token)

    async def async_send_sms(self, recipients: list[str], message: str) -> dict[str, Any]:
        """Send SMS message."""
        access_token = await self.async_get_access_token()

        params = {
            "access_token": access_token,
        }

        payload = {
            "channel": self._channel,
            # GoSMS accepts recipients in the same string field used for single-recipient sending.
            "recipients": ",".join(recipients),
            "message": message,
        }

        async with self._session.post(MESSAGES_URL, params=params, json=payload) as response:
            data: dict[str, Any] = await response.json(content_type=None)

            if response.status >= 400:
                _LOGGER.warning("GoSMS send failed: %s", data)
                raise GoSmsError("Unable to send SMS via GoSMS.")

            return data

    async def async_get_organization_detail(self) -> dict[str, Any]:
        """Load organization details including current credit/balance."""
        access_token = await self.async_get_access_token()

        params = {
            "access_token": access_token,
        }

        async with self._session.get(ORGANIZATION_DETAIL_URL, params=params) as response:
            data: dict[str, Any] = await response.json(content_type=None)

            if response.status >= 400:
                raise GoSmsError("Unable to load GoSMS organization details.")

            current_credit = data.get("currentCredit")
            normalized_balance: float | None
            try:
                normalized_balance = (
                    float(current_credit) if current_credit is not None else None
                )
            except (TypeError, ValueError):
                normalized_balance = None

            return {
                "balance": normalized_balance,
                "currency": data.get("currency"),
                "invoicing_type": data.get("invoicingType"),
                "raw": data,
            }
