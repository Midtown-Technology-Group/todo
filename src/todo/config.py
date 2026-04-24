from __future__ import annotations

import os

from mtg_microsoft_auth import AuthConfig, AuthMode


def _env_bool(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_auth_config() -> AuthConfig:
    scopes = os.environ.get("TODO_SCOPES", "Tasks.Read").split(",")
    return AuthConfig(
        client_id=os.environ.get("TODO_CLIENT_ID", "11111111-1111-1111-1111-111111111111"),
        tenant_id=os.environ.get("TODO_TENANT_ID", "common"),
        scopes=[scope.strip() for scope in scopes if scope.strip()],
        mode=AuthMode(os.environ.get("TODO_AUTH_MODE", "auto")),
        cache_namespace="todo",
        allow_broker=_env_bool("TODO_ALLOW_BROKER", True),
    )


def has_write_scope() -> bool:
    scopes = {
        scope.strip()
        for scope in os.environ.get("TODO_SCOPES", "Tasks.Read").split(",")
        if scope.strip()
    }
    return "Tasks.ReadWrite" in scopes
