"""Async tests for User API."""

import json

import httpx
import pytest
import respx

from nalogo.client import Client


@pytest.fixture
def authenticated_token() -> str:
    return json.dumps(
        {
            "token": "test_access_token",
            "refreshToken": "test_refresh_token",
            "profile": {"inn": "123456789012", "displayName": "Test User"},
        }
    )


class TestUserAPI:
    """Test User API functionality."""

    @pytest.mark.asyncio
    async def test_get_returns_profile_dict(self, authenticated_token):
        client = Client()
        await client.authenticate(authenticated_token)

        profile = {
            "id": 1000000,
            "inn": "123456789012",
            "displayName": "Test User",
            "email": "test@example.com",
            "phone": "79000000000",
            "status": "ACTIVE",
        }

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            respx_mock.get("/user").mock(
                return_value=httpx.Response(200, json=profile)
            )

            result = await client.user().get()

        assert result == profile
        assert result["inn"] == "123456789012"
