"""Async tests for PaymentType API."""

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


@pytest.fixture
def table_response() -> list[dict]:
    return [
        {
            "id": "abc",
            "bankName": "TestBank",
            "accountNumber": "40817810000000000001",
            "favorite": False,
        },
        {
            "id": "def",
            "bankName": "FavBank",
            "accountNumber": "40817810000000000002",
            "favorite": True,
        },
    ]


class TestPaymentTypeAPI:
    """Test PaymentType API functionality."""

    @pytest.mark.asyncio
    async def test_table_returns_list(self, authenticated_token, table_response):
        client = Client()
        await client.authenticate(authenticated_token)

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            respx_mock.get("/payment-type/table").mock(
                return_value=httpx.Response(200, json=table_response)
            )

            result = await client.payment_type().table()

        assert result == table_response
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_favorite_returns_first_favorite_entry(
        self, authenticated_token, table_response
    ):
        client = Client()
        await client.authenticate(authenticated_token)

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            respx_mock.get("/payment-type/table").mock(
                return_value=httpx.Response(200, json=table_response)
            )

            favorite = await client.payment_type().favorite()

        assert favorite is not None
        assert favorite["id"] == "def"
        assert favorite["favorite"] is True

    @pytest.mark.asyncio
    async def test_favorite_returns_none_when_no_favorite(self, authenticated_token):
        client = Client()
        await client.authenticate(authenticated_token)

        no_fav_response = [
            {"id": "x", "favorite": False},
            {"id": "y", "favorite": False},
        ]

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            respx_mock.get("/payment-type/table").mock(
                return_value=httpx.Response(200, json=no_fav_response)
            )

            favorite = await client.payment_type().favorite()

        assert favorite is None

    @pytest.mark.asyncio
    async def test_favorite_returns_none_on_empty_table(self, authenticated_token):
        client = Client()
        await client.authenticate(authenticated_token)

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            respx_mock.get("/payment-type/table").mock(
                return_value=httpx.Response(200, json=[])
            )

            favorite = await client.payment_type().favorite()

        assert favorite is None
