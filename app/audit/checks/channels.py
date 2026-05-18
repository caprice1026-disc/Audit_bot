from __future__ import annotations

from app.audit.models import DANGEROUS_PERMISSION_KEYS, ChannelSnapshot, Finding


def _has_dangerous_permission_diff(channel: ChannelSnapshot) -> bool:
    """カテゴリとの差分に危険権限が含まれるかを返す。"""
    if channel.category is None:
        return False
    channel_permissions = set(channel.overwrite_permissions)
    category_permissions = set(channel.category.overwrite_permissions)
    permission_diff = channel_permissions.symmetric_difference(category_permissions)
    return bool(permission_diff.intersection(DANGEROUS_PERMISSION_KEYS))


def check_channel_sync(channels: list[ChannelSnapshot]) -> list[Finding]:
    findings: list[Finding] = []
    for channel in channels:
        if channel.category is None:
            continue
        if channel.permissions_synced:
            continue

        severity = "high" if _has_dangerous_permission_diff(channel) else "medium"
        findings.append(
            Finding(
                finding_key="channel.desynced_from_category",
                severity=severity,
                category="channel",
                summary=(
                    f"{channel.name} はカテゴリ {channel.category.name} と権限同期されていません。"
                ),
            )
        )
    return findings
