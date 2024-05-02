from dependencies import os, datetime, relativedelta
from google_calendar import (
    build_google_calendar_api,
    get_schedule_from_google_calendar,
    add_event_to_google_calendar,
    remove_event_from_google_calendar,
)
from web_scraping import get_month_content_from_hnz_hp, get_contents_from_hnz_hp
"""
このモジュールは、日向坂46の公式ホームページからイベントスケジュールを取得し、Googleカレンダーに自動で追加する機能を提供します。
主な機能は以下の通りです：
- Google Calendar APIを使用してカレンダーのインスタンスを生成します。
- 日向坂46の公式ホームページから指定された月のスケジュールを取得します。
- 取得したスケジュールをGoogleカレンダーに追加します。
- Googleカレンダーから削除されたイベントを削除します。

これにより、ユーザーは日向坂46の最新のスケジュールを常にカレンダー上で確認することができます。
"""


def main():
    # Google Calendar APIのインスタンスを生成します。
    service = build_google_calendar_api()

    # 環境変数からカレンダーIDを取得します。
    calendar_id = os.environ["CALENDAR_ID_HNZ"]
    num_search_month = 3
    current_search_date = datetime.datetime.now()

    # 指定された月数分のスケジュールをカレンダーに反映します。
    for _ in range(num_search_month):
        year = current_search_date.year
        month = current_search_date.month
        previous_add_event_lists = get_schedule_from_google_calendar(
            service, calendar_id, year, month
        )

        # 日向坂46公式ホームページからその月のスケジュールを取得します。
        events_each_date = get_month_content_from_hnz_hp(
            year, "{:02}".format(month)
        )
        if events_each_date is None:
            continue

        for event_each_date in events_each_date:
            # 特定の日に予定されているイベントの詳細を取得します。
            event_date_text, events_time, events_name, events_category, events_link = (
                get_contents_from_hnz_hp(event_each_date)
            )
            event_date_text = "{:02}".format(int(event_date_text))

            # 取得したイベントをGoogleカレンダーに追加します。
            for event_name, event_category, event_time, event_link in zip(
                events_name, events_category, events_time, events_link
            ):
                add_event_to_google_calendar(
                    service,
                    calendar_id,
                    year,
                    month,
                    event_date_text,
                    event_name,
                    event_category,
                    event_time,
                    event_link,
                    previous_add_event_lists,
                )

        # Googleカレンダーから削除されたイベントを削除します。
        remove_event_from_google_calendar(
            service, calendar_id, previous_add_event_lists
        )

        # 次の月のスケジュール取得のために日付を更新します。
        current_search_date += relativedelta(months=1)


if __name__ == "__main__":
    main()
