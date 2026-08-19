# Copyright (c) 2020 ddn
# Copyright (c) 2026 CircleTenThanks
# 一部は https://qiita.com/ddn/items/42def5fa721e531eecdb を基に改変している.
"""日向坂46のスケジュールをGoogleカレンダーへ反映する."""

import datetime
import logging
import os

from dateutil.relativedelta import relativedelta

from .google_calendar import (
    ScrapedEvent,
    add_event_to_google_calendar,
    build_google_calendar_api,
    get_schedule_from_google_calendar,
    remove_event_from_google_calendar,
)
from .hinatazaka_scraper import get_events_from_hnz_hp, get_month_schedule_from_hnz_hp

_JST = datetime.timezone(datetime.timedelta(hours=9))
_SEARCH_MONTHS = 3


def main() -> None:
    """指定月数分の公式HPスケジュールをカレンダーへ反映する."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    service = build_google_calendar_api()
    calendar_id = os.environ["CALENDAR_ID_HNZ"]
    current_search_date = datetime.datetime.now(tz=_JST)

    for _ in range(_SEARCH_MONTHS):
        year = current_search_date.year
        month = current_search_date.month
        previous_add_event_lists = get_schedule_from_google_calendar(
            service,
            calendar_id,
            year,
            month,
        )

        events_each_date = get_month_schedule_from_hnz_hp(str(year), f"{month:02d}")
        if events_each_date is None:
            current_search_date += relativedelta(months=1)
            continue

        for event_each_date in events_each_date:
            event_date_text, events_time, events_name, events_category, events_link = (
                get_events_from_hnz_hp(event_each_date)
            )
            event_date_text = f"{int(event_date_text):02d}"

            for event_name, event_category, event_time, event_link in zip(
                events_name,
                events_category,
                events_time,
                events_link,
                strict=True,
            ):
                add_event_to_google_calendar(
                    service,
                    calendar_id,
                    ScrapedEvent(
                        year=year,
                        month=month,
                        date_text=event_date_text,
                        name=event_name,
                        category=event_category,
                        time=event_time,
                        link=event_link,
                    ),
                    previous_add_event_lists,
                )

        remove_event_from_google_calendar(
            service,
            calendar_id,
            previous_add_event_lists,
        )
        current_search_date += relativedelta(months=1)


if __name__ == "__main__":
    main()
