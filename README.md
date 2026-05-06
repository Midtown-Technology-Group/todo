# Todo

Windows-first Python Typer CLI for Microsoft To Do.

This is Midtown's Python command-line tool for working with Microsoft To Do
through Microsoft Graph and the shared Midtown WAM auth stack. It is not the
upstream .NET `todo-cli` application, although this repository still carries
some inherited material and attribution from that project.

Project site: <https://midtown-technology-group.github.io/todo/>

## What This Is

- A Python package named `todo`, exposed as the `todo` console script.
- A Typer/Rich CLI for listing, adding, completing, and removing To Do items.
- A Windows-first operator tool that uses `mtg-microsoft-auth` for shared Graph
  authentication and token cache reuse across Midtown tools.
- A local wrapper-friendly app; `.\invoke.ps1` runs the repo virtualenv with the
  correct source path.

## What This Is Not

- It is not the upstream .NET `mehmetseckin/todo-cli` app.
- It is not a general-purpose cross-platform packaged desktop client.
- It does not yet expose every Microsoft To Do task field. Richer fields such
  as due dates, My Day, reminders, repeats, file attachments, and notes are
  tracked for CLI support in
  <https://github.com/Midtown-Technology-Group/todo/issues/3>.

## Setup

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .[dev]
```

## Auth

Set these environment variables before running the CLI:

- `TODO_CLIENT_ID` (optional, defaults to the shared Midtown public client)
- `TODO_TENANT_ID` (optional, defaults to `common`)
- `TODO_SCOPES` (optional, defaults to `Tasks.Read`)
- `TODO_AUTH_MODE` (optional, defaults to `wam`)
- `TODO_ALLOW_BROKER` (optional, defaults to `true`)
- `MTG_AUTH_ACCOUNT_HINT` (optional, preferred UPN when multiple accounts are
  present in WAM)

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
