from dependencies import time, requests, BeautifulSoup
import text_processing
"""
ウェブスクレイピングモジュール
"""

def fetch_url_content(year, month):
    """
    指定年月のURLからのコンテンツを取得する。
    
    Args:
        year (str): 取得コンテンツの年
        month (str): 取得コンテンツの月
    """
    # URLの組み立てとリクエスト送信、BeautifulSoupオブジェクトの返却
    url = f"https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy={year}{month}"
    response = requests.get(url)
    return BeautifulSoup(response.content, features="lxml")

def validate_date(soup, year, month):
    """
    ページの年月と指定年月が一致するか検証する。
    
    Args:
        soup (BeautifulSoup): 解析HTML用BeautifulSoupオブジェクト
        year (str): 検証する年
        month (str): 検証する月
    """
    # ページからの年月抽出と指定年月との一致確認
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
    指定月のスケジュールを取得する。
    
    Args:
        year (str): 取得したいスケジュールの年
        month (str): 取得したいスケジュールの月
    """
    # URLからのコンテンツ取得と日付検証
    soup = fetch_url_content(year, month)
    if not validate_date(soup, year, month):
        return

    # スケジュール情報を含むHTML要素の取得
    events_each_date = soup.find_all("div", {"class": "p-schedule__list-group"})
    time.sleep(3)  # サーバー負荷軽減のための待機
    return events_each_date

def get_events_from_hnz_hp(event_each_date):
    """
    特定日のイベントを一括取得する。
    
    Args:
        event_each_date (bs4.element.Tag): イベント情報を含むHTMLタグ
    """
    # 日付とイベント情報の抽出
    event_date_text = text_processing.remove_blank(event_each_date.contents[1].text)[:-1]
    events_time = event_each_date.find_all("div", {"class": "c-schedule__time--list"})
    events_name = event_each_date.find_all("p", {"class": "c-schedule__text"})
    events_category = event_each_date.find_all("div", {"class": "p-schedule__head"})
    events_link = event_each_date.find_all("li", {"class": "p-schedule__item"})

    return event_date_text, events_time, events_name, events_category, events_link

def get_time_event_from_event_info(event_time_text):
    """
    イベントの開始・終了時刻を取得する。
    
    Args:
        event_time_text (str): イベントの開始、終了時刻
    """
    # 開始時間と終了時間の抽出
    has_end = event_time_text[-1] != "~"
    start, end = (event_time_text.split("~") + [""])[:2]
    start += ":00"
    end += ":00" if has_end else start
    return start, end

