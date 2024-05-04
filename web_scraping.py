from dependencies import time, requests, BeautifulSoup
import text_processing
"""
このモジュールは、ウェブスクレイピングを行い、日向坂46の公式ホームページからスケジュールやニュースを取得するための関数を提供します。
主な機能は以下の通りです：
- 日向坂46の公式ホームページからスケジュールを取得
- 日向坂46の公式ホームページからニュースを取得
これにより、ユーザーは日向坂46の最新のスケジュールやニュースを常に確認することができます。
"""
def fetch_url_content(year, month, content_type="schedule"):
    """
    指定された年月のURLからコンテンツを取得します。
    
    Args:
        year (str): 取得するコンテンツの年。
        month (str): 取得するコンテンツの月。
        content_type (str): 取得するコンテンツのタイプ（'schedule' または 'news'）。
    """
    # コンテンツタイプに応じてURLを組み立てます。
    if content_type == "schedule":
        url = f"https://www.hinatazaka46.com/s/official/media/list?ima=0000&dy={year}{month}"
    elif content_type == "news":
        url = f"https://www.hinatazaka46.com/s/official/news/list?ima=0000&cd=event&dy={year}{month}"
    else:
        raise ValueError("Invalid content type specified. Use 'schedule' or 'news'.")
    
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

def get_month_content_from_hnz_hp(year, month, content_type="schedule"):
    """
    指定した月のスケジュールまたはニュースを日向坂46公式HPから取得します。
    
    Args:
        year (str): コンテンツを取得する年。
        month (str): コンテンツを取得する月。
        content_type (str): 取得するコンテンツのタイプ（'schedule' または 'news'）。
    """
    # URLからコンテンツを取得します。
    soup = fetch_url_content(year, month, content_type)
    
    # content_typeが'schedule'の場合のみ日付の検証を行います。
    if content_type == "schedule":
        if not validate_date(soup, year, month):
            return

    # content_typeに応じてスケジュール情報を含むHTML要素を取得します。
    if content_type == "schedule":
        content_each_date = soup.find_all("div", {"class": "p-schedule__list-group"})
    elif content_type == "news":
        content_each_date = soup.find_all("ul", {"class": "p-news__list"})
    else:
        raise ValueError("Invalid content type specified. Use 'schedule' or 'news'.")

    time.sleep(3)  # サーバーへの負荷を軽減するために3秒間待機します。
    return content_each_date

def get_contents_from_hnz_hp(content_each_date, content_type="schedule"):
    """
    特定の日のスケジュールまたはニュースを一括で日向坂46公式HPから取得します。
    
    Args:
        content_each_date (bs4.element.Tag): 特定の日に関するスケジュール情報またはニュース情報を含むHTMLタグ。
        content_type (str): コンテンツのタイプ（'schedule' または 'news'）。
    """
    try:
        if content_type == "schedule":
            # 特定の日付とその日のイベント情報を抽出します。
            content_date_text = text_processing.remove_blank(content_each_date.contents[1].text)[:-1]
            contents_time = content_each_date.find_all("div", {"class": "c-schedule__time--list"})
            contents_name = content_each_date.find_all("p", {"class": "c-schedule__text"})
            contents_category = content_each_date.find_all("div", {"class": "c-schedule__category"})
            contents_link = content_each_date.find_all("li", {"class": "p-schedule__item"})
        elif content_type == "news":
            # ニュースタイプの情報を抽出し、日付のフォーマットを整形します。
            content_date_text = [date.text.split(".")[2] for date in content_each_date.find_all("time", {"class": "c-news__date"})]
            contents_time = None
            contents_name = content_each_date.find_all("p", {"class": "c-news__text"})
            contents_category = content_each_date.find_all("div", {"class": "c-news__category"})
            contents_link = content_each_date.find_all("li", {"class": "p-news__item"})
        else:
            raise ValueError("Invalid content type specified. Use 'schedule' or 'news'.")

        return content_date_text, contents_time, contents_name, contents_category, contents_link
    except Exception as e:
        if content_type == "schedule":
            print("スケジュールがありませんでした")
        elif content_type == "news":
            print("ニュースがありませんでした")
        return None, None, None, None, None
    
def get_time_content_from_content_info(content_time_text):
    """
    コンテンツの開始時間と終了時間を取得します。
    
    Args:
        content_time_text (str): コンテンツの時間を表すテキスト。
    """
    # コンテンツの時間テキストから開始時間と終了時間を抽出します。
    has_end = content_time_text[-1] != "~"
    start, end = (content_time_text.split("~") + [""])[:2]
    start += ":00"
    end += ":00" if has_end else start
    return start, end

def get_event_description(event_link_text, content_dt, content_type="schedule"):
    """
    イベントに登録されているメンバーを取得します。
    
    Args:
        event_link_text (str): イベントの詳細ページのURL。
        
    Returns:
        str: 取得したメンバーのテキスト情報。メンバーがいない場合は空文字列を返します。
    """
    try:
        if content_type == "schedule":
            result = requests.get(event_link_text)
            soup = BeautifulSoup(result.content, features="lxml")
            active_members = soup.find("div", {"class": "c-article__tag"}).findAll("a")

            if not active_members:
                return ""

            description = "メンバー:" + ",".join(member.text for member in active_members)
        elif content_type == "news":
            result = requests.get(event_link_text)
            soup = BeautifulSoup(result.content, features="lxml")
            description = soup.find("div", {"class": "p-article__text"}).text

            # 文字列から日時を抽出して表示
            try:
                section_text = text_processing.extract_section_text(description, "日程")
                if section_text != "":
                    extracted_datetimes = text_processing.parse_datetimes(section_text, content_dt)
                    for dt in extracted_datetimes:
                        print(f"Datetime: {dt}")
            except ValueError as e:
                print(f"Error: {e}")

            if not description:
                return ""
        else:
            raise ValueError("Invalid content type specified. Use 'schedule' or 'news'.")
    except AttributeError:
        return ""
    
    time.sleep(3)  # サーバーへの負荷を軽減するために3秒間待機
    return description
