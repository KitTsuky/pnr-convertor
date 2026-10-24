"""Build `src/pnr_convertor/data/airlines.json` from the OpenFlights `airlines.dat` dataset.

Usage: uv run python scripts/build_airlines.py <airlines.dat> <output.json>
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger("build_airlines")

IATA_CODE = re.compile(r"[A-Z0-9]{2}")

# Codes listed for several active airlines in OpenFlights, resolved to the current holder.
# Ambiguous codes not listed here are dropped: no name is better than a wrong one.
OVERRIDES = {
    "8M": "Myanmar Airways International",
    "G3": "Gol Transportes Aéreos",
    "JL": "Japan Airlines",
    "LH": "Lufthansa",
    "RA": "Nepal Airlines",
    "SQ": "Singapore Airlines",
    "VY": "Vueling Airlines",
    "WA": "KLM Cityhopper",
}


def build(rows: list[list[str]]) -> dict[str, str]:
    candidates: defaultdict[str, set[str]] = defaultdict(set)
    for row in rows:
        if len(row) != 8:
            continue
        _, name, _, iata, _, _, _, active = row
        if active == "Y" and IATA_CODE.fullmatch(iata):
            candidates[iata].add(name.strip())

    airlines = {code: names.pop() for code, names in candidates.items() if len(names) == 1}
    ambiguous = sorted(code for code, names in candidates.items() if len(names) > 1)
    airlines.update(OVERRIDES)
    dropped = [code for code in ambiguous if code not in OVERRIDES]
    logger.info("airlines=%d dropped_ambiguous=%s", len(airlines), dropped)
    return dict(sorted(airlines.items()))


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    with args.source.open(encoding="utf-8", newline="") as source:
        airlines = build(list(csv.reader(source)))
    args.output.write_text(
        json.dumps(airlines, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
