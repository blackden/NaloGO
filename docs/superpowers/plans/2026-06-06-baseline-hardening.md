# Baseline Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring the freshly-forked `nalogo` repo to a reproducible, lock-pinned green baseline; pay down five concrete debts captured in `docs/journal.md` (2026-06-06) so the next feature work starts from a stable floor.

**Architecture:** Each task = one GitHub issue → one branch (`task/<N>-<slug>`) → atomic conventional-commit history → one PR → squash-merge to `main`. The squash gives `main` exactly one line of history per task; the branch retains the TDD steps for archaeology. Tasks are sequential (Task 1 first — every subsequent task benefits from pinned versions), but Tasks 2 and 3 are trivially independent and can be run in any order after Task 1.

**Tech Stack:** Python 3.11+ (CI matrix 3.11/3.12), `uv` for env/locks, `httpx` + `pydantic v2` runtime, `pytest` + `respx` for tests, `ruff` + `black` + `mypy` + `bandit` for static gates, GitHub Actions for CI, `gh` CLI for issue/PR work.

---

## Conventions used throughout this plan

**Branch naming:** `task/<N>-<short-slug>`, e.g. `task/1-pin-versions`.

**Commit messages:** [Conventional Commits](https://www.conventionalcommits.org/) — `feat:`, `fix:`, `chore:`, `test:`, `refactor:`, `ci:`, `docs:`. The squash-merge to `main` will use the PR title as the message, so the in-branch commits are for archaeology only.

**Issue body template** (used in every task's Step 1):
```
Plan: docs/superpowers/plans/2026-06-06-baseline-hardening.md (Task N)

<one-paragraph task description from the plan>
```

**PR body template** (used in every task's final step):
```
Closes #<issue-number>

Part of the baseline-hardening pass. See `docs/superpowers/plans/2026-06-06-baseline-hardening.md` Task N.

## Changes
<bullet list>

## Verification
<exact commands run + outcome>
```

**Activate the venv before running any python/ruff/pytest/mypy/bandit command:**
```bash
source .venv/bin/activate
```
(All "Run:" lines below assume the venv is active.)

---

## File-level map of the work

| Task | Files created | Files modified |
|---|---|---|
| 1 | `uv.lock` | `pyproject.toml` |
| 2 | — | `.coverage` (deleted from index) |
| 3 | — | `.github/workflows/ci.yml` |
| 4 | `tests/test_dto_enum_serialization.py` | `nalogo/dto/income.py` |
| 5 | `tests/test_payment_type_async.py` | — |
| 6 | `tests/test_tax_async.py` | — |
| 7 | `tests/test_user_async.py` | — |

---

## Task 1: Pin dev tool versions and introduce `uv.lock`

**Why:** Today's CI is green only because GitHub Actions happens to install the right ruff/black/mypy versions. Locally on `ruff 0.15.16` three `UP042` errors appear — the same code would red CI as soon as the runner image bumps ruff. Pinning + `uv.lock` makes "green" reproducible across machines and across time.

**Files:**
- Modify: `pyproject.toml` (lines 36–55: `[project] dependencies` and `[project.optional-dependencies] dev`)
- Create: `uv.lock`

- [ ] **Step 1: Create issue and branch**

```bash
gh issue create \
  --title "chore: pin dev tool versions and introduce uv.lock" \
  --body "Plan: docs/superpowers/plans/2026-06-06-baseline-hardening.md (Task 1)

Pin minor versions of ruff/black/mypy/bandit/pytest/respx in pyproject.toml and commit a generated uv.lock so CI reproducibility is independent of GitHub Actions cache state. Today the upstream CI is green only because the cached ruff happens to predate the UP042 rule; locally on ruff 0.15 the same code shows three errors. Pin to ranges that exclude the next major (e.g. >=0.15.0,<0.16.0)."
```

Capture the issue number printed. Then:

```bash
git checkout -b task/1-pin-versions
```

- [ ] **Step 2: Read current state of pyproject.toml dev deps**

Run:
```bash
sed -n '36,55p' pyproject.toml
```
Expected output (current state):
```
dependencies = [
    "httpx>=0.25.0",
    "pydantic>=2.0.0,<3.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
    "respx>=0.20.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
    "mypy>=1.0.0",
    "coverage>=7.0.0",
    "bandit[toml]>=1.7.0",
    "build>=1.0.0",
    "twine>=4.0.0",
]
```

- [ ] **Step 3: Tighten version ranges**

Edit `pyproject.toml`. Replace the `[project.optional-dependencies] dev` block with **upper-bound-exclusive minor pins** (allows patch releases, blocks minor/major drift). Keep runtime `dependencies` as-is (they're already conservative).

New `dev` block:
```toml
dev = [
    "pytest>=7.0.0,<10.0.0",
    "pytest-asyncio>=0.21.0,<2.0.0",
    "pytest-cov>=4.0.0,<8.0.0",
    "respx>=0.20.0,<0.24.0",
    "ruff>=0.15.0,<0.16.0",
    "black>=24.0.0,<26.0.0",
    "mypy>=1.0.0,<2.0.0",
    "coverage>=7.0.0,<8.0.0",
    "bandit[toml]>=1.7.0,<2.0.0",
    "build>=1.0.0,<2.0.0",
    "twine>=4.0.0,<7.0.0",
]
```

Use the Edit tool to replace the exact 13-line block.

- [ ] **Step 4: Generate `uv.lock`**

Run:
```bash
uv lock
```
Expected: a new file `uv.lock` is written; no error. Run `ls -la uv.lock` to confirm it exists.

- [ ] **Step 5: Recreate venv from lock and re-run gates**

Run:
```bash
rm -rf .venv && uv venv --python 3.12 && uv pip install -e ".[dev]"
source .venv/bin/activate
ruff check .
black --check .
mypy nalogo/
pytest --cov=nalogo --cov-fail-under=80
bandit -r nalogo/ -ll
```
Expected:
- `ruff`: **3 errors UP042** in `nalogo/dto/income.py` (Task 4 will fix these) — this is the *known* baseline. Do NOT block Task 1 on it.
- `black`, `mypy`, `pytest`, `bandit`: all clean. Coverage 80.74%.

If anything other than the 3 known `UP042`s appears, stop and investigate before committing.

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: pin dev tool versions and add uv.lock

Constrain ruff/black/mypy/bandit/pytest/respx to upper-bound-exclusive
minor ranges and commit a generated uv.lock. Locks CI's notion of
'green' to a reproducible toolchain so a future ruff release cannot
silently turn the build red."
```

- [ ] **Step 7: Push and open PR**

```bash
git push -u origin task/1-pin-versions
gh pr create \
  --title "chore: pin dev tool versions and introduce uv.lock" \
  --body "Closes #<issue-number-from-Step-1>

Part of the baseline-hardening pass. See \`docs/superpowers/plans/2026-06-06-baseline-hardening.md\` Task 1.

## Changes
- Tightened upper bounds on every entry in \`[project.optional-dependencies] dev\`.
- Added \`uv.lock\` to the repo.

## Verification
- Recreated venv from scratch with \`rm -rf .venv && uv venv --python 3.12 && uv pip install -e \".[dev]\"\`.
- \`ruff check .\` → 3 known UP042 errors (Task 4 territory); no new findings.
- \`black --check\`, \`mypy nalogo/\`, \`pytest --cov-fail-under=80\`, \`bandit -r nalogo/ -ll\` all clean."
```

Wait for CI to report. Squash-merge once green (or once owner approves).

---

## Task 2: Untrack `.coverage` and prevent future re-adds

**Why:** `.coverage` (sqlite artifact from `pytest --cov`) is checked into the repo despite being in `.gitignore`. `.gitignore` only ignores *untracked* files; an already-tracked file must be explicitly untracked with `git rm --cached`. Every local coverage run currently dirties the working tree.

**Files:**
- Delete from index (file stays on disk): `.coverage`

- [ ] **Step 1: Create issue and branch**

```bash
gh issue create \
  --title "chore: untrack .coverage (already in .gitignore)" \
  --body "Plan: docs/superpowers/plans/2026-06-06-baseline-hardening.md (Task 2)

.coverage (sqlite artifact written by coverage.py during pytest --cov) is committed to the repo despite being in .gitignore. .gitignore only blocks untracked files, so the existing tracked copy stays. Run git rm --cached to remove from the index without deleting the local file. After this, future pytest --cov runs will no longer dirty the working tree."
```

```bash
git checkout main && git pull && git checkout -b task/2-untrack-coverage
```

- [ ] **Step 2: Confirm the file is currently tracked**

Run:
```bash
git ls-files .coverage
```
Expected: prints `.coverage`. If empty, the file is already untracked — abort this task as already-done and close the issue with a comment.

- [ ] **Step 3: Confirm `.gitignore` already excludes it**

Run:
```bash
grep -n '^\.coverage' .gitignore
```
Expected: a match like `73:.coverage` (line number may vary). If no match, also add `.coverage` to `.gitignore` in this commit.

- [ ] **Step 4: Untrack the file**

Run:
```bash
git rm --cached .coverage
```
Expected output: `rm '.coverage'`.

The file on disk is preserved. Verify:
```bash
test -f .coverage && echo "still on disk"
git status
```
Expected: `still on disk`, and `git status` shows `.coverage` as `deleted` in the index, with no working-tree counterpart (because `.gitignore` masks it).

- [ ] **Step 5: Commit**

```bash
git commit -m "chore: untrack .coverage

The file is already listed in .gitignore but was committed before
that rule existed. .gitignore does not retroactively untrack
files — git rm --cached removes it from the index while leaving
the local copy alone."
```

- [ ] **Step 6: Push and open PR**

```bash
git push -u origin task/2-untrack-coverage
gh pr create \
  --title "chore: untrack .coverage (already in .gitignore)" \
  --body "Closes #<issue-number>

Part of the baseline-hardening pass. See \`docs/superpowers/plans/2026-06-06-baseline-hardening.md\` Task 2.

## Changes
- \`git rm --cached .coverage\` — removes from index, file stays on disk and is masked by existing .gitignore rule.

## Verification
- \`git ls-files .coverage\` → empty after change.
- \`test -f .coverage && echo ok\` → ok (local file untouched)."
```

---

## Task 3: Drop legacy `migrate/python-async*` branches from CI triggers

**Why:** `.github/workflows/ci.yml` triggers on push to `main`, `migrate/python-async`, and `migrate/python-async-p1`. The last two were the migration branches when the Python port was assembled. They're long dead, but they sit in the trigger list as visual noise and as a foot-gun (someone names a future branch `migrate/python-async-*` and accidentally triggers CI on every push).

**Files:**
- Modify: `.github/workflows/ci.yml:4-6`

- [ ] **Step 1: Create issue and branch**

```bash
gh issue create \
  --title "ci: drop legacy migrate/python-async* branches from triggers" \
  --body "Plan: docs/superpowers/plans/2026-06-06-baseline-hardening.md (Task 3)

CI currently triggers on push to main, migrate/python-async, migrate/python-async-p1. The last two were the upstream migration branches that no longer exist. Strip them to: push on main only; PR to main only."
```

```bash
git checkout main && git pull && git checkout -b task/3-clean-ci-triggers
```

- [ ] **Step 2: Read current trigger block**

Run:
```bash
sed -n '1,8p' .github/workflows/ci.yml
```
Expected:
```yaml
name: Python CI

on:
  push:
    branches: [ main, migrate/python-async, migrate/python-async-p1 ]
  pull_request:
    branches: [ main ]
```

- [ ] **Step 3: Edit the `on:` block**

Use the Edit tool. Replace the exact 5-line `on:` block above with:

```yaml
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
```

- [ ] **Step 4: Verify yaml is still valid**

Run:
```bash
python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('valid')"
```
Expected: `valid` printed; no traceback.

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: drop dead migrate/python-async* branches from triggers

These were the upstream Python-port migration branches and no
longer exist. Keeping them in the trigger list adds noise and a
foot-gun for future branch naming."
```

- [ ] **Step 6: Push and open PR**

```bash
git push -u origin task/3-clean-ci-triggers
gh pr create \
  --title "ci: drop legacy migrate/python-async* branches from triggers" \
  --body "Closes #<issue-number>

Part of the baseline-hardening pass. See \`docs/superpowers/plans/2026-06-06-baseline-hardening.md\` Task 3.

## Changes
- Removed \`migrate/python-async\` and \`migrate/python-async-p1\` from \`.github/workflows/ci.yml\` push-trigger list.

## Verification
- YAML parses (\`python -c 'import yaml; yaml.safe_load(...)'\`)."
```

---

## Task 4: Migrate `class X(str, Enum)` → `StrEnum` with serialization regression test

**Why:** `ruff UP042` flags three classes in `nalogo/dto/income.py` (`IncomeType`, `PaymentType`, `CancelCommentType`) that use the legacy 3.10-style `(str, Enum)` mixin. On 3.11+ the idiomatic form is `enum.StrEnum`. The two produce identical `.value` and `json.dumps(x.value)` output but differ in `str(x)` and f-string interpolation: `class X(str, Enum)` returns `"X.A"`; `StrEnum` returns the value. The codebase uses `.value` explicitly everywhere in `model_dump()` (`nalogo/dto/income.py:169, 209, 244`), so the wire format is unchanged — but we add a regression test that pins this behavior in case a future refactor switches to `str(...)` interpolation.

**Files:**
- Create: `tests/test_dto_enum_serialization.py`
- Modify: `nalogo/dto/income.py:8` (import), `:14` (`IncomeType`), `:22` (`PaymentType`), `:29` (`CancelCommentType`)

- [ ] **Step 1: Create issue and branch**

```bash
gh issue create \
  --title "refactor: migrate income DTO enums to StrEnum (ruff UP042)" \
  --body "Plan: docs/superpowers/plans/2026-06-06-baseline-hardening.md (Task 4)

Three classes in nalogo/dto/income.py use the pre-3.11 (str, Enum) mixin and trip ruff UP042. The codebase targets Python 3.11+ so StrEnum is the idiomatic form. Wire format is unchanged because model_dump() uses .value explicitly, but pin that with a regression test before the refactor."
```

```bash
git checkout main && git pull && git checkout -b task/4-strenum-migration
```

- [ ] **Step 2: Write the failing/baseline-pinning test**

Create `tests/test_dto_enum_serialization.py`:

```python
"""
Pins the wire-format behavior of income DTO enums.

These tests must keep passing across the (str, Enum) → StrEnum
migration. They cover the only thing that matters for the upstream
API contract: the exact strings sent on the wire via .value and
model_dump().
"""

import json
from datetime import UTC, datetime
from decimal import Decimal

from nalogo.dto.income import (
    AtomDateTime,
    CancelCommentType,
    CancelRequest,
    IncomeClient,
    IncomeRequest,
    IncomeServiceItem,
    IncomeType,
    PaymentType,
)


class TestEnumValues:
    """Raw .value must round-trip the upstream-API strings exactly."""

    def test_income_type_values(self) -> None:
        assert IncomeType.FROM_INDIVIDUAL.value == "FROM_INDIVIDUAL"
        assert IncomeType.FROM_LEGAL_ENTITY.value == "FROM_LEGAL_ENTITY"
        assert IncomeType.FROM_FOREIGN_AGENCY.value == "FROM_FOREIGN_AGENCY"

    def test_payment_type_values(self) -> None:
        assert PaymentType.CASH.value == "CASH"
        assert PaymentType.ACCOUNT.value == "ACCOUNT"

    def test_cancel_comment_values(self) -> None:
        assert CancelCommentType.CANCEL.value == "Чек сформирован ошибочно"
        assert CancelCommentType.REFUND.value == "Возврат средств"


class TestEnumStringBehavior:
    """str() and equality behavior we explicitly rely on."""

    def test_str_subclass_equality(self) -> None:
        # Both (str, Enum) and StrEnum compare equal to the raw string.
        assert IncomeType.FROM_INDIVIDUAL == "FROM_INDIVIDUAL"
        assert PaymentType.CASH == "CASH"
        assert CancelCommentType.CANCEL == "Чек сформирован ошибочно"

    def test_json_dumps_uses_value(self) -> None:
        # json.dumps treats both str-Enum forms as the underlying string.
        assert json.dumps(IncomeType.FROM_INDIVIDUAL.value) == '"FROM_INDIVIDUAL"'
        assert json.dumps(PaymentType.CASH.value) == '"CASH"'


class TestDTOSerialization:
    """model_dump() on the request DTOs must produce the exact upstream payload."""

    def test_income_request_dump_includes_enum_value(self) -> None:
        item = IncomeServiceItem(
            name="Service",
            amount=Decimal("100"),
            quantity=Decimal("1"),
        )
        req = IncomeRequest(
            operation_time=AtomDateTime.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            request_time=AtomDateTime.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            services=[item],
            total_amount="100",
            client=IncomeClient(income_type=IncomeType.FROM_LEGAL_ENTITY),
            payment_type=PaymentType.ACCOUNT,
            ignore_max_total_income_restriction=False,
        )
        dumped = req.model_dump()
        assert dumped["paymentType"] == "ACCOUNT"
        assert dumped["client"]["incomeType"] == "FROM_LEGAL_ENTITY"

    def test_cancel_request_dump_includes_comment_value(self) -> None:
        req = CancelRequest(
            operation_time=AtomDateTime.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            request_time=AtomDateTime.from_datetime(datetime(2026, 1, 1, tzinfo=UTC)),
            comment=CancelCommentType.REFUND,
            receipt_uuid="abc",
        )
        dumped = req.model_dump()
        assert dumped["comment"] == "Возврат средств"
```

- [ ] **Step 3: Run the new test on the unchanged code (baseline pin)**

Run:
```bash
pytest tests/test_dto_enum_serialization.py -v
```
Expected: **all 7 tests PASS**. This proves the existing `(str, Enum)` behavior is the contract we will preserve.

- [ ] **Step 4: Commit the test alone (baseline pin)**

```bash
git add tests/test_dto_enum_serialization.py
git commit -m "test: pin enum wire-format behavior before StrEnum migration

Captures the exact strings model_dump() produces for IncomeType,
PaymentType, CancelCommentType so the upcoming StrEnum refactor
can be verified to be wire-compatible."
```

- [ ] **Step 5: Migrate the three enums**

Edit `nalogo/dto/income.py`.

Replace `:8`:
```python
from enum import Enum
```
with:
```python
from enum import StrEnum
```

Replace `:14-19`:
```python
class IncomeType(str, Enum):
    """Income type enumeration. Maps to PHP Enum\\IncomeType."""

    FROM_INDIVIDUAL = "FROM_INDIVIDUAL"
    FROM_LEGAL_ENTITY = "FROM_LEGAL_ENTITY"
    FROM_FOREIGN_AGENCY = "FROM_FOREIGN_AGENCY"
```
with:
```python
class IncomeType(StrEnum):
    """Income type enumeration. Maps to PHP Enum\\IncomeType."""

    FROM_INDIVIDUAL = "FROM_INDIVIDUAL"
    FROM_LEGAL_ENTITY = "FROM_LEGAL_ENTITY"
    FROM_FOREIGN_AGENCY = "FROM_FOREIGN_AGENCY"
```

Replace `:22-26`:
```python
class PaymentType(str, Enum):
    """Payment type enumeration. Maps to PHP Enum\\PaymentType."""

    CASH = "CASH"
    ACCOUNT = "ACCOUNT"
```
with:
```python
class PaymentType(StrEnum):
    """Payment type enumeration. Maps to PHP Enum\\PaymentType."""

    CASH = "CASH"
    ACCOUNT = "ACCOUNT"
```

Replace `:29-33`:
```python
class CancelCommentType(str, Enum):
    """Cancel comment type enumeration. Maps to PHP Enum\\CancelCommentType."""

    CANCEL = "Чек сформирован ошибочно"
    REFUND = "Возврат средств"
```
with:
```python
class CancelCommentType(StrEnum):
    """Cancel comment type enumeration. Maps to PHP Enum\\CancelCommentType."""

    CANCEL = "Чек сформирован ошибочно"
    REFUND = "Возврат средств"
```

- [ ] **Step 6: Verify wire format unchanged**

Run:
```bash
pytest tests/test_dto_enum_serialization.py -v
```
Expected: **all 7 tests still PASS**. If anything fails, the migration broke a contract — investigate before continuing.

- [ ] **Step 7: Verify the full suite and ruff**

Run:
```bash
pytest
ruff check .
mypy nalogo/
black --check .
```
Expected:
- `pytest`: 53 passed (46 existing + 7 new).
- `ruff check`: **0 errors** (the three `UP042` are gone, no new findings).
- `mypy`, `black`: clean.

- [ ] **Step 8: Commit the refactor**

```bash
git add nalogo/dto/income.py
git commit -m "refactor: migrate income DTO enums to StrEnum

Replaces (str, Enum) mixin with the idiomatic Python 3.11+
enum.StrEnum. Wire format is unchanged because model_dump()
uses .value explicitly — verified by the regression test in
tests/test_dto_enum_serialization.py.

Closes the three ruff UP042 findings on this file."
```

- [ ] **Step 9: Push and open PR**

```bash
git push -u origin task/4-strenum-migration
gh pr create \
  --title "refactor: migrate income DTO enums to StrEnum" \
  --body "Closes #<issue-number>

Part of the baseline-hardening pass. See \`docs/superpowers/plans/2026-06-06-baseline-hardening.md\` Task 4.

## Changes
- New \`tests/test_dto_enum_serialization.py\` pins the exact wire-format strings for IncomeType, PaymentType, CancelCommentType (committed in the first commit on this branch, *before* the refactor).
- \`nalogo/dto/income.py\`: \`(str, Enum)\` → \`StrEnum\` for all three enums. Closes the three ruff UP042 findings.

## Verification
- 7 new regression tests pass on the pre-refactor code (baseline pin).
- All 53 tests pass after the refactor.
- \`ruff check .\` reports 0 errors (was 3 UP042 before)."
```

---

## Task 5: Cover `nalogo/payment_type.py` with `respx` tests

**Why:** `nalogo/payment_type.py` sits at 43% line coverage — two methods (`table()`, `favorite()`) with no tests. The total project coverage is 80.74%, only 0.74 pp above the 80% gate; any new code without tests can drop below. Cover the file first so we have headroom.

**Files:**
- Create: `tests/test_payment_type_async.py`

- [ ] **Step 1: Create issue and branch**

```bash
gh issue create \
  --title "test: add respx tests for PaymentTypeAPI (lift coverage above margin)" \
  --body "Plan: docs/superpowers/plans/2026-06-06-baseline-hardening.md (Task 5)

nalogo/payment_type.py is at 43% coverage with no tests. Add respx-mocked tests for table() and favorite() — cover the happy path, the empty-list path, and the no-favorite path."
```

```bash
git checkout main && git pull && git checkout -b task/5-cover-payment-type
```

- [ ] **Step 2: Write the test file**

Create `tests/test_payment_type_async.py`:

```python
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
```

- [ ] **Step 3: Run the new tests**

Run:
```bash
pytest tests/test_payment_type_async.py -v
```
Expected: **4 tests PASS**.

- [ ] **Step 4: Confirm coverage uplift**

Run:
```bash
pytest --cov=nalogo --cov-report=term-missing | grep -E "(payment_type|TOTAL)"
```
Expected:
- `nalogo/payment_type.py` jumps from 43% → ≥90% (only the docstring/return-type-comment lines may remain uncovered).
- `TOTAL` ≥ 81% (was 80.74%).

- [ ] **Step 5: Commit and push**

```bash
git add tests/test_payment_type_async.py
git commit -m "test: cover PaymentTypeAPI.table() and .favorite()

Adds four respx-mocked tests covering the happy path, an empty
table, and the no-favorite-entry case. Lifts payment_type.py
coverage from 43% to ~90% and raises the project floor above
the 80% gate."
git push -u origin task/5-cover-payment-type
```

- [ ] **Step 6: Open PR**

```bash
gh pr create \
  --title "test: cover PaymentTypeAPI (lift baseline above 80% gate)" \
  --body "Closes #<issue-number>

Part of the baseline-hardening pass. See \`docs/superpowers/plans/2026-06-06-baseline-hardening.md\` Task 5.

## Changes
- New \`tests/test_payment_type_async.py\` with 4 cases: happy table, favorite-found, no-favorite, empty-table.

## Verification
- 4 new tests pass.
- \`payment_type.py\` coverage 43% → ~90%.
- Project coverage 80.74% → ≥81%."
```

---

## Task 6: Cover `nalogo/tax.py` with `respx` tests

**Why:** `tax.py` is at 44% coverage with three untested methods (`get()`, `history()`, `payments()`). Same rationale as Task 5 — push the floor up.

**Files:**
- Create: `tests/test_tax_async.py`

- [ ] **Step 1: Create issue and branch**

```bash
gh issue create \
  --title "test: add respx tests for TaxAPI (lift coverage above margin)" \
  --body "Plan: docs/superpowers/plans/2026-06-06-baseline-hardening.md (Task 6)

nalogo/tax.py is at 44% coverage. Add respx tests for get(), history() (with and without oktmo), and payments() (covering only_paid both true and false)."
```

```bash
git checkout main && git pull && git checkout -b task/6-cover-tax
```

- [ ] **Step 2: Write the test file**

Create `tests/test_tax_async.py`:

```python
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
```

- [ ] **Step 3: Run the new tests**

Run:
```bash
pytest tests/test_tax_async.py -v
```
Expected: **5 tests PASS**.

- [ ] **Step 4: Confirm coverage uplift**

Run:
```bash
pytest --cov=nalogo --cov-report=term-missing | grep -E "(tax\.py|TOTAL)"
```
Expected:
- `nalogo/tax.py` jumps from 44% → ≥90%.
- `TOTAL` rises further.

- [ ] **Step 5: Commit, push, PR**

```bash
git add tests/test_tax_async.py
git commit -m "test: cover TaxAPI.get(), .history(), .payments()

Adds five respx tests asserting both the responses and the JSON
bodies sent to /taxes/history and /taxes/payments. Lifts tax.py
coverage from 44% to ~90%."
git push -u origin task/6-cover-tax
gh pr create \
  --title "test: cover TaxAPI methods" \
  --body "Closes #<issue-number>

Part of the baseline-hardening pass. See \`docs/superpowers/plans/2026-06-06-baseline-hardening.md\` Task 6.

## Changes
- New \`tests/test_tax_async.py\` with 5 cases covering get(), history() (with/without oktmo), and payments() (only_paid both branches).

## Verification
- 5 new tests pass.
- \`tax.py\` coverage 44% → ~90%."
```

---

## Task 7: Cover `nalogo/user.py` with `respx` tests

**Why:** `user.py` is at 62% coverage with one untested method (`get()`). Cheapest of the three coverage tasks and finishes the gauntlet.

**Files:**
- Create: `tests/test_user_async.py`

- [ ] **Step 1: Create issue and branch**

```bash
gh issue create \
  --title "test: add respx test for UserAPI.get() (last coverage gap)" \
  --body "Plan: docs/superpowers/plans/2026-06-06-baseline-hardening.md (Task 7)

nalogo/user.py is at 62% coverage — only get() is untested. Add a single happy-path respx test."
```

```bash
git checkout main && git pull && git checkout -b task/7-cover-user
```

- [ ] **Step 2: Write the test file**

Create `tests/test_user_async.py`:

```python
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
```

- [ ] **Step 3: Run, verify, commit, PR**

```bash
pytest tests/test_user_async.py -v
```
Expected: 1 test PASS.

```bash
pytest --cov=nalogo --cov-report=term-missing | grep -E "(user\.py|TOTAL)"
```
Expected: `nalogo/user.py` 62% → 100%.

```bash
git add tests/test_user_async.py
git commit -m "test: cover UserAPI.get()

Happy-path respx test against /user. Closes the last
non-trivial coverage gap among the API modules."
git push -u origin task/7-cover-user
gh pr create \
  --title "test: cover UserAPI.get()" \
  --body "Closes #<issue-number>

Part of the baseline-hardening pass. See \`docs/superpowers/plans/2026-06-06-baseline-hardening.md\` Task 7.

## Changes
- New \`tests/test_user_async.py\` with one happy-path test.

## Verification
- 1 new test passes.
- \`user.py\` coverage 62% → 100%."
```

---

## After all seven tasks land

- Project coverage will be in the high 80s (was 80.74%).
- `ruff check .` will be clean (was 3 UP042).
- CI will run only on `main` push and PR (was also on dead `migrate/python-async*` branches).
- `.coverage` will stay untracked between coverage runs.
- `uv.lock` makes "green CI" reproducible against tool drift.

The next pass (out of scope for this plan, separate brainstorming) covers the items in `docs/journal.md` flagged "не лечим сразу": `httpx.AsyncClient` pooling, `refresh()` exception swallowing, token-blob DTO. Those each need an explicit design decision before any code change.

## Self-review

**Spec coverage** — every item in `docs/journal.md` Section "Известные ловушки апстрима, которые НЕ чиним сразу" plus the `UP042` finding plus the coverage-margin observation is addressed by exactly one task here. The three things deliberately *not* in scope (httpx pool, refresh swallowing, token-blob design) are explicitly listed in "After all seven tasks land" — not silently dropped.

**Placeholder scan** — every "Run:" line has the exact command; every test file is fully written out; every edit shows the old and new code blocks. Issue/PR templates use `<issue-number>` as a literal placeholder for the runtime value but the surrounding command shows where to substitute. No "TBD", no "similar to Task N", no "handle edge cases."

**Type/name consistency** — `tests/test_dto_enum_serialization.py` imports match the actual public surface of `nalogo.dto.income`. The respx base URL `https://lknpd.nalog.ru/api/v1` matches `Client._http_client.base_url` (`client.py:61`). `payment_type().table()/favorite()`, `tax().get()/history()/payments()`, `user().get()` all match the actual method names verified in `nalogo/payment_type.py`, `nalogo/tax.py`, `nalogo/user.py`.
