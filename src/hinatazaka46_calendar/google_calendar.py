# Copyright (c) 2020 ddn
# Copyright (c) 2026 CircleTenThanks
# 一部は https://qiita.com/ddn/items/42def5fa721e531eecdb を基に改変している.
"""Google Calendar APIを使用したカレンダー操作."""

import datetime
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build

from .event_formatter import (
    CalendarEventTimes,
    EventDate,
    get_event_info_from_hnz_hp,
    get_event_member_from_event_info,
    prepare_info_for_calendar,
)

if TYPE_CHECKING:
    from bs4 import Tag

LOGGER = logging.getLogger(__name__)
_CALENDAR_SCOPES = ("https://www.googleapis.com/auth/calendar",)
_CREDENTIALS_PATH = Path("credentials_hnz.json")
_JST = datetime.timezone(datetime.timedelta(hours=9))
_DECEMBER = 12
_OVERNIGHT_END_HOUR = 4
_FIRST_DAY = 1


@dataclass(frozen=True)
class ScrapedEvent:
    """公式HPから取得した1件のイベント."""

    year: int
    month: int
    date_text: str
    name: Tag
    category: Tag
    time: Tag
    link: Tag


def build_google_calendar_api() -> Resource:
    """Google Calendar APIクライアントを生成する.

    Returns:
        Google Calendar APIのサービスインスタンス。
    """
    creds = service_account.Credentials.from_service_account_file(
        str(_CREDENTIALS_PATH),
        scopes=_CALENDAR_SCOPES,
    )
    return build("calendar", "v3", credentials=creds)


def get_schedule_from_google_calendar(
    service: Resource,
    calendar_id: str,
    year: int,
    month: int,
) -> list[dict]:
    """指定年月のスケジュールを取得する.

    スケジュールを重複して登録しないように既存イベントを返す。

    Args:
        service: Google Calendar APIのサービスインスタンス。
        calendar_id: カレンダーID。
        year: 取得年。
        month: 取得月。

    Returns:
        既存イベントのリスト。
    """
    timezone = "Asia/Tokyo"
    start_time = datetime.datetime(year, month, _FIRST_DAY, tzinfo=_JST)
    if month == _DECEMBER:
        end_time = datetime.datetime(
            year + 1,
            1,
            _FIRST_DAY,
            _OVERNIGHT_END_HOUR,
            tzinfo=_JST,
        )
    else:
        end_time = datetime.datetime(
            year,
            month + 1,
            _FIRST_DAY,
            _OVERNIGHT_END_HOUR,
            tzinfo=_JST,
        )

    events_result = (
        service
        .events()
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

    for event in events:
        event["startTimeJST"] = change_event_starttime_to_jst(event)
        event["hnz_hp_checked"] = False
    return events


def add_event_to_google_calendar(
    service: Resource,
    calendar_id: str,
    scraped: ScrapedEvent,
    existing_calendar_events: list[dict],
) -> None:
    """Googleカレンダーへイベントを登録する.

    Args:
        service: Google Calendar APIのサービスインスタンス。
        calendar_id: カレンダーID。
        scraped: 公式HPから取得したイベント。
        existing_calendar_events: 既に追加済みのイベントリスト。
    """
    (
        event_name_text,
        event_category_text,
        event_time_text,
        event_link_text,
    ) = get_event_info_from_hnz_hp(
        scraped.name,
        scraped.category,
        scraped.time,
        scraped.link,
    )
    times = prepare_info_for_calendar(
        EventDate(year=scraped.year, month=scraped.month, day=scraped.date_text),
        event_name_text,
        event_category_text,
        event_time_text,
    )

    found_index = _find_existing_event_index(
        existing_calendar_events,
        times.title,
        times.start,
    )
    if found_index is not None:
        existing_calendar_events[found_index]["hnz_hp_checked"] = True
        LOGGER.info("pass:%s %s", times.start, times.title)
        return

    active_members = get_event_member_from_event_info(event_link_text)
    LOGGER.info("add:%s %s", times.start, times.title)
    build_google_calendar_format(
        service, calendar_id, times, active_members, event_link_text
    )


def _find_existing_event_index(
    existing_calendar_events: list[dict],
    event_title: str,
    event_start: str,
) -> int | None:
    """一致する既存イベントのインデックスを返す.

    Returns:
        一致したインデックス. なければ None.
    """
    for index, event in enumerate(existing_calendar_events):
        if (
            event.get("summary") == event_title
            and event.get("startTimeJST") == event_start
        ):
            return index
    return None


def build_google_calendar_format(
    service: Resource,
    calendar_id: str,
    times: CalendarEventTimes,
    active_members: str,
    event_link_text: str,
) -> None:
    """Googleカレンダー登録形式へデータを整形して登録する.

    Args:
        service: Google Calendar APIのサービスインスタンス。
        calendar_id: カレンダーID。
        times: 登録する日時情報。
        active_members: 参加メンバー。
        event_link_text: イベントリンクテキスト。
    """
    date_key = "date" if times.is_date else "dateTime"
    event = {
        "summary": times.title,
        "description": event_link_text + "\n" + active_members,
        "start": {
            date_key: times.start,
            "timeZone": "Japan",
        },
        "end": {
            date_key: times.end,
            "timeZone": "Japan",
        },
    }
    service.events().insert(calendarId=calendar_id, body=event).execute()


def remove_event_from_google_calendar(
    service: Resource,
    calendar_id: str,
    previous_add_event_lists: list[dict],
) -> None:
    """Googleカレンダーからイベントを削除する.

    Args:
        service: Google Calendar APIのサービスインスタンス。
        calendar_id: カレンダーID。
        previous_add_event_lists: 追加済みのイベントリスト。
    """
    for event in previous_add_event_lists:
        start_jst = datetime.datetime.fromisoformat(event["startTimeJST"])
        if start_jst.day == _FIRST_DAY and start_jst.day <= _OVERNIGHT_END_HOUR:
            continue
        if not event["hnz_hp_checked"]:
            service.events().delete(
                calendarId=calendar_id,
                eventId=event["id"],
            ).execute()
            LOGGER.info("del:%s %s", event["startTimeJST"], event["summary"])


def change_event_starttime_to_jst(event: dict) -> str:
    """イベント開始時間を日本時間へ変換する.

    Args:
        event: イベントデータ。

    Returns:
        JSTの日付または日時文字列。
    """
    if "date" in event["start"]:
        return event["start"]["date"]

    str_event_uct_time = event["start"]["dateTime"]
    event_jst_time = datetime.datetime.strptime(
        str_event_uct_time,
        "%Y-%m-%dT%H:%M:%S%z",
    )
    return event_jst_time.strftime("%Y-%m-%dT%H:%M:%S")
