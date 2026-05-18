from app.audit.models import CategorySnapshot, ChannelSnapshot, GuildSnapshot, RoleSnapshot
from app.audit.runner import run_prototype_audit


def test_prototype_audit_detects_role_and_channel_findings() -> None:
    category = CategorySnapshot(
        category_id="10",
        name="運営",
        overwrite_fingerprint="cat-a",
        overwrite_permissions={"VIEW_CHANNEL"},
    )
    channels = [
        ChannelSnapshot(
            channel_id="100",
            name="staff-room",
            permissions_synced=False,
            overwrite_fingerprint="chan-x",
            overwrite_permissions={"VIEW_CHANNEL", "SEND_MESSAGES"},
            category=category,
        )
    ]
    roles = [
        RoleSnapshot(
            role_id="1",
            name="Server Admin",
            permissions={"ADMINISTRATOR"},
            is_everyone=False,
        ),
        RoleSnapshot(
            role_id="2",
            name="@everyone",
            permissions={"CREATE_INSTANT_INVITE"},
            is_everyone=True,
        ),
    ]
    result = run_prototype_audit(GuildSnapshot(guild_id="g1", roles=roles, channels=channels))

    keys = [finding.finding_key for finding in result.findings]
    assert "channel.desynced_from_category" in keys
    assert "role.has_administrator" in keys
    assert "role.everyone_has_dangerous_permission" in keys
    assert result.total_findings == 3


def test_channel_desync_severity_becomes_high_when_dangerous_permission_diff_exists() -> None:
    category = CategorySnapshot(
        category_id="20",
        name="管理",
        overwrite_fingerprint="cat-b",
        overwrite_permissions={"VIEW_CHANNEL"},
    )
    channels = [
        ChannelSnapshot(
            channel_id="200",
            name="incident-room",
            permissions_synced=False,
            overwrite_fingerprint="chan-y",
            overwrite_permissions={"VIEW_CHANNEL", "MANAGE_WEBHOOKS"},
            category=category,
        )
    ]
    result = run_prototype_audit(GuildSnapshot(guild_id="g2", roles=[], channels=channels))

    finding = next(f for f in result.findings if f.finding_key == "channel.desynced_from_category")
    assert finding.severity == "high"


def test_synced_channels_do_not_create_findings() -> None:
    category = CategorySnapshot(
        category_id="30",
        name="公開",
        overwrite_fingerprint="cat-c",
        overwrite_permissions={"VIEW_CHANNEL"},
    )
    channels = [
        ChannelSnapshot(
            channel_id="300",
            name="announcements",
            permissions_synced=True,
            overwrite_fingerprint="chan-z",
            overwrite_permissions={"VIEW_CHANNEL"},
            category=category,
        )
    ]
    result = run_prototype_audit(GuildSnapshot(guild_id="g3", roles=[], channels=channels))
    assert result.total_findings == 0
