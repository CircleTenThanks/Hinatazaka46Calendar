from dependencies import time, requests, BeautifulSoup
import text_processing
"""
このモジュールは、ウェブスクレイピングを行い、日向坂46の公式ホームページからイベントスケジュールを取得するための関数を提供します。
主な機能は以下の通りです：
- 日向坂46の公式ホームページからイベントスケジュールを取得
これにより、ユーザーは日向坂46の最新のスケジュールを常に確認することができます。
"""
def fetch_url_content(year, month, url_type="media"):
    """
    指定された年月のURLからコンテンツを取得します。
    
    Args:
        year (str): 取得するコンテンツの年。
        month (str): 取得するコンテンツの月。
        url_type (str): 取得するコンテンツのタイプ（'media' または 'news'）。
    """
    # URLタイプに応じてURLを組み立てます。
    if url_type == "media":
        url = f"https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy={year}{month}"
    elif url_type == "news":
        url = f"https://www.hinatazaka46.com/s/official/news/list?ima=0000&dy={year}{month}"
    else:
        raise ValueError("Invalid URL type specified. Use 'media' or 'news'.")
    
    # リクエストを送信し、BeautifulSoupオブジェクトを返します。
    response = requests.get(url)
    return BeautifulSoup(response.content, features="lxml")

def validate_date(soup, year, month):
    """
    ページの年と月が指定された年月と一致するか検証します。
    
    Args:
        soup (BeautifulSoup): 解析するHTMLのBeautifulSoupオブジェクト。
        year (str): 検証する年。
        month (str): 検証する月。
    """
    # ページから年と月を抽出し、指定された年月と一致するか確認します。
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

def get_month_schedule_from_hnz_hp(year, month, content_type="media"):
    """
    指定した月のスケジュールを日向坂46公式HPから取得します。
    
    Args:
        year (str): スケジュールを取得する年。
        month (str): スケジュールを取得する月。
        content_type (str): 取得するコンテンツのタイプ（'media' または 'news'）。
    """
    # URLからコンテンツを取得し、日付の検証を行います。
    soup = fetch_url_content(year, month, content_type)
    if not validate_date(soup, year, month):
        return

    # content_typeに応じてスケジュール情報を含むHTML要素を取得します。
    if content_type == "media":
        events_each_date = soup.find_all("div", {"class": "p-schedule__list-group"})
    elif content_type == "news":
        events_each_date = soup.find_all("div", {"class": "p-news__list"})
    else:
        raise ValueError("Invalid content type specified. Use 'media' or 'news'.")

    time.sleep(3)  # サーバーへの負荷を軽減するために3秒間待機します。
    return events_each_date

def get_events_from_hnz_hp(event_each_date):
    """
    特定の日のイベントを一括で日向坂46公式HPから取得します。
    
    Args:
        event_each_date (bs4.element.Tag): 特定の日に関するイベント情報を含むHTMLタグ。
    """
    # 特定の日付とその日のイベント情報を抽出します。
    event_date_text = text_processing.remove_blank(event_each_date.contents[1].text)[:-1]
    events_time = event_each_date.find_all("div", {"class": "c-schedule__time--list"})
    events_name = event_each_date.find_all("p", {"class": "c-schedule__text"})
    events_category = event_each_date.find_all("div", {"class": "p-schedule__head"})
    events_link = event_each_date.find_all("li", {"class": "p-schedule__item"})

    return event_date_text, events_time, events_name, events_category, events_link

def get_time_event_from_event_info(event_time_text):
    """
    イベントの開始時間と終了時間を取得します。
    
    Args:
        event_time_text (str): イベントの時間を表すテキスト。
    """
    # イベントの時間テキストから開始時間と終了時間を抽出します。
    has_end = event_time_text[-1] != "~"
    start, end = (event_time_text.split("~") + [""])[:2]
    start += ":00"
    end += ":00" if has_end else start
    return start, end

