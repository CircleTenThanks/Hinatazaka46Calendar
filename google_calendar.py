from dependencies import os, pickle, datetime, build, service_account, Request
from text_processing import (
    get_event_info_from_hnz_hp,
    prepare_info_for_calendar,
)
from web_scraping import get_event_description
"""
このモジュールは、Google Calendar APIを使用してカレンダーの操作を行うための関数を提供します。
主な機能は以下の通りです：
- Google Calendar APIのセットアップ
- 指定されたカレンダーから特定の月のスケジュールを取得
- イベントの追加、更新、削除
これにより、外部のスケジュール情報をGoogleカレンダーに統合し、管理を容易にします。
"""

def build_google_calendar_api():
    """
    Google Calendar APIを構築します。
    トークンが存在する場合はそれを使用し、存在しない場合は新たに生成します。
    """
    SCOPES = ["https://www.googleapis.com/auth/calendar"]
    creds = None
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            creds = service_account.Credentials.from_service_account_file(
                "credentials_hnz.json", scopes=SCOPES
            )
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    service = build("calendar", "v3", credentials=creds)

    return service


def get_schedule_from_google_calendar(service, calendar_id, year, month):
    """
    Googleカレンダーから指定された年月のスケジュールを取得します。
    これにより、重複してスケジュールを登録することを防ぎます。
    Args:
        service: Google Calendar APIのサービスインスタンス
        calendar_id: カレンダーID
        year: 取得するスケジュールの年
        month: 取得するスケジュールの月
    """
    timezone = "Asia/Tokyo"

    # JSTタイムゾーンでの開始日時と終了日時を設定します
    start_time = datetime.datetime(
        year, month, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
    )
    # 翌月の4時までを取得対象とすることで、25時～28時表記のイベントもカバーします
    # 12月の場合、翌年の1月を指定する必要があります
    if month == 12:
        end_time = datetime.datetime(
            year + 1, 1, 1, 4, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )
    else:
        end_time = datetime.datetime(
            year, month + 1, 1, 4, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )

    # カレンダーのイベントを取得します
    events_result = (
        service.events()
        .list(
            calendarId=calendar_id,
            timeMin=start_time.isoformat(),
            timeMax=end_time.isoformat(),
            timeZone=timezone,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )

    events = events_result.get("items", [])

    if not events:
        return []
    else:
        for event in events:
            event["startTimeJST"] = change_event_starttime_to_jst(event)

            # HPに存在しているかを後の処理でチェックするためのキー。
            # 存在していれば True に更新される想定。
            event["hnz_hp_checked"] = False

        return events


def add_event_to_google_calendar(
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
    content_type,
):
    """
    Googleカレンダーにイベントを登録します。
    Args:
        service: Google Calendar APIのサービスインスタンス
        calendar_id: カレンダーID
        year: イベントの年
        month: イベントの月
        event_date_text: イベントの日付テキスト
        event_name: イベント名
        event_category: イベントカテゴリ
        event_time: イベント時間
        event_link: イベントリンク
        previous_add_event_lists: 以前に追加されたイベントリスト
    """
    (
        event_name_text,
        event_category_text,
        event_time_text,
        event_link_text,
    ) = get_event_info_from_hnz_hp(event_name, event_category, event_time, event_link)

    # カレンダーに反映させる情報の準備
    (
        event_title,
        event_start,
        event_end,
        is_date,
    ) = prepare_info_for_calendar(
        year,
        month,
        event_name_text,
        event_category_text,
        event_time_text,
        event_date_text,
    )

    # 見つかったインデックスを格納する変数
    found_index = None

    # eventsをイテレートして一致する要素を探す
    for index, event in enumerate(previous_add_event_lists):
        if (
            event.get("summary") == event_title
            and event.get("startTimeJST") == event_start
        ):
            found_index = index
            previous_add_event_lists[index].update({"hnz_hp_checked": True})
            break

    if found_index is not None:  # 同じ予定がすでに存在する場合は追加しない
        print("pass:" + event_start + " " + event_title)
        pass
    else:
        event_description = get_event_description(event_link_text, datetime.datetime(year, month, int(event_date_text)), content_type)
        print("add:" + event_start + " " + event_title)
        build_google_calendar_format(
            calendar_id,
            event_title,
            event_start,
            event_end,
            event_description,
            event_link_text,
            is_date,
            service,
        )

def build_google_calendar_format(
    calendar_id, summary, start, end, event_description, event_link_text, is_date, service
):
    """
    Googleカレンダーに登録する形式にデータを整形します。
    Args:
        calendar_id: カレンダーID
        summary: イベントの概要
        start: イベントの開始時間
        end: イベントの終了時間
        event_description: イベントに参加するメンバー
        event_link_text: イベントのリンクテキスト
        is_date: 日付のみかどうかのフラグ
        service: Google Calendar APIのサービスインスタンス
    """
    if is_date:
        event = {
            "summary": summary,
            "description": event_link_text + "\n" + event_description,
            "start": {
                "date": start,
                "timeZone": "Japan",
            },
            "end": {
                "date": end,
                "timeZone": "Japan",
            },
        }
    else:
        event = {
            "summary": summary,
            "description": event_link_text + "\n" + event_description,
            "start": {
                "dateTime": start,
                "timeZone": "Japan",
            },
            "end": {
                "dateTime": end,
                "timeZone": "Japan",
            },
        }

    event = (
        service.events()
        .insert(
            calendarId=calendar_id,
            body=event,
        )
        .execute()
    )


def remove_event_from_google_calendar(service, calendar_id, previous_add_event_lists):
    """
    Googleカレンダーから不要なイベントを削除します。
    Args:
        service: Google Calendar APIのサービスインスタンス
        calendar_id: カレンダーID
        previous_add_event_lists: 以前に追加されたイベントリスト
    """
    for event in previous_add_event_lists:
        # get_schedule_from_google_calendar では 25時～28時表記になっていた場合を考慮して翌月の4時までを取得対象としているため
        if (
            datetime.datetime.fromisoformat(event["startTimeJST"]).day == 1
            and datetime.datetime.fromisoformat(event["startTimeJST"]).day <= 4
        ):
            continue
        if event["hnz_hp_checked"] == False:
            service.events().delete(
                calendarId=calendar_id, eventId=event["id"]
            ).execute()
            print(f"del:{event['startTimeJST']} {event['summary']}")


def change_event_starttime_to_jst(event):
    """
    イベントの開始時間を日本時間に変換します。
    Args:
        event: イベントデータ
    """
    if "date" in event["start"].keys():
        return event["start"]["date"]
    else:
        str_event_uct_time = event["start"]["dateTime"]
        event_jst_time = datetime.datetime.strptime(
            str_event_uct_time, "%Y-%m-%dT%H:%M:%S+09:00"
        )
        str_event_jst_time = event_jst_time.strftime("%Y-%m-%dT%H:%M:%S")
        return str_event_jst_time
