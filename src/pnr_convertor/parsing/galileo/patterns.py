"""Travelport Galileo booking file display (`*R`, `*I`), e.g.:

BCF2ZS/AA HKGOU  TV8AA AG 13305213 10DEC
1.1SMITH/JOHNMR
 1 . KL  888 M  10MAY HKGAMS HK1  1220   1835  O*    E SU
 3 . SK  965 M  20MAY CPHHKG HK1  2100  #1345  O*    E WE/TH
FONE-LONT*0207 890 3472 TEST TRAVEL REF ANA
  2. LONH*0207 555 0100
TKTG-T*
"""

import re

# Record locator, agent sign, set, pseudo city, duty code `AG`, IATA number, creation date.
HEADER = re.compile(
    r"^\s*(?P<locator>[A-Z0-9]{6})/[A-Z0-9]{2}\s+\S+\s+\S+\s+AG\s+\d{7,8}\s+\d{1,2}[A-Z]{3}\s*$",
    re.MULTILINE,
)

WEEKDAYS = {"MO": 1, "TU": 2, "WE": 3, "TH": 4, "FR": 5, "SA": 6, "SU": 7}

# A marker before the arrival time gives the day difference.
ARRIVAL_DAY_MARKERS = {"#": 1, "*": 2, "-": -1}

AIR_SEGMENT = re.compile(
    r"""
    ^\s*(?P<index>\d{1,3})\s?\.\s*
    (?P<carrier>[A-Z0-9]{2})\s*(?P<flight>\d{1,4})\s*(?P<booking_class>[A-Z])\s+
    (?P<departure_date>\d{1,2}[A-Z]{3})\s+
    (?P<origin>[A-Z]{3})(?P<destination>[A-Z]{3})\s+
    (?P<status>[A-Z]{2})\s?(?P<passenger_count>\d{1,2})\s+
    (?P<departure_time>\d{4}|\d{3,4}[APNM])\s+
    (?P<arrival_marker>[#*-])?(?P<arrival_time>\d{4}|\d{3,4}[APNM])
    (?:\s*(?P<day_offset>[+-]\d)\b)?
    (?P<indicators>.*)$
    """,
    re.VERBOSE,
)

WEEKDAY_PAIR = re.compile(
    r"(?:^|\s)(?P<departure>MO|TU|WE|TH|FR|SA|SU)(?:/(?P<arrival>MO|TU|WE|TH|FR|SA|SU))?(?=\s|$)"
)

# `1.1SMITH/JOHNMR*ADT`, or an infant item `3.I/1BABY/LITTLEMISS*25DEC14`.
NAME_ITEM = re.compile(
    r"""
    (?:^|\s)(?P<index>\d{1,2})\.(?P<infant>I/)?\d{1,2}
    (?P<surname>[A-Z][A-Z' -]*?)/(?P<given>[A-Z][A-Z' ]*?)
    (?:\*(?P<suffix>\S+))?
    (?=\s+\d{1,2}\.(?:I/)?\d|\s*$)
    """,
    re.VERBOSE,
)

GIVEN_NAME = re.compile(
    r"^(?P<first_name>.+?)(?:\s?(?P<title>MRS|MR|MISS|MSTR|MS)|\s(?P<spaced_title>DR))?$"
)

PASSENGER_TYPE = re.compile(r"[A-Z]{3}")
CHILD_AGE = re.compile(r"C\d{2}")
DATE_OF_BIRTH = re.compile(r"\d{2}[A-Z]{3}\d{2}")

# Field lines such as `FONE-…`, `TKTG-…`, `FOP-…`; numbered continuation lines belong to them.
FIELD = re.compile(r"^\s*(?P<tag>[A-Z]{2,5})-(?P<rest>.*)$")
# A digit after the dot would make it a name item (`1.1DOE/JANE`).
NUMBERED_ITEM = re.compile(r"^\s*\d{1,2}\.\s*(?P<text>[^\d\s].*?)\s*$")
