from dependencies import re, mojimoji, datetime, requests, BeautifulSoup, time
from web_scraping import get_time_content_from_content_info
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
    event_category_text = remove_blank(event_category.text)
    if event_time is not None:
        event_time_text = remove_blank(event_time.text)
    else:
        event_time_text = None
    event_link_text = f"https://www.hinatazaka46.com{event_link.find('a')['href']}"

    return event_name_text, event_category_text, event_time_text, event_link_text


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
        start, end = get_time_content_from_content_info(event_time_text)
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
def extract_section_text(text, section):
    """
    指定されたセクションのテキストを抽出する。

    Args:
        text (str): 全体のテキスト。
        section (str): 抽出するセクション名。

    Returns:
        str: 指定されたセクションのテキスト。
    """
    section_pattern = rf'\【{section}\】(.*?)\【'
    section_match = re.search(section_pattern, text + '【', re.DOTALL)
    if section_match:
        return section_match.group(1)
    else:
        return ""

def parse_datetimes(text, content_dt):
    """
    テキストから日時情報を解析してdatetimeオブジェクトのリストを返す。

    Args:
        text (str): 日時情報が含まれるテキスト。
        content_dt (datetime): 基準となる日時。

    Returns:
        list: datetimeオブジェクトのリスト。
    """
    text = remove_blank(text)
    date_pattern = r'(\d{1,2})[月/-](\d{1,2})'
    time_pattern = r'開場.*?(\d{1,2})[時:](\d{1,2}).*?開演.*?(\d{1,2})[時:](\d{1,2})'

    datetimes = []
    time_matches = re.findall(time_pattern, text)
    date_matches = re.findall(date_pattern, text)

    if len(time_matches) == 0:
        datetimes = handle_no_time_matches(date_matches, content_dt)
    elif len(time_matches) == 1:
        datetimes = handle_single_time_match(date_matches, time_matches, content_dt)
    else:
        datetimes = handle_multiple_time_matches(date_matches, time_matches, content_dt)

    if not datetimes:
        raise ValueError("No valid dates found in the text.")

    return datetimes

def handle_no_time_matches(date_matches, content_dt):
    """
    時間が抽出できなかった場合の日時オブジェクトのリストを生成する。

    Args:
        date_matches (list): 日付のマッチリスト。
        content_dt (datetime): 基準となる日時。

    Returns:
        list: 日時オブジェクトのリスト。
    """
    datetimes = []
    for month, day in date_matches:
        month, day = map(int, (month, day))
        datetime_obj = datetime.datetime(content_dt.year, month, day, 0, 0)
        if datetime_obj < content_dt:
            datetime_obj += datetime.timedelta(year=1)
        datetimes.append(("", datetime_obj))
    return datetimes

def handle_single_time_match(date_matches, time_matches, content_dt):
    """
    全ての日付が共通の時間を持つ場合の日時オブジェクトのリストを生成する。

    Args:
        date_matches (list): 日付のマッチリスト。
        time_matches (list): 時間のマッチリスト。
        content_dt (datetime): 基準となる日時。

    Returns:
        list: 日時オブジェクトのリスト。
    """
    datetimes = []
    open_hour, open_minute, start_hour, start_minute = map(int, time_matches[0])
    for month, day in date_matches:
        month, day = map(int, (month, day))
        open_datetime = datetime.datetime(content_dt.year, month, day, open_hour, open_minute)
        start_datetime = datetime.datetime(content_dt.year, month, day, start_hour, start_minute)
        open_datetime = adjust_datetime_if_past(open_datetime, content_dt)
        start_datetime = adjust_datetime_if_past(start_datetime, content_dt)
        datetimes.append(("開場", open_datetime))
        datetimes.append(("開演", start_datetime))
    return datetimes

def handle_multiple_time_matches(date_matches, time_matches, content_dt):
    """
    各日付が異なる時間を持つ場合の日時オブジェクトのリストを生成する。

    Args:
        date_matches (list): 日付のマッチリスト。
        time_matches (list): 時間のマッチリスト。
        content_dt (datetime): 基準となる日時。

    Returns:
        list: 日時オブジェクトのリスト。
    """
    datetimes = []
    for (month, day), (open_hour, open_minute, start_hour, start_minute) in zip(date_matches, time_matches):
        month, day, open_hour, open_minute, start_hour, start_minute = map(int, (month, day, open_hour, open_minute, start_hour, start_minute))
        open_datetime = datetime.datetime(content_dt.year, month, day, open_hour, open_minute)
        start_datetime = datetime.datetime(content_dt.year, month, day, start_hour, start_minute)
        open_datetime = adjust_datetime_if_past(open_datetime, content_dt)
        start_datetime = adjust_datetime_if_past(start_datetime, content_dt)
        datetimes.append(("開場", open_datetime))
        datetimes.append(("開演", start_datetime))
    return datetimes

def adjust_datetime_if_past(datetime_obj, content_dt):
    """
    過去の日時であれば1年を加算する。

    Args:
        datetime_obj (datetime): 検証する日時オブジェクト。
        content_dt (datetime): 基準となる日時。

    Returns:
        datetime: 調整後の日時オブジェクト。
    """
    if datetime_obj < content_dt:
        return datetime_obj + datetime.timedelta(years=1)
    return datetime_obj