# Data sources

| Data           | Source                                                                   | License                                                    | Refresh                     |
| -------------- | ------------------------------------------------------------------------ | ---------------------------------------------------------- | --------------------------- |
| Airports + tz  | [airportsdata](https://github.com/mborsetti/airportsdata)                | MIT                                                        | Dependabot (Python package) |
| Airline names  | [OpenFlights](https://openflights.org/data) `airlines.dat`               | [ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/) | `make airlines`             |
| Distances      | [geographiclib](https://geographiclib.sourceforge.io/) (WGS84 geodesics) | MIT                                                        | Dependabot (Python package) |
| Timezone rules | [tzdata](https://pypi.org/project/tzdata/) (IANA)                        | Apache 2.0                                                 | Dependabot (Python package) |

## Airline names

`scripts/build_airlines.py` keeps active airlines with a two-character IATA code. OpenFlights lists
some codes for several airlines; those are dropped unless resolved in `OVERRIDES`, because a
missing name is better than a wrong one. OpenFlights is community-maintained and may lag behind
real-world changes; the `AirlineRepository` port allows swapping in a commercial source later.

Airline data © OpenFlights contributors, available under the Open Database License.
