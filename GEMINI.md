# Hinatazaka46Calendar 開発・運用ルール

このリポジトリは、日向坂46公式サイト（`https://www.hinatazaka46.com`）から3か月先までのスケジュールをスクレイピングし、公開Googleカレンダーへ自動同期するPythonパッケージです。

---

## 1. 設計思想と運用ポリシー

### 公式サイトへの負荷軽減（最重要）
- **スリープの厳守**: スクレイピング時は相手サーバーへの負荷を最小限にするため、月次一覧取得や各イベント詳細（出演メンバー取得）のHTTPリクエストごとに必ず待機時間（`_SCRAPE_WAIT_SECONDS = 3`）を設ける。
- **タイムアウトの明示**: `requests.get()` には必ず `timeout=_REQUEST_TIMEOUT_SECONDS`（30秒）を指定し、ハングアップを防ぐ。
- **不要なリクエストの回避**: Googleカレンダー側に同一イベント（タイトルと開始日時が一致）が既に存在する場合は、イベント詳細ページへのアクセス（メンバー取得）を行わずに `pass` する。

### カレンダー同期の整合性（追加・維持・削除）
- **対象期間**: 現在日時（JST）から3か月分（`_SEARCH_MONTHS = 3`）を月単位で同期する。
- **深夜帯（24時超え）の扱い**:
  - 公式サイトの深夜放送表記（例: `25:00`）は `convert_over24h_to_datetime()` によって翌日の日時へ変換される。
  - そのため、当月のカレンダー既存予定を取得する `get_schedule_from_google_calendar()` では、月末深夜の予定を取りこぼさないよう**翌月1日の午前4時（`_OVERNIGHT_END_HOUR = 4`）まで**を取得範囲に含める。
  - 逆に、月初の削除判定（`remove_event_from_google_calendar()`）では、前月末から越境してきた「1日の0時〜4時」の予定を誤削除しないよう保護している。
- **差分削除**: 公式サイトから削除・変更された予定をカレンダーから消すため、既存予定に `hnz_hp_checked` フラグを持たせ、公式HP側と一致しなかった未チェック予定は `delete` する。

### GitHub Actions による定期実行
- 本番環境では、GitHub Actions（`.github/workflows/sync-calendar.yml`）の `schedule`（`11 2 * * *`）および `workflow_dispatch` によって `uv run --frozen --no-dev hinatazaka46-calendar`（`hinatazaka46_calendar.main:main`）が定期実行されて稼働する。
- パッケージ構成は `src/hinatazaka46_calendar/` の **`src` レイアウト**を維持し、`pyproject.toml` の依存関係を変更した場合は `uv lock` で `uv.lock` を更新する。
- **GitHub Actions のバージョン指定ルール**: `.github/workflows/*.yml` で外部 Action（`uses:`）を指定する際は、メジャーバージョンタグ（`@v7` など）ではなく、**その時点の最新安定バージョンをパッチバージョンまで明示（例: `actions/checkout@v7.0.1`, `astral-sh/setup-uv@v10.4.0`, `dependabot/fetch-metadata@v3.1.0`）して記載する**こと。ワークフローの新規作成・更新時は、既存ファイルを含めすべての Action が最新安定バージョンになっているか確認する。

---

## 2. コーディング規約・品質基準

### Ruff 厳格設定（`ALL` + `preview = true`）の遵守
- **コード側での解消**: `pyproject.toml` では `select = ["ALL"]` かつ `preview = true` を有効にしている。Lint エラーが発生した場合は、**安易に `pyproject.toml` の `ignore` を増やしたり `# noqa` で握りつぶしたりせず、コード側の設計・記述を修正して解消する**こと。
  - マジックナンバーは定数化する（例: `_DECEMBER = 12`, `_FIRST_DAY = 1`）。
  - 引数やローカル変数が多すぎる場合は `dataclass(frozen=True)`（`ScrapedEvent`, `EventDate`, `CalendarEventTimes` など）にまとめる。
  - 型ヒント（Type Hints）をすべての関数シグネチャに付与し、型チェック時のみ必要なインポートは `if TYPE_CHECKING:` ブロックに入れる。
- **Docstring 規約**:
  - Google スタイル（`convention = "google"`）を使用する。
  - 1行目（サマリ）の末尾はピリオド `.` で終える（Ruff の `D415` 等のルールに準拠）。
- **ログ出力**:
  - `print()` は使用せず、`logging.getLogger(__name__)` を使用する。フォーマットは `%s` プレースホルダ形式（`LOGGER.info("add:%s %s", ...)`）を用いる。
- **著作権ヘッダ**:
  - `src/hinatazaka46_calendar/` 配下の各 `.py` ファイル先頭には、原著者（Qiita記事著者 `ddn` 氏）と `CircleTenThanks` を併記した以下のヘッダを維持する：
    ```python
    # Copyright (c) 2020 ddn
    # Copyright (c) 2026 CircleTenThanks
    # 一部は https://qiita.com/ddn/items/42def5fa721e531eecdb を基に改変している.
    ```

---

## 3. 開発コマンドとコミット規約

### 検証コマンド（変更後は必ず実行）
CI（`.github/workflows/ruff.yml`）で以下のチェックが必須ステータス（Required status checks）となっているため、変更後は必ず両方パスすることを確認する。

```zsh
uv run --frozen ruff check
uv run --frozen ruff format --check
```

### コミットメッセージ規約
- コードや設定ファイルを変更した際は、完了報告時に**コミットメッセージ案を1つだけ提示する**こと。
- 以下のプレフィックスを付けた簡潔な日本語で記述する：
  - `Add: ...`（新規機能・ファイル追加）
  - `Update: ...`（仕様変更・改善・リファクタリング）
  - `Fix: ...`（バグ修正）
  - `Remove: ...`（不要ファイル・機能の削除）
  - `Upgrade: ...`（依存パッケージのバージョン更新）

### 実行環境・認証情報
- 環境変数: `CALENDAR_ID_HNZ`（登録先のGoogleカレンダーID。GitHub Actions Secrets の `CALENDAR_ID_HNZ` に設定）
- サービスアカウント認証ファイル: カレントディレクトリの `credentials_hnz.json`（Git管理外・秘匿情報のため絶対にコミットしない。GitHub Actions では Secrets の `CREDENTIALS_HNZ_JSON` から実行時に生成する）
- ドキュメント: ユーザー向け案内は `docs/README.md`（GitHub Pages用）、開発・運用概要はルートの `README.md` に分離して管理する。
