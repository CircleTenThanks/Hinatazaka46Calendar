import time
import pickle
import os
from tendo import singleton
import mojimoji
import re

import requests
from bs4 import BeautifulSoup

import datetime
from dateutil.relativedelta import relativedelta

from googleapiclient.discovery import build
from google.oauth2 import service_account
from google.auth.transport.requests import Request


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


def remove_blank(text):
    """
    テキストから空白を削除し、全角文字を半角に変換します。
    """
    text = text.replace("\n", "")
    text = re.sub("^ +", "", text)
    text = re.sub(" +$", "", text)
    text = mojimoji.zen_to_han(text, kana=False)
    return text


def get_month_schedule_from_hnz_hp(year, month):
    """
    指定した月のスケジュールを取得します。
    """
    url = (
        f"https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy={year}{month}"
    )
    result = requests.get(url)
    soup = BeautifulSoup(result.content, features="lxml")

    # ページの年と月を取得
    page_year = remove_blank(
        soup.find("div", {"class": "c-schedule__page_year"}).text
    ).replace("年", "")
    page_month = remove_blank(
        soup.find("div", {"class": "c-schedule__page_month"}).text
    ).replace("月", "")

    # 年と月が一致しない場合はエラー
    if int(year) != int(page_year) or int(month) != int(page_month):
        print("Error URL")
        return

    # 各日付のイベントを取得
    events_each_date = soup.find_all("div", {"class": "p-schedule__list-group"})

    # サーバーへの負荷を解消するために一時停止
    time.sleep(3)

    return events_each_date


def get_time_event_from_event_info(event_time_text):
    """
    イベントの開始時間と終了時間を取得します。
    """
    # 終了時間が存在するか確認
    has_end = event_time_text[-1] != "~"
    if has_end:
        start, end = event_time_text.split("~")
    else:
        start = end = event_time_text.split("~")[0]
    start += ":00"
    end += ":00"
    return start, end


def get_events_from_hnz_hp(event_each_date):
    """
    特定の日のイベントを一括で取得します。
    """
    event_date_text = remove_blank(event_each_date.contents[1].text)[
        :-1
    ]  # 曜日以外の情報を取得
    events_time = event_each_date.find_all("div", {"class": "c-schedule__time--list"})
    events_name = event_each_date.find_all("p", {"class": "c-schedule__text"})
    events_category = event_each_date.find_all("div", {"class": "p-schedule__head"})
    events_link = event_each_date.find_all("li", {"class": "p-schedule__item"})

    return event_date_text, events_time, events_name, events_category, events_link


def get_event_info_from_hnz_hp(event_name, event_category, event_time, event_link):
    """
    イベントの詳細情報を取得します。
    """
    event_name_text = remove_blank(event_name.text)
    event_category_text = remove_blank(event_category.contents[1].text)
    event_time_text = remove_blank(event_time.text)
    event_link_text = f"https://www.hinatazaka46.com{event_link.find('a')['href']}"

    return event_name_text, event_category_text, event_time_text, event_link_text


def get_event_member_from_event_info(event_link_text):
    """
    イベントに登録されているメンバーを取得します。
    """
    try:
        result = requests.get(event_link_text)
        soup = BeautifulSoup(result.content, features="lxml")
        active_members = soup.find("div", {"class": "c-article__tag"}).findAll("a")

        if active_members is None:
            return ""

        members_text = "メンバー:" + ",".join(member.text for member in active_members)
        time.sleep(3)  # サーバー負荷の解消
    except AttributeError:
        return ""

    return members_text


def over24Hdatetime(year, month, day, times):
    """
    24H以上の時刻をdatetimeに変換する
    """
    if times.count(":") == 2:
        hour, minute = times.split(":")[:-1]
    else:
        # 1900 という表記の時がある
        times_arr = re.search(r"(\d\d)(\d\d)", times)
        if times_arr != None:
            hour = times_arr[1]
            minute = times_arr[2]
        else:
            hour = 0
            minute = 0

    # to minute
    minutes = int(hour) * 60 + int(minute)

    dt = datetime.datetime(year=int(year), month=int(month), day=int(day))
    dt += datetime.timedelta(minutes=minutes)

    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def prepare_info_for_calendar(event_name_text, event_category_text, event_time_text):

    month_text = "{:0=2}".format(int(month))

    event_title = f"({event_category_text}){event_name_text}"
    if event_time_text == "":
        event_start = f"{year}-{month_text}-{event_date_text}"
        event_end = f"{year}-{month_text}-{event_date_text}"
        is_date = True
    else:
        start, end = get_time_event_from_event_info(event_time_text)
        event_start = over24Hdatetime(year, month, event_date_text, start)
        event_end = over24Hdatetime(year, month, event_date_text, end)
        is_date = False
    return event_title, event_start, event_end, is_date


def change_event_starttime_to_jst(event):

    if "date" in event["start"].keys():
        return event["start"]["date"]
    else:
        str_event_uct_time = event["start"]["dateTime"]
        event_jst_time = datetime.datetime.strptime(
            str_event_uct_time, "%Y-%m-%dT%H:%M:%S+09:00"
        )
        str_event_jst_time = event_jst_time.strftime("%Y-%m-%dT%H:%M:%S")
        return str_event_jst_time


def get_schedule_from_google_calendar(service, calendar_id, year, month):
    """
    Googleカレンダーから指定された年月のスケジュールを取得します(重複してスケジュールを登録してしまうのを防ぐ目的)
    """
    timezone = "Asia/Tokyo"

    # JSTタイムゾーンでの開始日時と終了日時を設定します
    start_time = datetime.datetime(
        year, month, 1, tzinfo=datetime.timezone(datetime.timedelta(hours=9))
    )
    # 25時～28時表記になっていた場合を考慮して翌月の4時までを取得対象とする
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
    event_name, event_category, event_time, event_link, previous_add_event_lists
):
    """
    Googleカレンダーにイベントを登録します。
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
        event_name_text,
        event_category_text,
        event_time_text,
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
            event["hnz_hp_checked"] = True
            break

    if found_index is not None:  # NOTE:同じ予定がすでに存在する場合はパス
        print("pass:" + event_start + " " + event_title)
        pass
    else:
        active_members = get_event_member_from_event_info(event_link_text)
        print("add:" + event_start + " " + event_title)
        build_google_calendar_format(
            calendarId,
            event_title,
            event_start,
            event_end,
            active_members,
            event_link_text,
            is_date,
        )


def build_google_calendar_format(
    calendarId, summary, start, end, active_members, event_link_text, is_date
):

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
            calendarId=calendarId,
            body=event,
        )
        .execute()
    )


# me = singleton.SingleInstance()

# -------------------------step1:各種設定-------------------------
# API系
calendarId = os.environ["CALENDAR_ID_HNZ"]  # NOTE:自分のカレンダーID
service = build_google_calendar_api()

# サーチ範囲
num_search_month = 3  # NOTE;3ヶ月先の予定までカレンダーに反映
current_search_date = datetime.datetime.now()
year = current_search_date.year
month = current_search_date.month

# -------------------------step2.各日付ごとの情報を取得-------------------------
for _ in range(num_search_month):
    events_each_date = get_month_schedule_from_hnz_hp(year, "{:0=2}".format(int(month)))
    if events_each_date == None:
        continue
    for event_each_date in events_each_date:

        # step3: 特定の日の予定を一括で取得
        (
            event_date_text,
            events_time,
            events_name,
            events_category,
            events_link,
        ) = get_events_from_hnz_hp(event_each_date)

        event_date_text = "{:0=2}".format(
            int(event_date_text)
        )  # NOTE;2桁になるように0埋め（ex.0-> 01）

        previous_add_event_lists = get_schedule_from_google_calendar(
            service, calendarId, year, month
        )

        # step4: カレンダーへ情報を追加
        for event_name, event_category, event_time, event_link in zip(
            events_name, events_category, events_time, events_link
        ):
            add_event_to_google_calendar(
                event_name,
                event_category,
                event_time,
                event_link,
                previous_add_event_lists,
            )

    # step5:次の月へ
    current_search_date = current_search_date + relativedelta(months=1)
    year = current_search_date.year
    month = current_search_date.month
