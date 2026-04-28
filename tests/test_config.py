import pytest

from todo.config import DEFAULT_CACHE_NAMESPACE, DEFAULT_CLIENT_ID, load_auth_config


def test_load_auth_config_uses_wam_and_shared_cache_by_default(monkeypatch):
    monkeypatch.delenv("TODO_CLIENT_ID", raising=False)
    monkeypatch.delenv("TODO_AUTH_MODE", raising=False)
    monkeypatch.delenv("MTG_AUTH_CACHE_NAMESPACE", raising=False)
    monkeypatch.delenv("MTG_AUTH_ACCOUNT_HINT", raising=False)

    config = load_auth_config()

    assert config.mode.value == "wam"
    assert config.cache_namespace == DEFAULT_CACHE_NAMESPACE
    assert config.client_id == DEFAULT_CLIENT_ID
    assert config.account_hint is None


def test_load_auth_config_uses_shared_account_hint(monkeypatch):
    monkeypatch.setenv("TODO_CLIENT_ID", "11111111-1111-1111-1111-111111111112")
    monkeypatch.setenv("MTG_AUTH_ACCOUNT_HINT", "thomas@midtowntg.com")

    config = load_auth_config()

    assert config.account_hint == "thomas@midtowntg.com"


def test_load_auth_config_rejects_placeholder_client_id(monkeypatch):
    monkeypatch.setenv("TODO_CLIENT_ID", "11111111-1111-1111-1111-111111111111")

    with pytest.raises(RuntimeError, match="TODO_CLIENT_ID must be set"):
        load_auth_config()
