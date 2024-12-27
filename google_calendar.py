import os
import pickle
import datetime
from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request
from event_formatter import (
    get_event_info_from_hnz_hp,
    prepare_info_for_calendar,
    get_event_member_from_event_info,
)
"""
Google Calendar APIを使用したカレンダー操作モジュール
"""

def build_google_calendar_api():
    """
    Google Calendar APIを使用する準備。
    既存トークンを使用するか新規生成する。
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
    指定年月のスケジュールを取得する。
    スケジュールを重複して登録しないように工夫している。
    Args:
        service: Google Calendar APIのサービスインスタンス
        calendar_id: カレンダーID
        year: 取得年
        month: 取得月
    """
    timezone = "Asia/Tokyo"

    # JSTタイムゾーンでの開始・終了日時設定
    start_time = datetime.datetime(
        year, month, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
    )
    # 25時～28時表記のイベントを補正する。
    # 12月の場合は翌年1月指定
    if month == 12:
        end_time = datetime.datetime(
            year + 1, 1, 1, 4, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )
    else:
        end_time = datetime.datetime(
            year, month + 1, 1, 4, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
        )

    # カレンダーイベントの取得
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

            # HPでの存在確認用フラグ
            # 存在時はTrueに更新
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
):
    """
    Googleカレンダーへイベントを登録する。
    Args:
        service: Google Calendar APIのサービスインスタンス
        calendar_id: カレンダーID
        year: イベント年
        month: イベント月
        event_date_text: イベント日付テキスト
        event_name: イベント名
        event_category: イベントカテゴリ
        event_time: イベント時間
        event_link: イベントリンク
        previous_add_event_lists: 過去追加イベントリスト
    """
    (
        event_name_text,
        event_category_text,
        event_time_text,
        event_link_text,
    ) = get_event_info_from_hnz_hp(event_name, event_category, event_time, event_link)

    # カレンダー反映情報の準備
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

    # 一致イベントのインデックス格納用
    found_index = None

    # 一致要素の検索
    for index, event in enumerate(previous_add_event_lists):
        if (
            event.get("summary") == event_title
            and event.get("startTimeJST") == event_start
        ):
            found_index = index
            previous_add_event_lists[index].update({"hnz_hp_checked": True})
            break

    if found_index is not None:  # 既存予定の場合はスキップ
        print("pass:" + event_start + " " + event_title)
        pass
    else:
        active_members = get_event_member_from_event_info(event_link_text)
        print("add:" + event_start + " " + event_title)
        build_google_calendar_format(
            calendar_id,
            event_title,
            event_start,
            event_end,
            active_members,
            event_link_text,
            is_date,
            service,
        )


def build_google_calendar_format(
    calendar_id, summary, start, end, active_members, event_link_text, is_date, service
):
    """
    Googleカレンダー登録形式へデータを整形する。
    Args:
        calendar_id: カレンダーID
        summary: イベント概要
        start: 開始時間
        end: 終了時間
        active_members: 参加メンバー
        event_link_text: イベントリンクテキスト
        is_date: 日付のみフラグ
        service: Google Calendar APIのサービスインスタンス
    """
    if is_date:
        event = {
            "summary": summary,
            "description": event_link_text + "\n" + active_members,
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
            "description": event_link_text + "\n" + active_members,
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
    Googleカレンダーからイベントを削除する。
    Args:
        service: Google Calendar APIのサービスインスタンス
        calendar_id: カレンダーID
        previous_add_event_lists: 追加済みのイベントリスト
    """
    for event in previous_add_event_lists:
        # 25時～28時表記のイベントを考慮するため、翌月4時まで取得対象とする
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
    イベント開始時間を日本時間への変換する。
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
