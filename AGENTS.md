# Midtown Todo agent guide

This Windows-first Python CLI manages personal Microsoft To Do tasks and reads Planner data. Read [README.md](README.md) for the command contract and [pyproject.toml](pyproject.toml) for dependencies and pytest configuration. Implementation lives in `src/`, tests in `tests/`, and Windows packaging under `packaging/windows/`.

## Setup and checks

Follow the README's virtual environment setup, then install `-e .[dev]` using that environment's Python. The project declares pytest and selects `tests/`; run that suite with the environment's Python (`.\.venv\Scripts\python.exe -m pytest`) after relevant code changes. Keep authentication mocked for ordinary tests rather than using personal accounts.

## Authentication and operation boundaries

Retain the shared `mtg-microsoft-auth` cache contract, WAM defaults, account hint, and optional isolated `MTG_AUTH_CACHE_NAMESPACE`. Do not commit cache files or tokens. Default `Tasks.Read` remains read-only; `Tasks.ReadWrite` unlocks writes but tenant consent behavior must still be verified. Planner commands remain read-only and separate from personal To Do commands.

Add/update/complete/remove and attachment commands change real user data; require the exact authorized scope and read back the affected items. Preserve recurrence/due-date rules, Graph/Windows timezone handling, the under-3-MB attachment limit, and clear rejection of unsupported My Day changes before mutation.

## Release

[.github/workflows/release-msi.yml](.github/workflows/release-msi.yml) builds MSI assets and notifies `mtg-winget` on published releases. Source tests are separate from packaging, asset upload, feed update, and installed-client proof. Preserve inherited MIT attribution in `NOTICE` alongside this project's GPL-3.0-or-later license.
