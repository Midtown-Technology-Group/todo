# Todo

Windows-first Python tool for Microsoft To Do.

Project site: <https://midtown-technology-group.github.io/todo/>

## Setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

## Auth

Set these environment variables before running the CLI:

- `TODO_CLIENT_ID`
- `TODO_TENANT_ID`
- `TODO_SCOPES` (optional, defaults to `Tasks.Read`)
- `TODO_AUTH_MODE` (optional, defaults to `wam`)
- `TODO_ALLOW_BROKER` (optional, defaults to `true`)

`todo` now shares the Midtown Graph token cache with the other toys by default, so a successful WAM sign-in in one toy should usually carry across the rest. If you ever want an isolated cache for testing, set `MTG_AUTH_CACHE_NAMESPACE` explicitly. If your broker has multiple signed-in Microsoft accounts, set `MTG_AUTH_ACCOUNT_HINT` to the preferred UPN so silent reuse targets the right account before prompting.

`todo` now starts with `Tasks.Read` as its default scope. Set `TODO_SCOPES=Tasks.Read,Tasks.ReadWrite` when you are ready to grant write access for add/complete/remove flows.

`Tasks.ReadWrite` is the single write unlock for this tool. Microsoft currently lists the delegated scope as user-consentable, but tenant policy can still force an approval flow in practice, so treat live consent behavior as the real gate.

## Usage

```powershell
.\invoke.ps1 list --all
.\invoke.ps1 add item "Ship feature" --list Projects --star
.\invoke.ps1 complete 123
.\invoke.ps1 remove item --completed --all
```

## License

GPL-3.0-or-later.

This repo also includes inherited material derived from `mehmetseckin/todo-cli`
under MIT; see `NOTICE`.
