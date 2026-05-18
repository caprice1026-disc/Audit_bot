from __future__ import annotations

from dataclasses import dataclass, field


DANGEROUS_PERMISSION_KEYS = {
    "ADMINISTRATOR",
    "MANAGE_ROLES",
    "MANAGE_CHANNELS",
    "MANAGE_WEBHOOKS",
    "MENTION_EVERYONE",
    "CREATE_INSTANT_INVITE",
    "VIEW_CHANNEL",
    "SEND_MESSAGES",
    "MANAGE_MESSAGES",
}


@dataclass(slots=True)
class RoleSnapshot:
    role_id: str
    name: str
    permissions: set[str]
    is_everyone: bool = False


@dataclass(slots=True)
class CategorySnapshot:
    category_id: str
    name: str
    overwrite_fingerprint: str
    overwrite_permissions: set[str] = field(default_factory=set)


@dataclass(slots=True)
class ChannelSnapshot:
    channel_id: str
    name: str
    permissions_synced: bool
    overwrite_fingerprint: str
    overwrite_permissions: set[str] = field(default_factory=set)
    category: CategorySnapshot | None = None


@dataclass(slots=True)
class GuildSnapshot:
    guild_id: str
    roles: list[RoleSnapshot] = field(default_factory=list)
    channels: list[ChannelSnapshot] = field(default_factory=list)


@dataclass(slots=True)
class Finding:
    finding_key: str
    severity: str
    category: str
    summary: str


@dataclass(slots=True)
class AuditResult:
    findings: list[Finding]

    @property
    def total_findings(self) -> int:
        return len(self.findings)
