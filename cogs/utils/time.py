"""
Custom datetime functions.

:copyright: (c) 2022 Isaglish
:license: MIT, see LICENSE for more details.
"""

import datetime
import time
import re


def unix_timestamp(datetime: datetime.datetime) -> int:
    return int(time.mktime(datetime.timetuple()))


def str_to_timedelta(string: str) -> datetime.timedelta | None:
    string = re.sub(r'\s', r'', string)

    parts = re.match(
        r"""
        (?:(?P<days>\d+?)\s*(days?|d))?
        (?:(?P<hours>\d+?)\s*(hours?|hrs?|h))?
        (?:(?P<minutes>\d+?)\s*(minutes?|mins?|m))?
        (?:(?P<seconds>\d+?)\s*(seconds?|secs?|s))?
        """,
        string,
        flags=re.VERBOSE | re.IGNORECASE
    )

    if not parts:
        return None

    parts = parts.groupdict()
    parameters = {}
    for time, amount in parts.items():
        if amount:
            parameters[time] = int(amount)

    if not parameters:
        return None

    return datetime.timedelta(**parameters)