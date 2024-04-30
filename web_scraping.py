from dependencies import time, requests, BeautifulSoup
import text_processing


def get_month_schedule_from_hnz_hp(year, month):
    """
    指定した月のスケジュールを日向坂46公式HPから取得します。
    """
    url = (
        f"https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy={year}{month}"
    )
    result = requests.get(url)
    soup = BeautifulSoup(result.content, features="lxml")

    # ページの年と月を取得
    page_year = text_processing.remove_blank(
        soup.find("div", {"class": "c-schedule__page_year"}).text
    ).replace("年", "")
    page_month = text_processing.remove_blank(
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


def get_events_from_hnz_hp(event_each_date):
    """
    特定の日のイベントを一括で日向坂46公式HPから取得します。
    """
    event_date_text = text_processing.remove_blank(event_each_date.contents[1].text)[
        :-1
    ]  # 曜日以外の情報を取得
    events_time = event_each_date.find_all("div", {"class": "c-schedule__time--list"})
    events_name = event_each_date.find_all("p", {"class": "c-schedule__text"})
    events_category = event_each_date.find_all("div", {"class": "p-schedule__head"})
    events_link = event_each_date.find_all("li", {"class": "p-schedule__item"})

    return event_date_text, events_time, events_name, events_category, events_link


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
