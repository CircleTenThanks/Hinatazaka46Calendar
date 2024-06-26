from dependencies import re, mojimoji, datetime, requests, BeautifulSoup, time
from web_scraping import get_time_event_from_event_info
"""
このモジュールは、テキスト処理機能を提供します。主な機能は以下の通りです：
- テキストからの空白削除
- 全角文字の半角文字への変換
- ウェブスクレイピングで取得したHTMLからテキスト情報の抽出と整形
これにより、他のモジュールで扱いやすい形式のデータを提供します。
"""

def remove_blank(text):
    """
    テキストから空白を削除し、全角文字を半角に変換します。
    
    Args:
        text (str): 変換するテキスト。
        
    Returns:
        str: 変換後のテキスト。
    """
    text = text.replace("\n", "").strip()
    text = mojimoji.zen_to_han(text, kana=False)
    return text


def get_event_info_from_hnz_hp(event_name, event_category, event_time, event_link):
    """
    イベントの詳細情報を取得します。
    
    Args:
        event_name (bs4.element.Tag): イベント名を含むHTMLタグ。
        event_category (bs4.element.Tag): イベントカテゴリを含むHTMLタグ。
        event_time (bs4.element.Tag): イベント時間を含むHTMLタグ。
        event_link (bs4.element.Tag): イベントリンクを含むHTMLタグ。
        
    Returns:
        tuple: イベント名、カテゴリ、時間、リンクのテキスト情報。
    """
    event_name_text = remove_blank(event_name.text)
    event_category_text = remove_blank(event_category.contents[1].text)
    event_time_text = remove_blank(event_time.text)
    event_link_text = f"https://www.hinatazaka46.com{event_link.find('a')['href']}"

    return event_name_text, event_category_text, event_time_text, event_link_text


def get_event_member_from_event_info(event_link_text):
    """
    イベントに登録されているメンバーを取得します。
    
    Args:
        event_link_text (str): イベントの詳細ページのURL。
        
    Returns:
        str: 取得したメンバーのテキスト情報。メンバーがいない場合は空文字列を返します。
    """
    try:
        result = requests.get(event_link_text)
        soup = BeautifulSoup(result.content, features="lxml")
        active_members = soup.find("div", {"class": "c-article__tag"}).findAll("a")

        if not active_members:
            return ""

        members_text = "メンバー:" + ",".join(member.text for member in active_members)
        time.sleep(3)  # サーバーへの負荷を軽減するために3秒間待機
    except AttributeError:
        return ""

    return members_text


def prepare_info_for_calendar(
    year, month, event_name_text, event_category_text, event_time_text, event_date_text
):
    """
    Googleカレンダーに登録する情報を整形します。
    
    Args:
        year (int): イベントの年。
        month (int): イベントの月。
        event_name_text (str): イベント名。
        event_category_text (str): イベントカテゴリ。
        event_time_text (str): イベント時間。
        event_date_text (str): イベント日。
        
    Returns:
        tuple: イベントタイトル、開始日時、終了日時、日付のみかどうかのフラグ。
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
    24H以上の時刻をdatetimeに変換する。
    
    Args:
        year (int): 年。
        month (int): 月。
        day (int): 日。
        times (str): 時刻文字列。
        
    Returns:
        str: ISO 8601形式の日時文字列。
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
