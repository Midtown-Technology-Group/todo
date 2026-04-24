# Todo

Windows-first Python tool for Microsoft To Do.

## Setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
.\.venv\Scripts\python.exe -m pip install -e ..\midtown-org-scan\microsoft-auth
```

## Auth

Set these environment variables before running the CLI:

- `TODO_CLIENT_ID`
- `TODO_TENANT_ID`
- `TODO_SCOPES` (optional, defaults to `Tasks.Read`)
- `TODO_AUTH_MODE` (optional, defaults to `auto`)
- `TODO_ALLOW_BROKER` (optional, defaults to `true`)

`todo` now starts in read-only mode by default. Set `TODO_SCOPES=Tasks.Read,Tasks.ReadWrite` only when you are ready to grant write access for add/complete/remove flows.

## Usage

```powershell
.\invoke.ps1 list --all
.\invoke.ps1 add item "Ship feature" --list Projects --star
.\invoke.ps1 complete 123
.\invoke.ps1 remove item --completed --all
```
