# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`nalogo` — async Python client for the `lknpd.nalog.ru` ("Мой Налог") API used by Russian self-employed (самозанятые) to register income, fetch/cancel receipts, and read tax info. **This repo is a fork of [Rusik636/NaloGO](https://github.com/Rusik636/NaloGO)**, hosted as `blackden/NaloGO`. The library itself is a Python port of the PHP library [shoman4eg/moy-nalog](https://github.com/shoman4eg/moy-nalog) — the source-of-truth for *what each endpoint does* is still the PHP code; this codebase ports its semantics. Python `>=3.11`, packaged as `nalogo` on PyPI.

The README is in Russian; keep that convention for user-facing docstrings/error messages, but code identifiers stay English.

## Commands

Local tooling — prefer `uv` (project-wide preference, see `~/.claude/CLAUDE.md`); the upstream README uses raw `pip`, but `uv pip ...` is a drop-in:

```bash
uv venv && source .venv/bin/activate           # one-time
uv pip install -e ".[dev]"                     # all dev deps
```

Run the gates the same way CI runs them — they are the merge bar:

```bash
ruff check .                                   # lint
black --check .                                # format check (CI fails on dirty)
mypy nalogo/                                   # strict-ish: disallow_untyped_defs + warn_*
pytest                                         # full suite, asyncio_mode=auto
pytest tests/test_income_async.py              # single file
pytest tests/test_income_async.py -k cancel    # single test by name
pytest --cov=nalogo --cov-fail-under=80        # CI's coverage gate
bandit -r nalogo/ -ll                          # security scan (CI runs it)
python -m build && twine check dist/*          # CI's package-check job
```

`pytest-asyncio` is in `asyncio_mode=auto` — write `async def test_*` without `@pytest.mark.asyncio`. HTTP is mocked with `respx` (`pytest-httpx` not used).

## Architecture

The codebase mirrors the PHP original 1:1 in shape — docstrings throughout say `Maps to PHP X::y()`. If something looks unmotivated, the answer is usually "the PHP version does it this way."

**Three layers matter:**

**1. `Client` facade (`nalogo/client.py`)** — async entry point. Constructor takes `base_url`, optional `storage_path` (file for token persistence), `device_id`, `timeout`. Authenticates via `create_new_access_token(inn, pwd)` / `create_phone_challenge(phone)` + `create_new_access_token_by_phone(...)`, then `authenticate(token_json)`. Sub-API factory methods: `income()`, `receipt()`, `user()`, `tax()`, `payment_type()` — each returns a fresh wrapper bound to the shared `AsyncHTTPClient`.

**2. Auth (`nalogo/auth.py`)** — `AuthProviderImpl` implements the three flows:
- `create_new_access_token(inn, pwd)` → `POST {v1}/auth/lkfl`
- `create_phone_challenge(phone)` → `POST {v2}/auth/challenge/sms/start` (note: **v2**, all other calls use v1)
- `create_new_access_token_by_phone(phone, challengeToken, code)` → `POST {v1}/auth/challenge/sms/verify`
- `refresh(refreshToken)` → `POST {v1}/auth/token`, called transparently by the HTTP client

Token is the **full JSON blob from the upstream API** (token + refreshToken + profile + expiry), stored as `dict` in memory and optionally mirrored to `storage_path` (plain JSON on disk, including the refresh token — flag this for prod).

**3. HTTP pipeline (`nalogo/_http.py`)** — `AsyncHTTPClient.request()` injects `Authorization: Bearer <token>`; on a 401, takes `_refresh_lock` (asyncio.Lock prevents concurrent refresh storms), calls `auth_provider.refresh()`, and retries the request once. Single retry, matches PHP's `RETRY_LIMIT = 2`. After that, `raise_for_status()` maps the HTTP status to a typed exception.

Sub-API modules (`income.py`, `receipt.py`, `tax.py`, `user.py`, `payment_type.py`) are thin wrappers: build a pydantic v2 DTO, call `self.http.post(path, json_data=req.model_dump())`, return parsed JSON or hydrate via another DTO.

**Errors** (`nalogo/exceptions.py`) — `raise_for_status()` dispatches by status code to `ValidationException` (400), `UnauthorizedException` (401), `ForbiddenException` (403), `NotFoundException` (404), `ClientException` (406), `PhoneException` (422), `ServerException` (500), `UnknownErrorException` (else). All inherit `DomainException`, which **auto-logs the error with sensitive-data masking** (Authorization header, `token`/`refreshToken`/`password`/`secret` JSON fields, URL `token=`/`key=`/`secret=` query params). Don't roll your own logging around these — extend the masking patterns instead.

**DTOs (`nalogo/dto/`)** — pydantic v2 models with field aliases for JSON-PHP-style camelCase. Money goes through `decimal.Decimal` from `IncomeServiceItem.amount` onwards and is stringified at the request boundary; don't introduce `float` in finance paths. `IncomeType`, `PaymentType`, `CancelCommentType` are real `enum.Enum` subclasses (not constants — we're on 3.11+).

## Things to know before touching code

- **`.coverage` is committed to the repo despite being in `.gitignore`.** That's not a bug in `.gitignore` — `gitignore` only affects untracked files, and `.coverage` was tracked before the rule existed. If you want it out: `git rm --cached .coverage` in a follow-up. Until then, every `pytest --cov` run dirties the working tree.
- **`.gitignore` has `*.json` blanket-ignored** with an explicit allowlist (`!package.json`, `!pyproject.toml`). Adding a JSON test fixture requires either an explicit `!path/...` line or `git add -f`. Easy to forget; PR reviews catch nothing.
- **`pyproject.toml` `[project.urls]` still points to `your-org/nalogo`** — placeholder text from before publication. If we ever cut a release from this fork under a new PyPI name, those URLs and `authors`/`name` need editing first.
- **CI triggers on `migrate/python-async*` branches** (`.github/workflows/ci.yml`) — legacy from the PHP→Python migration phase. Safe to delete from the trigger list when we touch CI.
- **Token JSON blob is the public contract.** `client.authenticate(s: str)` takes the JSON string straight from `create_new_access_token*()`; `client.get_access_token()` returns it back as a string. Don't try to "improve" this by slicing the blob — `Client.receipt()` parses `profile.inn` from the JSON to build receipt URLs *without* a round-trip, and other downstream code may rely on the round-trippability.
- **`Client.receipt()` raises `ValueError` if profile is missing.** Profile is parsed from the token JSON on `authenticate()`. Custom/external tokens that don't carry `profile.inn` will not work for the receipt API. PHP version falls back to `user().get()` — Python version does not. Consider this before "fixing" downstream callers.
- **`httpx.AsyncClient()` is instantiated per request** in `_http.py` (and per call in `auth.py`). No connection pool reuse. For this API's traffic profile it's fine, but a long-running script that makes many calls will pay the TLS handshake every time. If you optimize this, do it without breaking the 401-retry path.
- **`refresh()` swallows all exceptions** (`auth.py`: `except Exception: return None`) by design, to match PHP's silent-fail behavior. Returns `None` → caller treats it as "refresh failed, give up." If you debug auth issues, temporarily replace this with `logger.exception` rather than `print`.
- **Python 3.11+ floor.** Free to use `Self`, `StrEnum`, `ExceptionGroup`, PEP 604 `X | Y` unions. Don't introduce `from __future__ import annotations` selectively — be consistent with the existing files (currently *not* using it).

## Upstream

The PHP library at [shoman4eg/moy-nalog](https://github.com/shoman4eg/moy-nalog) is the semantic reference for endpoint behavior, error codes, and edge cases — when in doubt about *what the API expects*, read the PHP source, not just the Python port. The upstream Python repo [Rusik636/NaloGO](https://github.com/Rusik636/NaloGO) (this fork's parent) tracks Python-side fixes; consider adding it as a `git remote` named `upstream` and pulling fixes from there.
