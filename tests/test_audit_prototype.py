from app.audit.models import CategorySnapshot, ChannelSnapshot, GuildSnapshot, RoleSnapshot
from app.audit.runner import run_prototype_audit


def test_prototype_audit_detects_role_and_channel_findings() -> None:
    category = CategorySnapshot(category_id="10", name="運営", overwrite_fingerprint="cat-a")
    channels = [
        ChannelSnapshot(
            channel_id="100",
            name="staff-room",
            permissions_synced=False,
            overwrite_fingerprint="chan-x",
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
