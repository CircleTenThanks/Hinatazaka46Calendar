# Copyright (c) 2020 ddn
# Copyright (c) 2026 CircleTenThanks
# 一部は https://qiita.com/ddn/items/42def5fa721e531eecdb を基に改変している.
"""イベント情報をGoogleカレンダー登録形式へ整形する."""

import datetime
import re
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup, Tag

from .hinatazaka_scraper import get_time_event_from_event_info
from .text_formatter import remove_blank

_REQUEST_TIMEOUT_SECONDS = 30
_SCRAPE_WAIT_SECONDS = 3
_JST = datetime.timezone(datetime.timedelta(hours=9))


@dataclass(frozen=True)
class EventDate:
    """イベントの年月日."""

    year: int
    month: int
    day: str


@dataclass(frozen=True)
class CalendarEventTimes:
    """カレンダー登録用のタイトルと日時."""

    title: str
    start: str
    end: str
    is_date: bool


def get_event_info_from_hnz_hp(
    event_name: Tag,
    event_category: Tag,
    event_time: Tag,
    event_link: Tag,
) -> tuple[str, str, str, str]:
    """イベント詳細情報を取得する.

    Args:
        event_name: イベント名のHTMLタグ。
        event_category: イベントカテゴリのHTMLタグ。
        event_time: イベント時間のHTMLタグ。
        event_link: イベントリンクのHTMLタグ。

    Returns:
        イベント名、カテゴリ、時間、リンクのテキスト情報。
    """
    event_name_text = remove_blank(event_name.text)
    event_category_text = remove_blank(event_category.contents[1].text)
    event_time_text = remove_blank(event_time.text)
    event_link_text = f"https://www.hinatazaka46.com{event_link.find('a')['href']}"

    return event_name_text, event_category_text, event_time_text, event_link_text


def _parse_member_names(soup: BeautifulSoup) -> str:
    """イベント詳細ページからメンバー名を組み立てる.

    Returns:
        メンバー名. 未登録なら空文字列.
    """
    active_members = soup.find("div", {"class": "c-article__tag"}).find_all("a")
    if not active_members:
        return ""
    return "メンバー:" + ",".join(member.text for member in active_members)


def get_event_member_from_event_info(event_link_text: str) -> str:
    """イベント登録メンバーを取得する.

    Args:
        event_link_text: イベント詳細ページのURL。

    Returns:
        メンバーのテキスト情報。メンバー未登録時は空文字列。
    """
    try:
        result = requests.get(event_link_text, timeout=_REQUEST_TIMEOUT_SECONDS)
        soup = BeautifulSoup(result.content, features="lxml")
        members_text = _parse_member_names(soup)
        time.sleep(_SCRAPE_WAIT_SECONDS)
    except AttributeError:
        return ""

    return members_text


def prepare_info_for_calendar(
    event_date: EventDate,
    event_name_text: str,
    event_category_text: str,
    event_time_text: str,
) -> CalendarEventTimes:
    """Googleカレンダー登録情報を整形する.

    Args:
        event_date: イベントの年月日。
        event_name_text: イベント名。
        event_category_text: イベントカテゴリ。
        event_time_text: イベント時間。

    Returns:
        イベントタイトルと開始・終了日時。
    """
    month_text = f"{int(event_date.month):02d}"
    event_title = f"({event_category_text}){event_name_text}"
    if not event_time_text:
        event_start = f"{event_date.year}-{month_text}-{event_date.day}"
        return CalendarEventTimes(
            title=event_title,
            start=event_start,
            end=event_start,
            is_date=True,
        )

    start, end = get_time_event_from_event_info(event_time_text)
    return CalendarEventTimes(
        title=event_title,
        start=convert_over24h_to_datetime(
            event_date.year, event_date.month, event_date.day, start
        ),
        end=convert_over24h_to_datetime(
            event_date.year, event_date.month, event_date.day, end
        ),
        is_date=False,
    )


def convert_over24h_to_datetime(year: int, month: int, day: str, times: str) -> str:
    """24時間以上の表記の時刻をdatetimeに変換する.

    Args:
        year: 年。
        month: 月。
        day: 日。
        times: 時刻文字列。

    Returns:
        ISO形式の日時文字列。
    """
    if ":" in times:
        hour, minute = times.split(":")[:2]
    else:
        match = re.search(r"(\d{2})(\d{2})", times)
        if match:
            hour, minute = match.groups()
        else:
            hour, minute = "0", "0"

    minutes = int(hour) * 60 + int(minute)
    dt = datetime.datetime(
        year=int(year),
        month=int(month),
        day=int(day),
        tzinfo=_JST,
    )
    dt += datetime.timedelta(minutes=minutes)

    return dt.strftime("%Y-%m-%dT%H:%M:%S")
