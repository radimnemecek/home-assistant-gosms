from __future__ import annotations

import logging
from typing import Any

import aiohttp

_LOGGER = logging.getLogger(__name__)

TOKEN_URL = "https://app.gosms.eu/oauth/v2/token"
MESSAGES_URL = "https://app.gosms.eu/api/v1/messages"
MESSAGES_TEST_URL = "https://app.gosms.eu/api/v1/messages/test"
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

    async def async_send_sms(self, recipients: list[str], message: str, channel: int | None = None) -> dict[str, Any]:
        """Send SMS message."""
        access_token = await self.async_get_access_token()

        params = {
            "access_token": access_token,
        }

        payload = {
            "channel": channel if channel is not None else self._channel,
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

    async def async_preview_sms(self, recipients: list[str], message: str, channel: int | None = None) -> dict[str, Any]:
        """Preview SMS details without sending a message."""
        access_token = await self.async_get_access_token()

        params = {
            "access_token": access_token,
        }

        payload = {
            "channel": channel if channel is not None else self._channel,
            # GoSMS SendMessage schema allows recipients as string/array/object.
            "recipients": recipients,
            "message": message,
        }

        async with self._session.post(MESSAGES_TEST_URL, params=params, json=payload) as response:
            data: dict[str, Any] = await response.json(content_type=None)

            if response.status >= 400:
                raise GoSmsError("Unable to preview SMS via GoSMS.")

            stats = data.get("stats") if isinstance(data.get("stats"), dict) else {}
            sending_info = (
                data.get("sendingInfo") if isinstance(data.get("sendingInfo"), dict) else {}
            )

            def _to_float(value: Any) -> float | None:
                try:
                    return float(value)
                except (TypeError, ValueError):
                    return None

            def _to_int(value: Any) -> int | None:
                try:
                    return int(value)
                except (TypeError, ValueError):
                    return None

            currency = stats.get("currency")
            status = sending_info.get("status")

            return {
                "price": _to_float(stats.get("price")),
                "currency": currency.strip() if isinstance(currency, str) else None,
                "sms_count": _to_int(stats.get("smsCount")),
                # GoSMS OpenAPI uses the key name "messagePatsCount" in TestSendMessageDetail.
                "message_parts_count": _to_int(stats.get("messagePatsCount")),
                "recipients_count": _to_int(stats.get("recipientsCount")),
                "has_diacritics": (
                    stats.get("hasDiacritics")
                    if isinstance(stats.get("hasDiacritics"), bool)
                    else None
                ),
                "status": status if isinstance(status, str) else None,
                "number_types": stats.get("numberTypes") if isinstance(stats.get("numberTypes"), dict) else None,
            }
