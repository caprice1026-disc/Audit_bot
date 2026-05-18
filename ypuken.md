Discord Security Auditor Bot

要件定義書兼設計書 v0.1

1. 概要

本Botは、Discordサーバーに導入され、Discord APIおよび discord.py を利用してサーバーのセキュリティ状態を監査するBotである。

主な目的は、サーバー管理者または許可されたロールを持つユーザーが、以下の状態を非公開で確認できるようにすること。

ロール権限の過剰付与

@everyone の危険権限

チャンネル権限の問題

カテゴリとチャンネルの権限非同期

招待リンクのリスク

Webhookのリスク

AutoMod設定の不足

監査ログ上の危険な変更履歴


初期フェーズでは読み取り専用の監査Botとして実装する。
自動修正は後続フェーズで /remediate 系コマンドとして分離する。


---

2. 開発方針

2.1 技術スタック

項目	採用

言語	Python
Discordライブラリ	discord.py
コマンド方式	Slash Command
機能管理	Cogs / Extensions
DB	SQLiteから開始、PostgreSQL移行可能な設計
ORM	SQLAlchemy 2.x
マイグレーション	Alembic
設定	YAML + DB
多言語対応	locales/ja.yml, locales/en.yml
初期レポート形式	Discord Embed


discord.py のCogは、コマンド・リスナー・状態を1つのクラスにまとめる仕組みで、公式ドキュメントでもExtensionsとの併用が想定されている。Extensionsは setup コルーチンをエントリポイントにして Bot.load_extension() で読み込む形式である。


---

3. フェーズ定義

Phase 1: 読み取り専用監査

初期実装対象。

/audit 系コマンド

/config 系コマンド

/audit doctor

ロールベース実行権限

監査結果のDB保存

監査結果のEmbed表示

多言語対応

allowlist対応

監査ログ要約保存

チャンネル非同期検出


このフェーズでは、BotはDiscord上の設定を変更しない。

Phase 2: 修正支援

後続実装。

修正案の詳細化

dry-run対応

修正対象のプレビュー

/remediate channel-sync dry_run:true


Phase 3: 自動修正

後続実装。

明示確認付きの修正

/remediate channel-sync confirm:true

Invite削除

Webhook削除

AutoMod作成補助


Phase 3では追加権限が必要になる可能性があるため、Phase 1のBot権限とは分離する。


---

4. スコープ

4.1 初期スコープ

監査対象

カテゴリ	内容

Guild	サーバー設定
Role	ロール権限
@everyone	全員ロールの危険権限
Channel	チャンネル権限
Channel Sync	カテゴリとチャンネルの権限非同期
Invite	招待リンク
Webhook	Webhook
AutoMod	Auto Moderation
Audit Log	直近の管理操作履歴
Bot	Bot自身の権限状態


初期対象外

メッセージ本文の監査

DM監査

ユーザーアカウント自動操作

self-bot方式

自動修正

公開チャンネルへの監査結果投稿

Webダッシュボード

PDF / HTML / Markdown / JSONレポート出力


ただし、Markdown / JSON / HTML / PDF出力は将来拡張可能な設計にする。


---

5. 権限・Intent設計

5.1 Bot権限

初期実装は拡張監査モード込みで以下の権限を要求する。

Use Application Commands
View Channels
View Audit Log
Manage Guild
Manage Webhooks

権限	用途

Use Application Commands	Slash Command実行
View Channels	チャンネル構造・権限確認
View Audit Log	監査ログ確認
Manage Guild	AutoMod設定確認
Manage Webhooks	Webhook一覧確認


Discordの権限はビットフラグで管理され、ADMINISTRATOR は全権限を許可し、チャンネル権限上書きをバイパスする。権限上書きはチャンネル単位で適用され、カテゴリ同期の判定もDiscordの権限仕様に含まれている。

5.2 Botに付与しない権限

Phase 1では以下を付与しない。

Administrator
Manage Channels
Manage Roles
Kick Members
Ban Members
Moderate Members

理由は、初期実装が読み取り専用であるため。
特に Administrator は監査Bot自身が巨大なリスクになるため、原則として使わない。

5.3 将来の修正用権限

Phase 2 / Phase 3で修正機能を追加する場合、別の招待URLまたは別設定として以下を検討する。

Manage Channels
Manage Roles
Manage Webhooks
Manage Guild

Manage Channels はチャンネル権限同期の自動修正に必要になる想定。

5.4 Intents

初期実装では以下を使用する。

intents = discord.Intents.default()
intents.guilds = True

5.5 初期では使わないIntent

Guild Members Intent
Message Content Intent
Presence Intent

メッセージ本文監査は行わないため、Message Content Intent は不要。
強権限ロールを実際に誰が持っているか、休眠管理者検出などを行う場合のみ、将来的に Guild Members Intent を検討する。


---

6. Slash Command設計

6.1 監査コマンド

/audit summary
/audit roles
/audit channels
/audit permissions
/audit invites
/audit webhooks
/audit logs days:7
/audit automod
/audit report
/audit channel-sync
/audit channel-sync category:<category>
/audit channel-sync channel:<channel>
/audit doctor

6.2 設定コマンド

/config locale set locale:ja|en
/config locale show

/config access add-role role:@Role
/config access remove-role role:@Role
/config access add-user user:@User
/config access remove-user user:@User
/config access list

/config allowlist add
/config allowlist remove
/config allowlist list

/config audit-mode set mode:basic|standard|extended
/config retention set days:<days>
/config profile set profile:auto|small|medium|large|enterprise

6.3 将来の修正コマンド

/remediate channel-sync dry_run:true
/remediate channel-sync channel:<channel> dry_run:true
/remediate channel-sync channel:<channel> confirm:true


---

7. Interaction応答仕様

監査コマンドは処理が重くなるため、必ず defer してから結果を followup で返す。

await interaction.response.defer(ephemeral=True, thinking=True)

discord.py では thinking=True にした場合、後続で Interaction.followup を送る必要がある。Interaction tokenは15分有効であり、ephemeral=True は応答をコマンド実行者だけに見せる用途である。

7.1 応答可視性

初期実装では監査結果は常に ephemeral。

report_visibility = ephemeral

visibility:channel は初期では実装しない。
セキュリティ診断結果を公開チャンネルに出すと、弱点の回覧板になる。地獄町内会。


---

8. Cogs設計

8.1 Cogs一覧

app/cogs/
  audit.py
  config.py
  health.py
  admin.py

Cog	責務

audit.py	/audit 系コマンド
config.py	/config 系コマンド
health.py	/ping, /status
admin.py	Cog reloadなど開発・運用者向け


8.2 Cogの責務

CogにはDiscordとの入出力のみを書く。
監査ロジックはCogに書かない。

AuditCog
  ↓
AccessControlService
  ↓
AuditRunner
  ↓
checks/*
  ↓
AllowlistService
  ↓
ScoreCalculator
  ↓
AuditRepository
  ↓
EmbedFormatter

8.3 拡張読み込み

await bot.load_extension("app.cogs.audit")
await bot.load_extension("app.cogs.config")
await bot.load_extension("app.cogs.health")


---

9. 監査モード

9.1 basic

- サーバー設定
- ロール権限
- @everyone
- チャンネル権限
- チャンネル非同期

9.2 standard

デフォルト。

- basic
- Invite
- Webhook
- AutoMod

9.3 extended

- standard
- Audit Log
- 直近の危険操作
- 権限変更の履歴
- Webhook / Invite / Role / Channel変更履歴

Discordの監査ログは VIEW_AUDIT_LOG 権限が必要で、取得できる監査ログエントリは45日間保存される。取得APIでは1回あたりの limit が1〜100の範囲で指定される。


---

10. 監査項目

10.1 Guild監査

Finding Key:

guild.mfa_disabled
guild.verification_level_low
guild.explicit_content_filter_disabled
guild.community_disabled
guild.safety_alerts_channel_missing

見る内容:

MFA要求状態

認証レベル

露骨コンテンツフィルタ

Community設定

Safety alerts channel


10.2 Role監査

Finding Key:

role.has_administrator
role.has_manage_roles
role.has_manage_channels
role.has_manage_webhooks
role.has_mention_everyone
role.everyone_has_dangerous_permission
role.bot_role_too_powerful

見る内容:

Administrator

Manage Roles

Manage Channels

Manage Webhooks

Mention Everyone

@everyone の危険権限

Botロールの過剰権限


10.3 Channel監査

Finding Key:

channel.desynced_from_category
channel.everyone_can_view
channel.everyone_can_send
channel.everyone_can_create_invite
channel.everyone_can_mention_everyone
channel.role_has_manage_webhooks
channel.role_has_manage_channels

見る内容:

カテゴリ非同期

@everyone の閲覧権限

@everyone の送信権限

Invite作成権限

everyoneメンション権限

Webhook管理権限

チャンネル管理権限


10.3.1 チャンネル非同期監査

このBotの重要機能として、カテゴリと子チャンネルの権限非同期を検出する。

Discordでは、子チャンネルの権限上書きが親カテゴリと一致している場合に「同期されている」と扱われ、親カテゴリの変更が同期済み子チャンネルに反映される。

検出対象:

- categoryを持つテキストチャンネル
- categoryを持つボイスチャンネル
- categoryを持つフォーラム等、対応可能なGuildChannel

判定:

channel.permissions_synced == False

追加で、親カテゴリと子チャンネルのpermission overwritesを比較し、差分を人間向けに表示する。

危険度を上げる権限:

VIEW_CHANNEL
SEND_MESSAGES
MANAGE_CHANNELS
MANAGE_WEBHOOKS
MENTION_EVERYONE
MANAGE_MESSAGES
CREATE_INSTANT_INVITE

出力例:

🟡 注意: #event-staff が親カテゴリ「運営」と権限同期されていません

何が問題？
このチャンネルだけ、親カテゴリと違う権限設定になっています。

なぜ危ない？
親カテゴリ側で権限を修正しても、このチャンネルには反映されません。

差分:
- @everyone: チャンネルを見る権限が親カテゴリでは拒否、チャンネルでは未設定
- Event Staff: メッセージ送信が親カテゴリでは許可、チャンネルでは拒否

おすすめ対応:
意図した例外でなければ、チャンネル権限をカテゴリと同期してください。
意図した例外なら、理由と期限を付けて例外リストに登録してください。

10.4 Invite監査

Finding Key:

invite.no_expiration
invite.unlimited_uses
invite.targets_sensitive_channel
invite.created_by_high_risk_user

見る内容:

期限なしInvite

使用回数無制限Invite

センシティブチャンネルへのInvite

危険ロール保持者によるInvite作成


10.5 Webhook監査

Finding Key:

webhook.exists
webhook.exists_in_public_channel
webhook.too_many_in_channel
webhook.created_recently

WebhookはBot認証なしでもチャンネルへ投稿できる仕組みであり、チャンネルWebhook一覧・Guild Webhook一覧の取得には MANAGE_WEBHOOKS 権限が必要である。

見る内容:

Webhook存在数

公開チャンネル内Webhook

チャンネルごとのWebhook過多

最近作成されたWebhook


初期実装では削除しない。
Webhook URLやtokenは保存・表示しない。

10.6 AutoMod監査

Finding Key:

automod.disabled
automod.no_mention_spam_rule
automod.no_keyword_rule
automod.rule_disabled
automod.exemptions_too_broad

Auto Moderationリソースへのアクセスには MANAGE_GUILD 権限が必要であり、GuildのAutoModルール一覧取得も MANAGE_GUILD を要求する。

見る内容:

AutoModルールの有無

メンションスパム対策

キーワード対策

無効化されたルール

例外ロール・例外チャンネルの広すぎる設定


10.7 Audit Log監査

Finding Key:

auditlog.recent_permission_change
auditlog.recent_role_change
auditlog.recent_channel_permission_change
auditlog.recent_webhook_change
auditlog.recent_invite_change
auditlog.unusual_admin_activity

見る内容:

直近のロール変更

直近のチャンネル権限変更

直近のWebhook作成・変更・削除

直近のInvite作成・変更・削除

不自然な管理者操作



---

11. 非エンジニア向け出力仕様

各Findingは必ず以下を持つ。

1. 何が問題か
2. なぜ危ないか
3. どう直すか
4. 影響範囲
5. 根拠

表示例

🔴 緊急: 管理者権限を持つロールがあります

何が問題？
「Server Admin」ロールに管理者権限があります。

なぜ危ない？
この権限を持つアカウントが乗っ取られると、チャンネル削除、ロール変更、Bot追加などが可能になります。

どう直す？
管理者権限は最小限のロールだけに限定してください。日常運用には個別権限を使うことを推奨します。

影響範囲:
- Role: Server Admin


---

12. レポート仕様

12.1 初期レポート形式

Discord Embedのみ。

Discord Embedには、title 256文字、description 4096文字、field最大25個、field value 1024文字、1メッセージ内の全Embed合計6000文字などの制限がある。制限超過時はBad Requestになるため、表示側で要約とページングを行う。

12.2 /audit summary

表示内容:

- スコア
- 監査モード
- Critical / High / Medium / Low / Info 件数
- 上位5件の重要Finding
- 一部失敗したカテゴリ
- 詳細コマンドへの案内

12.3 カテゴリ別コマンド

/audit channels
/audit roles
/audit invites
/audit webhooks
/audit automod
/audit logs

カテゴリ別コマンドでは、そのカテゴリのFindingを優先度順に表示する。

12.4 ページング方針

初期実装ではボタンUIによるページングは必須としない。
まずは以下の方針で実装する。

/audit summary:
  上位5件のみ

/audit <category>:
  カテゴリ別に上限件数まで表示

将来的に discord.ui.View を使ったページングを追加する。


---

13. アクセス制御

13.1 基本方針

監査コマンドは、許可されたロールまたはユーザーのみ実行できる。

Discord側のApplication Command権限だけに依存せず、Bot内でDB設定を使って判定する。

discord.py の app_commands.check はInteractionを受け取るpredicateでコマンド実行可否を判定でき、has_role / has_any_role はロール名またはロールIDで判定できる。has_permissions はDiscord側のApplication Command権限ではなく、プログラム内で評価されるチェックである。

13.2 判定順

1. Guild owner
2. allowed_user_ids
3. allowed_role_ids
4. bypass_permissions
5. deny

bypass_permissions

初期値:

administrator
manage_guild

ただし、最終的には /config access による明示許可を推奨する。

13.3 保存単位

ロール名ではなく role_id を保存する。
ユーザー名ではなく user_id を保存する。

DiscordのSnowflake IDは最大64bitサイズであり、HTTP APIではオーバーフロー防止のため文字列として返されるため、DB上でも文字列として扱う。


---

14. 設定仕様

14.1 設定の優先順位

1. guild_settings.config_overrides_json
2. server profile
3. config/audit_rules.yml defaults
4. コード内の安全な初期値

14.2 サーバープロファイル

初期ではインターフェースのみ実装し、後で動的切替を拡張する。

auto
small
medium
large
enterprise

想定分類:

small:
  member_count < 100

medium:
  100 <= member_count < 1000

large:
  1000 <= member_count < 10000

enterprise:
  10000 <= member_count

14.3 audit_rules.yml

defaults:
  thresholds:
    administrator_roles:
      high: 3
      critical: 5

    desynced_channels:
      high: 10
      critical: 30

    permanent_invites:
      high: 1
      critical: 3

  risk_weights:
    VIEW_CHANNEL: 10
    SEND_MESSAGES: 6
    CREATE_INSTANT_INVITE: 6
    MENTION_EVERYONE: 8
    MANAGE_CHANNELS: 9
    MANAGE_ROLES: 10
    MANAGE_WEBHOOKS: 10
    ADMINISTRATOR: 15

profiles:
  small:
    member_count_max: 99
    thresholds:
      administrator_roles:
        high: 3
        critical: 5

  medium:
    member_count_min: 100
    member_count_max: 999
    thresholds:
      administrator_roles:
        high: 3
        critical: 5

  large:
    member_count_min: 1000
    member_count_max: 9999
    thresholds:
      administrator_roles:
        high: 2
        critical: 4

  enterprise:
    member_count_min: 10000
    thresholds:
      administrator_roles:
        high: 1
        critical: 3


---

15. DB設計

15.1 方針

初期DBはSQLite

将来PostgreSQLに移行可能な設計

Discord IDはすべて TEXT

JSON系カラムはSQLiteでは TEXT

PostgreSQL移行時は JSONB 化可能

日時はISO8601文字列またはDB側DateTimeで統一

監査ログのraw payloadは初期では保存しない


15.2 テーブル一覧

guild_settings
guild_access_roles
guild_access_users
audit_runs
audit_findings
audit_log_entries
allowlist_entries


---

15.3 guild_settings

CREATE TABLE guild_settings (
    guild_id TEXT PRIMARY KEY,

    locale TEXT NOT NULL DEFAULT 'ja',
    default_audit_mode TEXT NOT NULL DEFAULT 'standard',
    server_profile TEXT NOT NULL DEFAULT 'auto',

    log_retention_days INTEGER NOT NULL DEFAULT 90,
    store_audit_logs BOOLEAN NOT NULL DEFAULT 1,
    store_raw_payload BOOLEAN NOT NULL DEFAULT 0,

    report_format TEXT NOT NULL DEFAULT 'embed',
    report_visibility TEXT NOT NULL DEFAULT 'ephemeral',

    config_overrides_json TEXT NOT NULL DEFAULT '{}',

    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);


---

15.4 guild_access_roles

CREATE TABLE guild_access_roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    guild_id TEXT NOT NULL,
    role_id TEXT NOT NULL,

    note TEXT,
    added_by_user_id TEXT,
    created_at TEXT NOT NULL,

    UNIQUE (guild_id, role_id)
);


---

15.5 guild_access_users

CREATE TABLE guild_access_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    guild_id TEXT NOT NULL,
    user_id TEXT NOT NULL,

    note TEXT,
    added_by_user_id TEXT,
    created_at TEXT NOT NULL,

    UNIQUE (guild_id, user_id)
);


---

15.6 audit_runs

CREATE TABLE audit_runs (
    id TEXT PRIMARY KEY,

    guild_id TEXT NOT NULL,
    executed_by_user_id TEXT NOT NULL,

    mode TEXT NOT NULL,
    status TEXT NOT NULL,

    score INTEGER,
    max_score INTEGER NOT NULL DEFAULT 100,

    total_findings INTEGER NOT NULL DEFAULT 0,
    critical_count INTEGER NOT NULL DEFAULT 0,
    high_count INTEGER NOT NULL DEFAULT 0,
    medium_count INTEGER NOT NULL DEFAULT 0,
    low_count INTEGER NOT NULL DEFAULT 0,
    info_count INTEGER NOT NULL DEFAULT 0,

    checked_categories_json TEXT NOT NULL DEFAULT '[]',
    skipped_categories_json TEXT NOT NULL DEFAULT '[]',
    error_summary_json TEXT NOT NULL DEFAULT '[]',

    started_at TEXT NOT NULL,
    finished_at TEXT,

    created_at TEXT NOT NULL
);

status

success
partial_success
failed
cancelled


---

15.7 audit_findings

CREATE TABLE audit_findings (
    id TEXT PRIMARY KEY,

    audit_run_id TEXT NOT NULL,
    guild_id TEXT NOT NULL,

    finding_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,

    severity TEXT NOT NULL,
    category TEXT NOT NULL,

    title_key TEXT NOT NULL,
    summary_key TEXT NOT NULL,
    why_it_matters_key TEXT NOT NULL,
    recommendation_key TEXT NOT NULL,

    target_type TEXT,
    target_id TEXT,
    target_name_snapshot TEXT,

    evidence_json TEXT NOT NULL DEFAULT '[]',
    affected_items_json TEXT NOT NULL DEFAULT '[]',
    metadata_json TEXT NOT NULL DEFAULT '{}',

    risk_score INTEGER NOT NULL DEFAULT 0,

    is_allowlisted BOOLEAN NOT NULL DEFAULT 0,
    allowlist_entry_id INTEGER,

    created_at TEXT NOT NULL,

    FOREIGN KEY (audit_run_id) REFERENCES audit_runs(id)
);

fingerprint例

channel.desynced_from_category:guild:123:channel:456
role.has_administrator:guild:123:role:789
invite.no_expiration:guild:123:invite:abcDEF
webhook.exists:guild:123:webhook:999
automod.no_mention_spam_rule:guild:123


---

15.8 audit_log_entries

CREATE TABLE audit_log_entries (
    id TEXT PRIMARY KEY,

    audit_run_id TEXT,
    guild_id TEXT NOT NULL,

    discord_audit_log_id TEXT,
    action_type TEXT NOT NULL,

    actor_user_id TEXT,
    target_type TEXT,
    target_id TEXT,

    reason TEXT,
    changes_summary_json TEXT NOT NULL DEFAULT '[]',
    risk_classification TEXT NOT NULL DEFAULT 'info',

    occurred_at TEXT NOT NULL,
    fetched_at TEXT NOT NULL,

    raw_payload_json TEXT,

    FOREIGN KEY (audit_run_id) REFERENCES audit_runs(id)
);

保存方針

保存する:

- action_type
- actor_user_id
- target_type
- target_id
- reason
- changes_summary_json
- risk_classification
- occurred_at

初期では保存しない:

- raw payload全体
- Webhook token
- Invite URL全体
- メッセージ本文

store_raw_payload = true の場合のみ raw_payload_json に保存する。


---

15.9 allowlist_entries

CREATE TABLE allowlist_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    guild_id TEXT NOT NULL,

    finding_key TEXT NOT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT,

    permission_key TEXT,
    fingerprint TEXT,

    reason TEXT NOT NULL,

    expires_at TEXT,
    created_by_user_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT 1
);

allowlistマッチ順

1. fingerprint 完全一致
2. finding_key + target_type + target_id + permission_key
3. finding_key + target_type + target_id
4. finding_key + target_type

4は広すぎるため、設定時に警告を出す。


---

15.10 インデックス

CREATE INDEX idx_audit_runs_guild_created
ON audit_runs (guild_id, created_at);

CREATE INDEX idx_audit_findings_run
ON audit_findings (audit_run_id);

CREATE INDEX idx_audit_findings_guild_fingerprint
ON audit_findings (guild_id, fingerprint);

CREATE INDEX idx_audit_findings_guild_key
ON audit_findings (guild_id, finding_key);

CREATE INDEX idx_audit_log_entries_guild_occurred
ON audit_log_entries (guild_id, occurred_at);

CREATE INDEX idx_allowlist_guild_key_target
ON allowlist_entries (guild_id, finding_key, target_type, target_id);

CREATE INDEX idx_access_roles_guild
ON guild_access_roles (guild_id);

CREATE INDEX idx_access_users_guild
ON guild_access_users (guild_id);


---

16. Findingモデル

16.1 基本方針

Findingは監査で検出された1件の問題

文言は直接持たず、locale keyを持つ

DB保存・allowlist・差分比較のために安定IDを持つ

同一問題判定用にfingerprintを持つ

表示時にi18nで翻訳する


16.2 Pythonモデル

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class Severity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AuditCategory(StrEnum):
    GUILD = "guild"
    ROLE = "role"
    CHANNEL = "channel"
    INVITE = "invite"
    WEBHOOK = "webhook"
    AUTOMOD = "automod"
    AUDITLOG = "auditlog"
    BOT = "bot"


class TargetType(StrEnum):
    GUILD = "guild"
    ROLE = "role"
    CHANNEL = "channel"
    CATEGORY = "category"
    INVITE = "invite"
    WEBHOOK = "webhook"
    AUTOMOD_RULE = "automod_rule"
    USER = "user"
    BOT = "bot"
    UNKNOWN = "unknown"


class Evidence(BaseModel):
    label_key: str
    value: str
    raw_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AffectedItem(BaseModel):
    target_type: TargetType
    target_id: str | None = None
    display_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Finding(BaseModel):
    finding_key: str
    fingerprint: str

    severity: Severity
    category: AuditCategory
    risk_score: int = 0

    title_key: str
    summary_key: str
    why_it_matters_key: str
    recommendation_key: str

    target_type: TargetType = TargetType.UNKNOWN
    target_id: str | None = None
    target_name_snapshot: str | None = None

    evidence: list[Evidence] = Field(default_factory=list)
    affected_items: list[AffectedItem] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    is_allowlisted: bool = False
    allowlist_entry_id: int | None = None

    created_at: datetime


---

16.3 AuditResultモデル

class AuditStatus(StrEnum):
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AuditMode(StrEnum):
    BASIC = "basic"
    STANDARD = "standard"
    EXTENDED = "extended"


class AuditError(BaseModel):
    category: AuditCategory
    message_key: str
    detail: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditResult(BaseModel):
    audit_run_id: str
    guild_id: str
    executed_by_user_id: str

    mode: AuditMode
    status: AuditStatus

    score: int | None = None
    max_score: int = 100

    findings: list[Finding] = Field(default_factory=list)
    errors: list[AuditError] = Field(default_factory=list)

    checked_categories: list[AuditCategory] = Field(default_factory=list)
    skipped_categories: list[AuditCategory] = Field(default_factory=list)

    started_at: datetime
    finished_at: datetime | None = None


---

17. Finding Key一覧 v1

Guild

guild.mfa_disabled
guild.verification_level_low
guild.explicit_content_filter_disabled
guild.community_disabled
guild.safety_alerts_channel_missing

Role

role.has_administrator
role.has_manage_roles
role.has_manage_channels
role.has_manage_webhooks
role.has_mention_everyone
role.everyone_has_dangerous_permission
role.bot_role_too_powerful

Channel

channel.desynced_from_category
channel.everyone_can_view
channel.everyone_can_send
channel.everyone_can_create_invite
channel.everyone_can_mention_everyone
channel.role_has_manage_webhooks
channel.role_has_manage_channels

Invite

invite.no_expiration
invite.unlimited_uses
invite.targets_sensitive_channel
invite.created_by_high_risk_user

Webhook

webhook.exists
webhook.exists_in_public_channel
webhook.too_many_in_channel
webhook.created_recently

AutoMod

automod.disabled
automod.no_mention_spam_rule
automod.no_keyword_rule
automod.rule_disabled
automod.exemptions_too_broad

Audit Log

auditlog.recent_permission_change
auditlog.recent_role_change
auditlog.recent_channel_permission_change
auditlog.recent_webhook_change
auditlog.recent_invite_change
auditlog.unusual_admin_activity


---

18. スコアリング仕様

18.1 基本スコア

初期値: 100

Critical: -20
High:     -10
Medium:   -5
Low:      -2
Info:      0

最低値: 0

18.2 カテゴリ別減点上限

roles:          最大 -40
channels:       最大 -30
invites:        最大 -20
webhooks:       最大 -20
audit_logs:     最大 -20
guild_settings: 最大 -15
automod:        最大 -15

18.3 allowlist適用時

Finding自体は保存する
is_allowlisted = true
スコア減点対象から除外
レポート上は「例外リスト適用済み」と表示


---

19. 多言語対応

19.1 方針

初期実装から多言語対応する。
対応言語は日本語・英語。

locales/
  ja.yml
  en.yml

19.2 locale解決順

1. guild_settings.locale
2. interaction.guild_locale
3. interaction.locale
4. ja

discord.py のInteractionにはユーザーのlocaleとGuildのpreferred localeを参照する属性がある。

19.3 翻訳対象

翻訳する:

- Finding title
- summary
- why_it_matters
- recommendation
- severity label
- category label
- report heading
- error message
- permission label
- permission risk description

翻訳しない:

- channel name
- role name
- user name
- Discord ID
- permission internal key
- finding_key
- fingerprint

19.4 ja.yml構造

meta:
  locale_name: "日本語"

common:
  severity:
    critical: "緊急"
    high: "高"
    medium: "中"
    low: "低"
    info: "情報"

  category:
    guild: "サーバー設定"
    role: "ロール"
    channel: "チャンネル"
    invite: "招待リンク"
    webhook: "Webhook"
    automod: "AutoMod"
    auditlog: "監査ログ"
    bot: "Bot"

  status:
    success: "完了"
    partial_success: "一部完了"
    failed: "失敗"
    cancelled: "キャンセル"

report:
  summary_title: "セキュリティ診断結果"
  score_line: "スコア: {score} / {max_score}"
  finding_counts: "緊急: {critical} / 高: {high} / 中: {medium} / 低: {low} / 情報: {info}"
  partial_success_notice: "一部の監査は権限不足またはエラーにより完了できませんでした。"
  no_findings: "大きな問題は見つかりませんでした。"
  allowlisted_suffix: "例外リスト適用済み"

errors:
  permission_missing: "Botに必要な権限がありません。"
  audit_log_permission_missing: "Botに監査ログを見る権限がないため、監査ログを確認できませんでした。"
  webhook_permission_missing: "BotにWebhook管理権限がないため、Webhookを確認できませんでした。"
  unknown_error: "予期しないエラーが発生しました。"

permissions:
  VIEW_CHANNEL:
    label: "チャンネルを見る権限"
    risk: "本来見えない場所が見える可能性があります。"
  SEND_MESSAGES:
    label: "メッセージを送る権限"
    risk: "荒らしやスパム投稿の入口になる可能性があります。"
  CREATE_INSTANT_INVITE:
    label: "招待リンクを作る権限"
    risk: "意図しない人がサーバーに参加できる可能性があります。"
  MANAGE_CHANNELS:
    label: "チャンネルを管理する権限"
    risk: "チャンネル設定や権限を変更できる可能性があります。"
  MANAGE_ROLES:
    label: "ロールを管理する権限"
    risk: "他のユーザーの権限を変更できる可能性があります。"
  MANAGE_WEBHOOKS:
    label: "Webhookを管理する権限"
    risk: "外部サービス名義の投稿を作れる可能性があります。"
  MENTION_EVERYONE:
    label: "@everyone / @here を使う権限"
    risk: "全体通知スパムにつながる可能性があります。"
  ADMINISTRATOR:
    label: "管理者権限"
    risk: "サーバー内のほぼすべての操作が可能になります。"

evidence:
  parent_category: "親カテゴリ"
  permission_diff: "権限差分"
  affected_role: "対象ロール"
  affected_channel: "対象チャンネル"
  current_value: "現在の値"
  expected_value: "推奨値"

findings:
  channel:
    desynced_from_category:
      title: "チャンネルがカテゴリと同期されていません"
      summary: "{channel_name} は親カテゴリ {category_name} と権限設定が異なります。"
      why_it_matters: "親カテゴリ側で権限を修正しても、このチャンネルには反映されない可能性があります。そのため、非公開にしたつもりの情報が見えてしまう事故につながります。"
      recommendation: "意図した例外でなければ、チャンネル権限をカテゴリと同期してください。意図した例外であれば、理由と期限を付けて例外リストに登録してください。"

    everyone_can_view:
      title: "@everyone がチャンネルを閲覧できます"
      summary: "{channel_name} は全員が閲覧できる設定です。"
      why_it_matters: "案内・運営・管理用チャンネルが全員に見えると、内部情報が漏れる可能性があります。"
      recommendation: "公開する必要がないチャンネルでは、@everyone の閲覧権限を拒否してください。"

    everyone_can_send:
      title: "@everyone がメッセージを送信できます"
      summary: "{channel_name} は全員がメッセージを送信できる設定です。"
      why_it_matters: "荒らしやスパム投稿の入口になりやすく、重要チャンネルでは特に危険です。"
      recommendation: "重要チャンネルでは @everyone の送信権限を拒否し、必要なロールだけに許可してください。"

  role:
    has_administrator:
      title: "管理者権限を持つロールがあります"
      summary: "{role_name} に管理者権限が付与されています。"
      why_it_matters: "この権限を持つアカウントが乗っ取られると、チャンネル削除、ロール変更、Bot追加など、サーバー全体への影響が出る可能性があります。"
      recommendation: "管理者権限は最小限のロールだけに付与し、通常運用では個別権限を使ってください。"

    everyone_has_dangerous_permission:
      title: "@everyone に危険な権限があります"
      summary: "@everyone に {permission_label} が付与されています。"
      why_it_matters: "サーバー参加者全員が強い操作をできる状態になっています。"
      recommendation: "@everyone から該当権限を外し、必要なロールだけに付与してください。"


---

20. 例外リスト仕様

20.1 目的

運用上、意図的に許容している設定を毎回警告しないために使用する。

例:

- イベント用に一時的にカテゴリ非同期にしているチャンネル
- 緊急対応用のAdministratorロール
- 外部連携用のWebhook

20.2 例外登録項目

guild_id
finding_key
target_type
target_id
permission_key
fingerprint
reason
expires_at
created_by_user_id
is_active

20.3 期限切れ

expires_at を過ぎた例外は無効扱いにする。
監査結果では「期限切れの例外設定があります」と表示する。


---

21. 排他制御・クールダウン

21.1 同時実行制御

同一Guildで同時に実行できる監査は1つまで。

初期実装:

asyncio.Lock per guild

将来:

DB lock

21.2 クールダウン

同一ユーザー・同一Guildで30秒

21.3 上限設定

limits:
  max_channels_per_run: 500
  max_audit_log_entries: 300
  max_webhooks_per_run: 300
  max_invites_per_run: 300
  command_cooldown_seconds: 30


---

22. /audit doctor 仕様

22.1 目的

Bot自身が監査に必要な権限を持っているか確認する。

22.2 確認項目

- View Channels
- View Audit Log
- Manage Guild
- Manage Webhooks
- Botロールの位置
- 読めないチャンネル数
- AutoMod取得可否
- Webhook取得可否
- DB接続状態
- localeロード状態

22.3 出力例

🩺 Bot診断結果

正常:
- Slash Commandは利用可能です
- DB接続は正常です

不足:
- View Audit Log がありません
  → 監査ログ監査はスキップされます

注意:
- 読み取れないチャンネルが3件あります
  → チャンネル監査結果が一部不足する可能性があります


---

23. エラー処理

23.1 部分成功

監査の一部カテゴリで失敗しても、可能なカテゴリは結果を返す。

AuditResult.status = partial_success

例:

できたこと:
- ロール監査
- チャンネル監査
- サーバー設定監査

できなかったこと:
- Webhook監査
- 監査ログ監査

理由:
Botに必要な権限がありません。

23.2 エラー分類

permission_missing
api_error
rate_limited
timeout
db_error
unknown_error

23.3 ログマスキング

ログに出してはいけないもの:

- Bot token
- Webhook URL
- Webhook token
- Invite URL全文
- raw payload内の不要な個人情報


---

24. セキュリティ要件

24.1 監査結果

初期実装ではephemeralのみ

DB保存するが、公開チャンネルには投稿しない

Findingのevidenceは必要最小限にする

Invite URLやWebhook URLは保存・表示しない


24.2 DB

Discord IDは文字列で保存

raw payloadは初期では保存しない

保存期間は guild_settings.log_retention_days で制御

期限切れデータの削除ジョブを実装可能にする


24.3 Bot権限

Administrator は要求しない

Phase 1では書き込み系権限を要求しない

Phase 2以降の修正機能は /remediate に分離



---

25. ディレクトリ構成

discord-security-auditor/
  app/
    main.py
    bot.py

    cogs/
      audit.py
      config.py
      health.py
      admin.py

    audit/
      __init__.py
      models.py
      runner.py
      scoring.py
      allowlist.py
      i18n.py
      permissions.py
      profiles.py

      checks/
        guild_settings.py
        roles.py
        channels.py
        invites.py
        webhooks.py
        automod.py
        audit_logs.py
        bot_self_check.py

    db/
      base.py
      models.py
      session.py

      repositories/
        guild_settings.py
        access_control.py
        audit_runs.py
        allowlist.py
        audit_logs.py

    reports/
      embed_formatter.py
      render_models.py

    config/
      settings.py

  config/
    audit_rules.yml

  locales/
    ja.yml
    en.yml

  migrations/
    versions/

  tests/
    test_channel_sync.py
    test_role_permissions.py
    test_allowlist.py
    test_scoring.py
    test_i18n.py
    test_embed_pagination.py

  pyproject.toml
  .env.example
  README.md


---

26. 主要処理フロー

26.1 /audit summary

1. Slash Command受信
2. AccessControlServiceで実行権限確認
3. interaction.response.defer(ephemeral=True, thinking=True)
4. Guild単位ロック取得
5. guild_settings取得
6. audit_rules.yml + profile + overridesを解決
7. AuditRunner実行
8. 各checkがFindingを返す
9. AllowlistService.apply()
10. ScoreCalculator.calculate()
11. AuditRepository.save_run()
12. I18nRenderer.render()
13. EmbedFormatter.format()
14. interaction.followup.send(embed=..., ephemeral=True)
15. ロック解放

26.2 /audit channel-sync

1. 対象チャンネルまたはカテゴリを解決
2. 子チャンネルのpermissions_synced確認
3. 非同期の場合、親カテゴリとのoverwrite差分を生成
4. 危険権限が含まれる場合はseverityを上げる
5. Findingとして保存
6. Embedで表示


---

27. テスト方針

27.1 単体テスト

tests/
  test_channel_sync.py
  test_role_permissions.py
  test_allowlist.py
  test_scoring.py
  test_i18n.py
  test_embed_pagination.py

27.2 特にテストすべき箇所

- チャンネル非同期の検出
- 親カテゴリとの差分生成
- 危険権限によるseverity昇格
- allowlist適用
- allowlist期限切れ
- スコア計算
- locale key不足時のfallback
- Embed文字数制限
- 部分成功ステータス

27.3 DTO化

Discordオブジェクトを直接テストしづらいため、監査ロジックには内部DTOを渡せる設計にする。

Discord Channel
  ↓
ChannelSnapshot
  ↓
Audit Check


---

28. 非機能要件

項目	要件

可用性	一部監査失敗時も可能な範囲で結果を返す
拡張性	Cogs / checks分離で機能追加可能
保守性	Finding ID、locale key、DB schemaを安定化
セキュリティ	初期は読み取り専用、結果はephemeral
国際化	ja / enを初期対応
パフォーマンス	Guild単位ロック、件数上限、カテゴリ別監査
監査性	audit_runs / audit_findings / audit_log_entriesを保存
移植性	SQLiteからPostgreSQLへ移行可能
安全性	Webhook token / Invite URL / Bot tokenはログ出力しない



---

29. 実装優先順位

29.1 最初に実装するもの

1. app/audit/models.py
2. locales/ja.yml
3. locales/en.yml
4. app/db/models.py
5. app/db/session.py
6. app/db/repositories/guild_settings.py
7. app/db/repositories/audit_runs.py
8. app/audit/i18n.py
9. app/audit/allowlist.py
10. app/audit/scoring.py
11. app/audit/checks/channels.py
12. app/reports/embed_formatter.py
13. app/cogs/audit.py
14. app/cogs/config.py
15. /audit doctor

29.2 最初のMVPコマンド

/ping
/audit doctor
/audit channel-sync
/audit channels
/audit roles
/audit summary
/config access add-role
/config access list
/config locale set
/config allowlist add
/config allowlist list

29.3 初期MVPで最重要

channel.desynced_from_category
role.has_administrator
role.everyone_has_dangerous_permission
channel.everyone_can_view
channel.everyone_can_send


---

30. 未決定事項

以下は後で決める。

- DBを最初からPostgreSQLにするか
- EmbedのボタンページングをPhase 1に含めるか
- Webhook監査でどこまで名前・作成者を表示するか
- Invite監査でコードを一部マスクするか、完全非表示にするか
- server_profileの具体的しきい値
- schedule監査を実装するか
- JSON / Markdown exportをPhase 2に含めるか


---

31. 確定事項まとめ

- discord.pyで実装する
- Slash Command対応
- Cogs / Extensionsで機能管理する
- 監査ロジックはCogから分離する
- 初期は読み取り専用
- 監査結果はephemeral
- 実行権限はロール・ユーザー単位で設定可能にする
- 監査範囲はbasic / standard / extended
- 初期デフォルトはstandard
- 拡張監査モード込みのBot権限で設計する
- チャンネル非同期監査を重視する
- サーバーサイズ別profileは後で拡張可能な形にする
- allowlistを実装する
- 初期レポート形式はDiscord Embed
- 多言語対応は最初から入れる
- 監査結果と監査ログ要約はDB保存する
- DB保存期間は設定から変更可能にする
- Finding IDとfingerprintを安定IDとして扱う
- 将来の修正機能は/remediateに分離する