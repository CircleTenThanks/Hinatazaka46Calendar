import datetime
import requests
from bs4 import BeautifulSoup
import time
from hinatazaka_scraper import get_time_event_from_event_info
from text_formatter import remove_blank
"""
イベントフォーマッターモジュール
"""

def get_event_info_from_hnz_hp(event_name, event_category, event_time, event_link):
    """
    イベント詳細情報を取得する
    """
    event_name_text = remove_blank(event_name.text)
    event_category_text = remove_blank(event_category.contents[1].text)
    event_time_text = remove_blank(event_time.text)
    event_link_text = f"https://www.hinatazaka46.com{event_link.find('a')['href']}"

    return event_name_text, event_category_text, event_time_text, event_link_text

def get_event_member_from_event_info(event_link_text):
    """
    イベント登録メンバーを取得する
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
    Googleカレンダー登録情報を整形する
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

def over24Hdatetime(year, month, day, times):
    """
    24H以上の表記の時刻をdatetimeに変換する
    """
    if times.count(":") == 2:
        hour, minute = times.split(":")[:-1]
    else:
        times_arr = re.search(r"(\d\d)(\d\d)", times)
        if times_arr != None:
            hour = times_arr[1]
            minute = times_arr[2]
        else:
            hour = 0
            minute = 0

    minutes = int(hour) * 60 + int(minute)
    dt = datetime.datetime(year=int(year), month=int(month), day=int(day))
    dt += datetime.timedelta(minutes=minutes)

    return dt.strftime("%Y-%m-%dT%H:%M:%S")