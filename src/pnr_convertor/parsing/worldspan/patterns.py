"""Travelport Worldspan PNR display (`*R`), e.g.:

1P- 4I5RJD
 1.1MONDESIR/PMS*ADT
 1 UA 957Q 01NOV MO LHRJFK HK1  0900  1210 /O $ E
 2 UA 956Q 11NOV TH JFKLHR HK1  1855  0655 #1/O $ E
P- 1.IKM 0181 745-1900 T/WORLDSPAN TRAVEL / REF PAULINE
T- 1.T/28JUL1000 1P/IKM/PM*E0161504119448 I996683
"""

import re

HEADER = re.compile(r"^\s*1P-\s*(?P<locator>[A-Z0-9]{6})\b", re.MULTILINE)

WEEKDAYS = {"MO": 1, "TU": 2, "WE": 3, "TH": 4, "FR": 5, "SA": 6, "SU": 7}

# `#1` after the arrival time is the arrival day offset; `/O` or `/X` and `$ E` follow.
AIR_SEGMENT = re.compile(
    r"""
    ^\s*(?P<index>\d{1,3})\.?\s+
    (?P<carrier>[A-Z0-9]{2})\s*(?P<flight>\d{1,4})(?P<booking_class>[A-Z])\s+
    (?P<departure_date>\d{1,2}[A-Z]{3})\s+
    (?P<weekday>MO|TU|WE|TH|FR|SA|SU)\s+
    (?P<origin>[A-Z]{3})(?P<destination>[A-Z]{3})\s+
    (?P<status>[A-Z]{2})(?P<passenger_count>\d{1,2})\s+
    (?P<departure_time>\d{4}|\d{3,4}[APNM])\s+
    (?P<arrival_time>\d{4}|\d{3,4}[APNM])
    (?:\s*(?P<day_offset>[#-]\d))?
    (?:[\s/].*)?$
    """,
    re.VERBOSE,
)

# `1.1DAY/JOHN.MR*ADT`, `2.1DOE/ANA@*CNN`; `@` precedes the type of a name without a title.
NAME_ITEM = re.compile(
    r"""
    (?:^|\s)(?P<index>\d{1,2})\.\d{1,2}
    (?P<surname>[A-Z][A-Z' -]*?)/(?P<given>[A-Z][A-Z' .]*?)@?
    (?:\*(?P<type_code>[A-Z0-9]{3}))?
    (?=\s+\d{1,2}\.\d|\s*$)
    """,
    re.VERBOSE,
)

GIVEN_NAME = re.compile(
    r"^(?P<first_name>.+?)(?:\.?(?P<title>MRS|MR|MISS|MSTR|MS)|\.(?P<dotted_title>DR))?$"
)

# Field lines such as `P- 1.…`, `T- 1.…`, `FQ- …`; numbered continuation lines belong to them.
FIELD = re.compile(r"^(?P<tag>[A-Z]{1,4})-\s*(?P<rest>.*)$")
NUMBERED_ITEM = re.compile(r"^\s*\d{1,2}\.(?P<text>\S.*?)\s*$")

TICKET = re.compile(r"\*(?P<electronic>E)?(?P<number>\d{13})\b")
