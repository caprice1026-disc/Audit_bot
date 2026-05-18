from __future__ import annotations

import importlib
import os


class MissingTokenError(RuntimeError):
    """DISCORD_BOT_TOKEN が未設定の場合に送出する。"""


def create_bot_from_env() -> object:
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        raise MissingTokenError("DISCORD_BOT_TOKEN が設定されていません。")

    discord = importlib.import_module("discord")
    intents = discord.Intents.default()
    intents.guilds = True
    client = discord.Client(intents=intents)
    client.run(token)
    return client
