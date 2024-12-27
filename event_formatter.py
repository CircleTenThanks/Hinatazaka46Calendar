import datetime
import requests
from bs4 import BeautifulSoup
import time
import re
from hinatazaka_scraper import get_time_event_from_event_info
from text_formatter import remove_blank

"""
イベントフォーマッターモジュール
"""

def get_event_info_from_hnz_hp(event_name, event_category, event_time, event_link):
    """
    イベント詳細情報を取得する
    
    Args:
        event_name (bs4.element.Tag): イベント名のHTMLタグ
        event_category (bs4.element.Tag): イベントカテゴリのHTMLタグ
        event_time (bs4.element.Tag): イベント時間のHTMLタグ
        event_link (bs4.element.Tag): イベントリンクのHTMLタグ
        
    Returns:
        tuple: イベント名、カテゴリ、時間、リンクのテキスト情報
    """
    event_name_text = remove_blank(event_name.text)
    event_category_text = remove_blank(event_category.contents[1].text)
    event_time_text = remove_blank(event_time.text)
    event_link_text = f"https://www.hinatazaka46.com{event_link.find('a')['href']}"

    return event_name_text, event_category_text, event_time_text, event_link_text

def get_event_member_from_event_info(event_link_text):
    """
    イベント登録メンバーを取得する
    
    Args:
        event_link_text (str): イベント詳細ページのURL
        
    Returns:
        str: メンバーのテキスト情報。メンバー未登録時は空文字列。
    """
    try:
        result = requests.get(event_link_text)
        soup = BeautifulSoup(result.content, features="lxml")
        active_members = soup.find("div", {"class": "c-article__tag"}).findAll("a")

        if not active_members:
            return ""

        members_text = "メンバー:" + ",".join(member.text for member in active_members)
        time.sleep(3)
    except AttributeError:
        return ""

    return members_text

def prepare_info_for_calendar(year, month, event_name_text, event_category_text, event_time_text, event_date_text):
    """
    Googleカレンダー登録情報を整形する。
    
    Args:
        year (int): イベント年
        month (int): イベント月
        event_name_text (str): イベント名
        event_category_text (str): イベントカテゴリ
        event_time_text (str): イベント時間
        event_date_text (str): イベント日
        
    Returns:
        tuple: イベントタイトル、開始日時、終了日時、日付のみかを示すフラグ。
    """
    month_text = "{:0=2}".format(int(month))

    event_title = f"({event_category_text}){event_name_text}"
    if not event_time_text:
        event_start = f"{year}-{month_text}-{event_date_text}"
        event_end = f"{year}-{month_text}-{event_date_text}"
        is_date = True
    else:
        start, end = get_time_event_from_event_info(event_time_text)
        event_start = over24Hdatetime(year, month, event_date_text, start)
        event_end = over24Hdatetime(year, month, event_date_text, end)
        is_date = False
    return event_title, event_start, event_end, is_date

def over24Hdatetime(year: int, month: int, day: str, times: str) -> str:
    """
    24H以上の表記の時刻をdatetimeに変換する
    
    Args:
        year (int): 年
        month (int): 月
        day (str): 日
        times (str): 時刻文字列
        
    Returns:
        str: ISO形式の日時文字列
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
    dt = datetime.datetime(year=int(year), month=int(month), day=int(day))
    dt += datetime.timedelta(minutes=minutes)

    return dt.strftime("%Y-%m-%dT%H:%M:%S")