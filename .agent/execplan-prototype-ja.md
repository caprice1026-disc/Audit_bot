# プロトタイプ実装計画（Discord Security Auditor Bot）

このExecPlanは living document です。`Progress`、`Surprises & Discoveries`、`Decision Log`、`Outcomes & Retrospective` を作業中に更新し続けます。

本計画は `PLANS.md` に従って維持します。

## Purpose / Big Picture

この変更により、Discord APIの実運用接続を必要とせず、監査ロジックの中核（カテゴリ同期ずれ検出、危険権限検出、サマリー生成）をローカルで検証できる最小プロトタイプを提供します。利用者は `pytest` を実行するだけで、Discordトークンを使う箇所がモックされること、および監査結果が期待どおりに生成されることを確認できます。

## Progress

- [x] (2026-05-18 00:00Z) 既存資料（`ypuken.md`、`PLANS.md`）を確認し、初期プロトタイプ範囲を定義した。
- [x] (2026-05-18 00:10Z) プロトタイプ実装（モデル、チェック、サービス、Botエントリ）を追加した。
- [x] (2026-05-18 00:20Z) Discordトークン利用箇所を `pytest` モックで検証するテストを追加した。
- [x] (2026-05-18 00:25Z) `pytest` 実行で全テスト成功を確認した。
- [x] (2026-05-18 00:40Z) チャンネル権限差分に危険権限が含まれる場合のseverity昇格ロジックを追加した。

## Surprises & Discoveries

- Observation: リポジトリには `youken.md` ではなく `ypuken.md` が存在した。
  Evidence: `rg --files | rg 'youken|ypuken'` の結果で `ypuken.md` のみ検出。

## Decision Log

- Decision: Discord依存を最小化するため、プロトタイプ段階では Discord オブジェクトを直接使わずに内部DTO（dataclass）を使用する。
  Rationale: 要件の「DTO化」方針に沿って、テスト容易性とモック容易性を優先するため。
  Date/Author: 2026-05-18 / Codex

- Decision: Discord APIトークンを使う処理は `create_bot_from_env` に閉じ込め、`discord.Client` を遅延importしてモック可能にする。
  Rationale: pytestでネットワーク不要な単体テストを確実に成立させるため。
  Date/Author: 2026-05-18 / Codex

## Outcomes & Retrospective

初期目的どおり、監査ロジックの最小機能とトークン利用部のモックテストが成立した。加えて、チャンネル非同期に危険権限差分がある場合の優先度昇格（medium→high）を実装し、誤検知でないことをテストで確認した。未実装領域（Slash Command、DB保存、Embed整形、多言語）は将来マイルストーンとして分離しやすい構成にした。

## Context and Orientation

このリポジトリは要件文書中心で、実装コードは未整備です。本プロトタイプでは以下の最小構成を新規作成します。

- `app/audit/models.py`: 監査用DTO（Role, Channel, Category, Finding など）
- `app/audit/checks/channels.py`: カテゴリ同期ずれ検出
- `app/audit/checks/roles.py`: 管理者権限・@everyone危険権限検出
- `app/audit/runner.py`: 複数チェックの統合実行
- `app/bot.py`: トークン読込とBot作成（モック対象）
- `tests/*`: 監査ロジックとBot作成のテスト

## Plan of Work

まず、監査対象を表す簡潔なdataclassを導入し、Discord実オブジェクトを使わずに判定できるようにします。次に、要件で最重要とされた `channel.desynced_from_category`、`role.has_administrator`、`role.everyone_has_dangerous_permission` を関数として実装します。その後、Runnerで結果を統合し、カテゴリ別件数と総件数を返します。最後に、Discordトークン利用箇所を `create_bot_from_env` に限定し、`pytest` で `sys.modules` 差し替えモックを使って `discord.Client.run(token)` が正しいトークンで呼ばれることを検証します。

## Concrete Steps

作業ディレクトリは `/workspace/Audit_bot`。

    mkdir -p .agent app/audit/checks tests
    <各ファイルを作成>
    pytest -q

期待出力の例:

    5 passed in 0.xx s

## Validation and Acceptance

`pytest -q` が成功し、以下を確認できれば受け入れとします。

- 同期ずれチャンネルが `channel.desynced_from_category` として検出される。
- 管理者権限ロールが `role.has_administrator` として検出される。
- `@everyone` の危険権限が `role.everyone_has_dangerous_permission` として検出される。
- Discordトークン利用処理が、実トークンを使わずモッククライアント経由で検証される。

## Idempotence and Recovery

本手順は全てファイル追加中心であり、再実行可能です。テストが失敗した場合は `pytest -q -k <失敗ケース>` で局所再実行し、修正後に全件再実行します。

## Artifacts and Notes

    pytest -q
    .....
    6 passed in 0.03s

## Interfaces and Dependencies

- `app.audit.models.Finding`
  - `finding_key: str`
  - `severity: str`
  - `category: str`
  - `summary: str`
- `app.audit.runner.run_prototype_audit(guild: GuildSnapshot) -> AuditResult`
- `app.bot.create_bot_from_env() -> object`

更新履歴メモ: 初版作成。要件文書が `youken.md` 指定だったが実ファイル名 `ypuken.md` に合わせて実装方針を確定した。
