from __future__ import annotations

from app.audit.models import ChannelSnapshot, Finding


def check_channel_sync(channels: list[ChannelSnapshot]) -> list[Finding]:
    findings: list[Finding] = []
    for channel in channels:
        if channel.category is None:
            continue
        if channel.permissions_synced:
            continue
        findings.append(
            Finding(
                finding_key="channel.desynced_from_category",
                severity="medium",
                category="channel",
                summary=(
                    f"{channel.name} はカテゴリ {channel.category.name} と権限同期されていません。"
                ),
            )
        )
    return findings
