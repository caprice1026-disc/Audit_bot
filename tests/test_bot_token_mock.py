import types

import pytest

from app.bot import MissingTokenError, create_bot_from_env


class DummyClient:
    def __init__(self, intents: object) -> None:
        self.intents = intents
        self.received_token: str | None = None

    def run(self, token: str) -> None:
        self.received_token = token


class DummyIntents:
    guilds = False

    @classmethod
    def default(cls) -> "DummyIntents":
        return cls()


def test_create_bot_from_env_raises_when_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISCORD_BOT_TOKEN", raising=False)
    with pytest.raises(MissingTokenError):
        create_bot_from_env()


def test_create_bot_from_env_uses_mocked_discord(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISCORD_BOT_TOKEN", "dummy-token")

    created_clients: list[DummyClient] = []

    def client_factory(*, intents: object) -> DummyClient:
        client = DummyClient(intents=intents)
        created_clients.append(client)
        return client

    dummy_module = types.SimpleNamespace(Intents=DummyIntents, Client=client_factory)
    monkeypatch.setattr("importlib.import_module", lambda name: dummy_module)

    client = create_bot_from_env()

    assert isinstance(client, DummyClient)
    assert created_clients[0].received_token == "dummy-token"
    assert created_clients[0].intents.guilds is True
