---
name: hinatazaka-scraper-maintenance
description: >-
  日向坂46公式サイト（hinatazaka46.com）のHTML構造変更への追従、時刻・カテゴリ・出演メンバー抽出ロジックの修正、
  およびGoogleカレンダー同期の不具合調査を行うためのスキル。スクレイピングやカレンダー登録の修正時に使用する。
---

# 日向坂46カレンダー スクレイパー保守・改修スキル

日向坂46公式サイトの仕様変更や新しいスケジュール表記パターンに対応する際の手順とチェックリストです。

## 1. モジュール構成と責務

- `src/hinatazaka46_calendar/hinatazaka_scraper.py`:
  - 月間スケジュール一覧ページ（`https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy=YYYYMM`）の取得とHTML解析を担当。
  - 主要セレクタ:
    - 年月検証: `div.c-schedule__page_year`, `div.c-schedule__page_month`
    - 日別グループ: `div.p-schedule__list-group`
    - 時刻: `div.c-schedule__time--list`
    - タイトル: `p.c-schedule__text`
    - カテゴリ: `div.p-schedule__head`
    - 詳細リンク親要素: `li.p-schedule__item`
- `src/hinatazaka46_calendar/event_formatter.py`:
  - 詳細ページからの出演メンバー抽出（`div.c-article__tag` 内の `a` タグ）およびカレンダー登録用の日時・タイトル整形を担当。
  - 24時以降の深夜時刻（`24:30` や `25:00` など）を `convert_over24h_to_datetime()` で翌日日時に変換する。
- `src/hinatazaka46_calendar/text_formatter.py`:
  - `mojimoji.zen_to_han(text, kana=False)` による全角英数字・記号の半角正規化（カナは全角維持）と改行・空白除去を担当。
- `src/hinatazaka46_calendar/google_calendar.py`:
  - Google Calendar API (`v3`) による予定一覧取得、重複チェック、新規追加、および公式HPから消えた予定の削除を担当。

## 2. 公式サイト仕様変更時の調査・修正手順

1. **HTML構造の確認**
   - 対象月のURL（例: `https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy=202611`）を取得し、`validate_date()` や `get_events_from_hnz_hp()` で抽出している要素数（`events_time`, `events_name`, `events_category`, `events_link`）が一致しているか確認する。
   - `main.py` では `zip(..., strict=True)` を使用しているため、いずれかのセレクタが欠落すると `ValueError` で即座に検知できる。

2. **詳細ページ（出演メンバー）の確認**
   - イベント詳細ページで `div.c-article__tag` が存在しない場合でも、`get_event_member_from_event_info()` が `AttributeError` をキャッチして空文字列 `""` を返す設計になっているか確認する。

3. **深夜帯（日付跨ぎ）と月末・月初境界の検証**
   - 時刻フォーマットの変更を行う場合、以下が壊れていないか必ず確認する：
     - 時刻未指定（終日イベント）の場合に `is_date=True`（`YYYY-MM-DD`）になること。
     - 開始時刻のみ（例: `22:00~`）の場合に `start == end` の日時イベントになること。
     - 12月実行時に翌年1月1日4:00まで正しく取得範囲が計算されること。

## 3. 修正後の検証手順

1. **Ruff による静的解析とフォーマット確認**
   ```zsh
   uv run --frozen ruff check
   uv run --frozen ruff format --check
   ```
   ※ `select = ["ALL"]`, `preview = true` が有効なため、新規関数には必ず Google スタイルの Docstring と完全な型アノテーションを記述し、複雑度（C901 / PLR0913 等）の制限を超えないよう小さなヘルパー関数や `dataclass` に分割すること。
