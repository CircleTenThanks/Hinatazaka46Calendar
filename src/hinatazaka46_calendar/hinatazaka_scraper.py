# Copyright (c) 2020 ddn
# Copyright (c) 2026 CircleTenThanks
# 一部は https://qiita.com/ddn/items/42def5fa721e531eecdb を基に改変している.
"""日向坂46公式HPからのスケジュール取得."""

import logging
import time
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup, Tag

from .text_formatter import remove_blank

if TYPE_CHECKING:
    from bs4.element import PageElement

LOGGER = logging.getLogger(__name__)
_REQUEST_TIMEOUT_SECONDS = 30
_SCRAPE_WAIT_SECONDS = 3


def fetch_url_content(year: str, month: str) -> BeautifulSoup:
    """指定年月のURLからコンテンツを取得する.

    Args:
        year: 取得コンテンツの年。
        month: 取得コンテンツの月。

    Returns:
        解析済みHTML。
    """
    url = (
        f"https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy={year}{month}"
    )
    response = requests.get(url, timeout=_REQUEST_TIMEOUT_SECONDS)
    return BeautifulSoup(response.content, features="lxml")


def validate_date(soup: BeautifulSoup, year: str, month: str) -> bool:
    """ページの年月と指定年月が一致するか検証する.

    Args:
        soup: 解析HTML用BeautifulSoupオブジェクト。
        year: 検証する年。
        month: 検証する月。

    Returns:
        年月が一致すれば True。
    """
    page_year = remove_blank(
        soup.find("div", {"class": "c-schedule__page_year"}).text
    ).replace("年", "")
    page_month = remove_blank(
        soup.find("div", {"class": "c-schedule__page_month"}).text
    ).replace("月", "")

    if int(year) != int(page_year) or int(month) != int(page_month):
        LOGGER.info("Error URL")
        return False
    return True


def get_month_schedule_from_hnz_hp(year: str, month: str) -> list[Tag] | None:
    """指定月のスケジュールを取得する.

    Args:
        year: 取得したいスケジュールの年。
        month: 取得したいスケジュールの月。

    Returns:
        日ごとのスケジュール要素。取得できない場合は None。
    """
    soup = fetch_url_content(year, month)
    if not validate_date(soup, year, month):
        return None

    events_each_date = soup.find_all("div", {"class": "p-schedule__list-group"})
    time.sleep(_SCRAPE_WAIT_SECONDS)
    return events_each_date


def get_events_from_hnz_hp(
    event_each_date: Tag,
) -> tuple[
    str, list[PageElement], list[PageElement], list[PageElement], list[PageElement]
]:
    """特定日のイベントを一括取得する.

    Args:
        event_each_date: イベント情報を含むHTMLタグ。

    Returns:
        日付テキストとイベント要素のタプル。
    """
    event_date_text = remove_blank(event_each_date.contents[1].text)[:-1]
    events_time = event_each_date.find_all("div", {"class": "c-schedule__time--list"})
    events_name = event_each_date.find_all("p", {"class": "c-schedule__text"})
    events_category = event_each_date.find_all("div", {"class": "p-schedule__head"})
    events_link = event_each_date.find_all("li", {"class": "p-schedule__item"})

    return event_date_text, events_time, events_name, events_category, events_link


def get_time_event_from_event_info(event_time_text: str) -> tuple[str, str]:
    """イベントの開始・終了時刻を取得する.

    Args:
        event_time_text: イベントの開始、終了時刻。

    Returns:
        開始時刻と終了時刻。
    """
    has_end = event_time_text[-1] != "~"
    parts = event_time_text.split("~")
    start = parts[0]
    end = parts[1] if len(parts) > 1 else ""
    start += ":00"
    end += ":00" if has_end else start
    return start, end
