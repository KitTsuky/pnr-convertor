"""Sabre PNR display (`*A`) and itinerary display (`*I`, `*IA`), e.g.:

1.2POPESCU/ANDREI MR/MARIA MRS  2.1IONESCU/ELENA MS
 1 RO 381Y 5DEC F*OTPAMS HK3 715A 905A/DCRO*QWE3RT
 2 AA7386D 13JUL S DFWMEL*SS2   825P  500A  15JUL T /DCAA /E
PHONES
  1.BUH021-555-0100-A
A1B2.A1B2*AKT 1532/14OCT25   KXLQPZ H
"""

import re

WEEKDAYS = {"M": 1, "T": 2, "W": 3, "Q": 4, "F": 5, "J": 6, "S": 7}

# `*` before the outbound and after the return city pair marks married segments.
AIR_SEGMENT = re.compile(
    r"""
    ^\s*(?P<index>\d{1,3})\s+
    (?P<carrier>[A-Z0-9]{2})\s*(?P<flight>\d{1,4})(?P<booking_class>[A-Z])\s*
    (?P<departure_date>\d{1,2}[A-Z]{3})\s+
    (?P<weekday>[MTWQFJS])\s*\*?
    (?P<origin>[A-Z]{3})(?P<destination>[A-Z]{3})\*?\s*
    (?P<status>[A-Z]{2})(?P<passenger_count>\d{1,2})\s+
    (?P<departure_time>\d{3,4}[APNM])\s+
    (?P<arrival_time>\d{3,4}[APNM])
    (?:\s+(?P<arrival_date>\d{1,2}[A-Z]{3})\s+(?P<arrival_weekday>[MTWQFJS]))?
    (?:[\s/].*)?$
    """,
    re.VERBOSE,
)

# One name item: a surname followed by one or more given names, e.g. `1.2JONES/ALAN/DORIS`.
NAME_ITEM = re.compile(
    r"(?:^|\s)\d{1,2}\.\d{1,2}(?P<surname>[A-Z][A-Z' -]*?)(?P<given_names>(?:/[A-Z][A-Z' ]*?)+)"
    r"(?=\s{2,}\d{1,2}\.\d|\s*$)"
)

GIVEN_NAME = re.compile(r"^(?P<first_name>.+?)(?:\s(?P<title>MRS|MR|MS|MISS|MSTR|DR))?$")

SECTION_HEADER = re.compile(
    r"^\s*(?P<section>PHONES|TKT/TIME LIMIT|GENERAL FACTS|REMARKS|ADDRESS|RECEIVED FROM|"
    r"CUSTOMER NUMBER|FREQUENT TRAVELER|AA FACTS|SECURITY INFO|PRICE QUOTE)\b"
)

# Phones start with a city code; `1.1DOE/JANE` (a digit after the dot) is a name item.
NUMBERED_ITEM = re.compile(r"^\s*\d{1,3}\.(?P<text>[^\d\s].*?)\s*$")

# The signature line closes a stored PNR: pseudo city, agent, time/date, then the locator.
SIGNATURE = re.compile(
    r"^\s*[A-Z0-9]{3,4}\.[A-Z0-9]{3,4}\*[A-Z0-9]{3}\s+\d{4}/\d{2}[A-Z]{3}\d{2}\s+"
    r"(?P<locator>[A-Z]{6})\b",
    re.MULTILINE,
)
