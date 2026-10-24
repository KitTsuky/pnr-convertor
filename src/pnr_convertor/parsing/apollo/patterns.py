"""Travelport Apollo PNR display (`*R`), e.g.:

K4WQ7D/WS QSBYC DPBVWS AG 05578602 19NOV
 1.1POPESCU/ANDREI MR
 1 UA9993S 12FEB NBOBRU HK1  1140P  645A+*      TH/FR   E  1
 2 UA 995S 13FEB BRUEWR HK1  1115A  130P *         FR   E  1
FONE-SFOAS/800-555-0100 TEST TRAVEL
TKTG-T/QSB 20NOV0014Z WS AG **ELECTRONIC DATA EXISTS**
"""

import re

# Same layout as the Galileo booking file header; the segment lines tell the two apart.
HEADER = re.compile(
    r"^\s*(?P<locator>[A-Z0-9]{6})/[A-Z0-9]{2}\s+\S+\s+\S+\s+AG\s+\d{7,8}\s+\d{1,2}[A-Z]{3}\s*$",
    re.MULTILINE,
)

WEEKDAYS = {"MO": 1, "TU": 2, "WE": 3, "TH": 4, "FR": 5, "SA": 6, "SU": 7}

# No dot after the segment number, 12-hour times, `+` after the arrival time for the next day.
AIR_SEGMENT = re.compile(
    r"""
    ^\s*(?P<index>\d{1,3})\s+
    (?P<carrier>[A-Z0-9]{2})\s*(?P<flight>\d{1,4})(?P<booking_class>[A-Z])\s+
    (?P<departure_date>\d{1,2}[A-Z]{3})\s+
    (?P<origin>[A-Z]{3})(?P<destination>[A-Z]{3})\s+
    (?P<status>[A-Z]{2})(?P<passenger_count>\d{1,2})\s+
    (?P<departure_time>\d{3,4}[APNM])\s+
    (?P<arrival_time>\d{3,4}[APNM])(?P<day_offset>[+-]\d?)?
    (?P<indicators>(?:[\s*].*)?)$
    """,
    re.VERBOSE,
)

WEEKDAY_PAIR = re.compile(
    r"(?:^|\s)(?P<departure>MO|TU|WE|TH|FR|SA|SU)(?:/(?P<arrival>MO|TU|WE|TH|FR|SA|SU))?(?=\s|$)"
)

# `1.1SMITH/A MR`, `2.1JONES/S MS*C10`, infant `3.I/1SMITH/CHARLES MSTR*12MAR25`.
NAME_ITEM = re.compile(
    r"""
    (?:^|\s)(?P<index>\d{1,2})\.(?P<infant>I/)?\d{1,2}
    (?P<surname>[A-Z][A-Z' -]*?)/(?P<given>[A-Z][A-Z' ]*?)
    (?:\*(?P<suffix>\S+))?
    (?=\s+\d{1,2}\.(?:I/)?\d|\s*$)
    """,
    re.VERBOSE,
)

GIVEN_NAME = re.compile(r"^(?P<first_name>.+?)(?:\s(?P<title>MRS|MR|MS|MISS|MSTR|DR))?$")

PASSENGER_TYPE = re.compile(r"[A-Z]{3}")
CHILD_AGE = re.compile(r"C\d{2}")
DATE_OF_BIRTH = re.compile(r"\d{2}[A-Z]{3}\d{2}")

# Field lines such as `FONE-…`, `TKTG-…`, `ATFQ-…`; numbered continuation lines belong to them.
FIELD = re.compile(r"^\s*(?P<tag>[A-Z]{2,5})-(?P<rest>.*)$")
# A digit after the dot would make it a name item (`1.1DOE/JANE`).
NUMBERED_ITEM = re.compile(r"^\s*\d{1,2}\.?\s+(?P<text>[^\d\s].*?)\s*$")
