"""Async tests for Tax API."""

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


class TestTaxAPI:
    """Test Tax API functionality."""

    @pytest.mark.asyncio
    async def test_get_returns_current_tax_data(self, authenticated_token):
        client = Client()
        await client.authenticate(authenticated_token)

        tax_data = {"amount": "100.00", "currency": "RUB", "status": "due"}

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            respx_mock.get("/taxes").mock(
                return_value=httpx.Response(200, json=tax_data)
            )

            result = await client.tax().get()

        assert result == tax_data

    @pytest.mark.asyncio
    async def test_history_without_oktmo_posts_null(self, authenticated_token):
        client = Client()
        await client.authenticate(authenticated_token)

        history_data = {"records": []}

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            route = respx_mock.post("/taxes/history").mock(
                return_value=httpx.Response(200, json=history_data)
            )

            result = await client.tax().history()

        assert result == history_data
        assert route.called
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"oktmo": None}

    @pytest.mark.asyncio
    async def test_history_with_oktmo_passes_value(self, authenticated_token):
        client = Client()
        await client.authenticate(authenticated_token)

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            route = respx_mock.post("/taxes/history").mock(
                return_value=httpx.Response(200, json={"records": []})
            )

            await client.tax().history(oktmo="46000000")

        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"oktmo": "46000000"}

    @pytest.mark.asyncio
    async def test_payments_defaults_only_paid_false(self, authenticated_token):
        client = Client()
        await client.authenticate(authenticated_token)

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            route = respx_mock.post("/taxes/payments").mock(
                return_value=httpx.Response(200, json={"records": []})
            )

            await client.tax().payments()

        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"oktmo": None, "onlyPaid": False}

    @pytest.mark.asyncio
    async def test_payments_with_only_paid_and_oktmo(self, authenticated_token):
        client = Client()
        await client.authenticate(authenticated_token)

        with respx.mock(base_url="https://lknpd.nalog.ru/api/v1") as respx_mock:
            route = respx_mock.post("/taxes/payments").mock(
                return_value=httpx.Response(
                    200, json={"records": [{"id": "p1", "amount": "50"}]}
                )
            )

            result = await client.tax().payments(oktmo="46000000", only_paid=True)

        assert len(result["records"]) == 1
        sent_body = json.loads(route.calls[0].request.content)
        assert sent_body == {"oktmo": "46000000", "onlyPaid": True}
