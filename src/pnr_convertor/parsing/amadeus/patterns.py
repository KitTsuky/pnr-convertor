"""Amadeus PNR display (`RT` response), e.g.:

RP/BUHRO08AA/BUHRO08AA            AA/SU  10JAN26/0915Z   ZX7K2P
  1.POPESCU/ANDREI MR   2.POPESCU/MARIA MRS
  3  RO 391 Y 15MAR 7 OTPCDG HK2  0710 0920   15MAR  E  RO/ZX7K2P
  4  BA 284 H 10APR 4*LHRJFK HK2  1120A  215P 10APR  E  BA/9XZABC
"""

import re

HEADER = re.compile(r"^RP/\S+.*\s(?P<locator>[A-Z0-9]{6})$", re.MULTILINE)

AIR_SEGMENT = re.compile(
    r"""
    ^\s*(?P<index>\d{1,3})\s+
    (?P<carrier>[A-Z0-9]{2})\s*(?P<flight>\d{1,4})\s*
    (?P<booking_class>[A-Z])\s+
    (?P<departure_date>\d{2}[A-Z]{3})\s+
    (?:(?P<weekday>[1-7])\s*)?\*?
    (?P<origin>[A-Z]{3})(?P<destination>[A-Z]{3})\s+
    (?P<status>[A-Z]{2})(?P<passenger_count>\d{1,2})\s+
    (?P<departure_time>\d{4}|\d{3,4}[APNM])\s+
    (?P<arrival_time>\d{4}|\d{3,4}[APNM])(?P<day_offset>[+-]\d)?
    (?:\s+(?P<arrival_date>\d{2}[A-Z]{3}))?
    (?:\s.*)?$
    """,
    re.VERBOSE,
)

NAMES_LINE = re.compile(r"^\s*\d{1,3}\.[A-Z]")

NAME = re.compile(
    r"""
    (?P<index>\d{1,3})\.
    (?P<last_name>[A-Z][A-Z' -]*?)/
    (?P<first_name>[A-Z][A-Z' -]+?)
    (?:\s?(?P<title>MRS|MR|MS|MISS|MSTR)|\s(?P<spaced_title>DR))?
    (?=\s{2,}\d{1,3}\.|\s*$)
    """,
    re.VERBOSE,
)

TICKET = re.compile(
    r"""
    ^\s*\d{1,3}\s+FA\s+(?:PAX|INF)\s+
    (?P<number>\d{3}-\d{10}(?:-\d{2})?)
    (?:/(?P<electronic>ET)?(?P<airline>[A-Z0-9]{2}))?
    (?:/(?P<issue_date>\d{2}[A-Z]{3}\d{2}))?
    .*?(?:/P(?P<passenger>\d{1,3}))?\s*$
    """,
    re.VERBOSE,
)

SEAT_REQUEST = re.compile(
    r"^\s*\d{1,3}\s+SSR\s+(?:NSST|RQST|SEAT)\s+[A-Z0-9]{2}\s+[A-Z]{2}\d{1,2}\s+[A-Z]{6}/"
    r"(?P<seats>.*?)/S(?P<segment>\d{1,3})\b"
)

SEAT = re.compile(r"(?<![A-Z0-9])(?P<seat>\d{1,3}[A-Z])(?:,P(?P<passenger>\d{1,3}))?(?=/|$)")

CONTACT = re.compile(r"^\s*\d{1,3}\s+AP(?P<qualifier>[A-Z]?)\s+(?P<text>.+?)\s*$")
