from __future__ import annotations

from app.audit.checks.channels import check_channel_sync
from app.audit.checks.roles import check_role_permissions
from app.audit.models import AuditResult, GuildSnapshot


def run_prototype_audit(guild: GuildSnapshot) -> AuditResult:
    findings = []
    findings.extend(check_channel_sync(guild.channels))
    findings.extend(check_role_permissions(guild.roles))
    return AuditResult(findings=findings)
