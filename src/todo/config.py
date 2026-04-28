from __future__ import annotations

import os

from mtg_microsoft_auth import AuthConfig, AuthMode

DEFAULT_CACHE_NAMESPACE = "mtg-shared-microsoft-auth"
DEFAULT_CLIENT_ID = "e02be6f7-063a-46a6-b2cc-109d5f51055c"
PLACEHOLDER_CLIENT_ID = "11111111-1111-1111-1111-111111111111"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_auth_config() -> AuthConfig:
    scopes = os.environ.get("TODO_SCOPES", "Tasks.Read").split(",")
    return AuthConfig(
        client_id=_required_client_id(),
        tenant_id=os.environ.get("TODO_TENANT_ID", "common"),
        scopes=[scope.strip() for scope in scopes if scope.strip()],
        mode=AuthMode(os.environ.get("TODO_AUTH_MODE", "wam")),
        cache_namespace=os.environ.get("MTG_AUTH_CACHE_NAMESPACE", DEFAULT_CACHE_NAMESPACE),
        account_hint=os.environ.get("MTG_AUTH_ACCOUNT_HINT"),
        allow_broker=_env_bool("TODO_ALLOW_BROKER", True),
    )


def has_write_scope() -> bool:
    scopes = {
        scope.strip()
        for scope in os.environ.get("TODO_SCOPES", "Tasks.Read").split(",")
        if scope.strip()
    }
    return "Tasks.ReadWrite" in scopes


def _required_client_id() -> str:
    client_id = os.environ.get("TODO_CLIENT_ID", DEFAULT_CLIENT_ID).strip()
    if not client_id or client_id == PLACEHOLDER_CLIENT_ID:
        raise RuntimeError(
            "TODO_CLIENT_ID must be set to a real Entra public client application ID or omitted to use the shared Midtown app. "
            "Refusing to use the placeholder client ID."
        )
    return client_id
