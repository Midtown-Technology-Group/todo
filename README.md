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
.\invoke.ps1 planner plans
.\invoke.ps1 planner tasks --plan-id <planner-plan-id>
.\invoke.ps1 add item "Ship feature" --list Projects --star
.\invoke.ps1 add item "Renew pass GPG key/subkeys" --star --due 2027-01-15 --remind 2027-01-15T09:00:00 --note "Verify key fingerprint" --repeat yearly --time-zone "Eastern Standard Time"
.\invoke.ps1 update item <item-id> --due 2027-01-15 --note "Updated context"
.\invoke.ps1 attach file <item-id> .\evidence.pdf
.\invoke.ps1 complete 123
.\invoke.ps1 remove item --completed --all
```

Task creation and updates support due dates, reminders, plain-text notes, and
`daily`, `weekly`, `monthly`, or `yearly` recurrence. Recurrence needs a due
date when creating a task; updates can reuse the task's existing due date.
`--time-zone` accepts the Graph/Windows time-zone name and defaults to `UTC`.

The `attach file` command uses the Microsoft Graph v1.0 small-attachment API
and accepts files under 3 MB. Larger Graph upload sessions are not implemented
yet, and the CLI reports that limit without uploading the file.

Microsoft Graph v1.0 does not expose My Day membership for Microsoft To Do
tasks. `--my-day` and `--no-my-day` therefore fail clearly before creating or
updating a task; use a Microsoft To Do client to change My Day membership.

With `--output json`, list results include due, reminder, note/body, recurrence,
and attachment-presence fields. Successful add, update, and attachment commands
retain the existing `status` and `message` keys and add the created or updated
resource under `data` for scripts.

Planner commands are read-only and use the same `TODO_SCOPES=Tasks.Read`
baseline as personal To Do reads. They intentionally live under `planner` so
project tasks do not masquerade as personal To Do items.

## License

GPL-3.0-or-later.

This repo also includes inherited material derived from `mehmetseckin/todo-cli`
under MIT; see `NOTICE`.
