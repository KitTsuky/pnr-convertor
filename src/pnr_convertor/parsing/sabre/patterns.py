"""Sabre itinerary display (`*I`, `*IA`), e.g.:

1 AI 174J 14JUN J SFODEL SS2  1000A  345P  15JUN S /DCAI /E
2 AA7386D 13JUL S DFWMEL*SS2   825P  500A  15JUL T /DCAA /E
"""

import re

WEEKDAYS = {"M": 1, "T": 2, "W": 3, "Q": 4, "F": 5, "J": 6, "S": 7}

AIR_SEGMENT = re.compile(
    r"""
    ^\s*(?P<index>\d{1,3})\s+
    (?P<carrier>[A-Z0-9]{2})\s*(?P<flight>\d{1,4})(?P<booking_class>[A-Z])\s+
    (?P<departure_date>\d{2}[A-Z]{3})\s+
    (?P<weekday>[MTWQFJS])\s+
    (?P<origin>[A-Z]{3})(?P<destination>[A-Z]{3})\*?\s*
    (?P<status>[A-Z]{2})(?P<passenger_count>\d{1,2})\s+
    (?P<departure_time>\d{3,4}[APNM])\s+
    (?P<arrival_time>\d{3,4}[APNM])
    (?:\s+(?P<arrival_date>\d{2}[A-Z]{3})\s+(?P<arrival_weekday>[MTWQFJS]))?
    (?:\s.*)?$
    """,
    re.VERBOSE,
)
