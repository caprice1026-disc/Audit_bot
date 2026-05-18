from __future__ import annotations

from app.audit.models import DANGEROUS_PERMISSION_KEYS, Finding, RoleSnapshot


def check_role_permissions(roles: list[RoleSnapshot]) -> list[Finding]:
    findings: list[Finding] = []
    for role in roles:
        if "ADMINISTRATOR" in role.permissions:
            findings.append(
                Finding(
                    finding_key="role.has_administrator",
                    severity="high",
                    category="role",
                    summary=f"{role.name} に管理者権限が付与されています。",
                )
            )

        if role.is_everyone:
            risky = sorted(role.permissions.intersection(DANGEROUS_PERMISSION_KEYS))
            for permission_name in risky:
                findings.append(
                    Finding(
                        finding_key="role.everyone_has_dangerous_permission",
                        severity="high",
                        category="role",
                        summary=f"@everyone に危険権限 {permission_name} が付与されています。",
                    )
                )
    return findings
