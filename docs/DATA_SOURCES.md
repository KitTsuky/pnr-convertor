# Data sources

| Data           | Source                                                                                                        | License                                                    | Refresh                     |
| -------------- | ------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------- | --------------------------- |
| Airports + tz  | [airportsdata](https://github.com/mborsetti/airportsdata)                                                     | MIT                                                        | Dependabot (Python package) |
| Airline names  | [OpenFlights](https://openflights.org/data) `airlines.dat`                                                    | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | `make airlines`             |
| Distances      | [geographiclib](https://geographiclib.sourceforge.io/) (WGS84 geodesics)                                      | MIT                                                        | Dependabot (Python package) |
| Timezone rules | [tzdata](https://pypi.org/project/tzdata/) (IANA)                                                             | Apache 2.0                                                 | Dependabot (Python package) |
| Airline logos  | [Wikidata](https://www.wikidata.org/wiki/Property:P154) / [Wikimedia Commons](https://commons.wikimedia.org/) | Per file, in `data/airline_logos/manifest.json`            | Manual                      |

## Airline names

`scripts/build_airlines.py` keeps active airlines with a two-character IATA code. OpenFlights lists
some codes for several airlines; those are dropped unless resolved in `OVERRIDES`, because a
missing name is better than a wrong one. OpenFlights is community-maintained and may lag behind
real-world changes; the `AirlineRepository` port allows swapping in a commercial source later.

Airline data © OpenFlights contributors, available under the Open Database License.

## Airline logos

`data/airline_logos/` holds PNG logos (at most 128 px high) for 469 airlines, taken from the logo
(P154) of each airline's Wikidata item and rendered by Wikimedia Commons. Commons hosts only free
files: 417 are public domain (mostly text logos below the threshold of originality), the rest are
under CC0, CC BY, CC BY-SA, GFDL, FAL or MPL. `manifest.json` records, for every logo, the airline,
its Wikidata item, the Commons file page, the license and the author, which is the attribution
those licenses require.

Logos are trademarks of their airlines. They are shown only to identify the airline operating a
flight, never to suggest endorsement. Airlines without a logo here show their IATA code instead.
