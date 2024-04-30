from dependencies import re, mojimoji, datetime, requests, BeautifulSoup, time
from web_scraping import get_time_event_from_event_info


def remove_blank(text):
    """
    テキストから空白を削除し、全角文字を半角に変換します。
    """
    text = text.replace("\n", "")
    text = re.sub("^ +", "", text)
    text = re.sub(" +$", "", text)
    text = mojimoji.zen_to_han(text, kana=False)
    return text


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


def prepare_info_for_calendar(
    year, month, event_name_text, event_category_text, event_time_text, event_date_text
):
    """
    Googleカレンダーに登録する情報を整形します。
    """
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
