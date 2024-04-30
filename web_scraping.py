from dependencies import time, requests, BeautifulSoup
import text_processing

def fetch_url_content(year, month):
    """
    指定された年月のURLからコンテンツを取得します。
    """
    url = f"https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy={year}{month}"
    response = requests.get(url)
    return BeautifulSoup(response.content, features="lxml")

def validate_date(soup, year, month):
    """
    ページの年と月が指定された年月と一致するか検証します。
    """
    page_year = text_processing.remove_blank(
        soup.find("div", {"class": "c-schedule__page_year"}).text
    ).replace("年", "")
    page_month = text_processing.remove_blank(
        soup.find("div", {"class": "c-schedule__page_month"}).text
    ).replace("月", "")

    if int(year) != int(page_year) or int(month) != int(page_month):
        print("Error URL")
        return False
    return True

def get_month_schedule_from_hnz_hp(year, month):
    """
    指定した月のスケジュールを日向坂46公式HPから取得します。
    """
    soup = fetch_url_content(year, month)
    if not validate_date(soup, year, month):
        return

    events_each_date = soup.find_all("div", {"class": "p-schedule__list-group"})
    time.sleep(3)  # サーバーへの負荷を解消するために一時停止
    return events_each_date

def get_events_from_hnz_hp(event_each_date):
    """
    特定の日のイベントを一括で日向坂46公式HPから取得します。
    """
    event_date_text = text_processing.remove_blank(event_each_date.contents[1].text)[:-1]
    events_time = event_each_date.find_all("div", {"class": "c-schedule__time--list"})
    events_name = event_each_date.find_all("p", {"class": "c-schedule__text"})
    events_category = event_each_date.find_all("div", {"class": "p-schedule__head"})
    events_link = event_each_date.find_all("li", {"class": "p-schedule__item"})

    return event_date_text, events_time, events_name, events_category, events_link

def get_time_event_from_event_info(event_time_text):
    """
    イベントの開始時間と終了時間を取得します。
    """
    has_end = event_time_text[-1] != "~"
    start, end = (event_time_text.split("~") + [""])[:2]
    start += ":00"
    end += ":00" if has_end else start
    return start, end
