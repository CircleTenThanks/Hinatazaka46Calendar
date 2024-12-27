from dependencies import os, datetime, relativedelta
from google_calendar import (
    build_google_calendar_api,
    get_schedule_from_google_calendar,
    add_event_to_google_calendar,
    remove_event_from_google_calendar,
)
from web_scraping import get_month_schedule_from_hnz_hp, get_events_from_hnz_hp

def main():
    # Google Calendar APIインスタンスの生成
    service = build_google_calendar_api()

    # 環境変数からカレンダーID取得
    calendar_id = os.environ["CALENDAR_ID_HNZ"]
    num_search_month = 3
    current_search_date = datetime.datetime.now()

    # 指定月数分のスケジュールをカレンダーへ反映
    for _ in range(num_search_month):
        year = current_search_date.year
        month = current_search_date.month
        previous_add_event_lists = get_schedule_from_google_calendar(
            service, calendar_id, year, month
        )

        # 日向坂46公式ホームページから当月スケジュールを取得
        events_each_date = get_month_schedule_from_hnz_hp(
            year, "{:02}".format(month)
        )
        if events_each_date is None:
            continue

        for event_each_date in events_each_date:
            # 特定の日のイベント詳細を取得
            event_date_text, events_time, events_name, events_category, events_link = (
                get_events_from_hnz_hp(event_each_date)
            )
            event_date_text = "{:02}".format(int(event_date_text))

            # 取得イベントをGoogleカレンダーへ追加
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

        # Googleカレンダーから削除済みイベントを削除
        remove_event_from_google_calendar(
            service, calendar_id, previous_add_event_lists
        )

        # 次月スケジュール取得のため日付更新
        current_search_date += relativedelta(months=1)


if __name__ == "__main__":
    main()
