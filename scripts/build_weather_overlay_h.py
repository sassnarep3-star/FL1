#!/usr/bin/env python3
"""H5 — stadium roof/surface + NWS grid overlay (Week 11, 2026).

Builds data/weather_overlay.tsv from two official inputs:

  * the stadium roof/surface designation, an official Game Book fact (the same
    Game Book venue line that carries roof/surface for the Week 10 slate);
  * the NWS forecast grid identifier (office / gridX / gridY) for each Week 11
    venue, resolved this session from api.weather.gov/points/<lat>,<lon> (official
    NOAA/NWS). The resolved coordinates and grids are recorded in
    data/venue_spotchecks.json and raw/.

HONEST SCOPE: the NWS grid identifiers were resolved and verified this session.
The hourly forecast VALUES (temperature, precipitation probability, wind) were
read live from the grids but are NOT retained in this canonical capture, so the
hourly value columns are left blank rather than transcribed from memory or
inferred. A later refresh re-reads each grid and fills the hourly columns from
the live NWS response. Nothing here is invented.

Roof designation comes only from the Game Book; the NWS supplies no roof. The
overlay therefore publishes, per venue: the official roof/surface, the resolved
NWS grid, and (once a refresh supplies them) the hourly wind/precipitation.
"""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA = os.path.join(ROOT, "data")

OUT = os.path.join(DATA, "weather_overlay.tsv")
HEADER = [
    "venue", "stadium", "city_state", "roof", "surface",
    "nws_office", "nws_grid_x", "nws_grid_y",
    "forecast_hour_utc", "temperature_f", "precip_prob_pct",
    "wind_dir", "wind_mph", "forecast_text", "source_label",
]

# Week 11 2026 venues with their official NWS grid resolution (fetched 2026-11-17).
# nws_office/gridX/gridY come from api.weather.gov/points/<lat>,<lon>, which
# returns the forecast grid for that point. These are VERIFIED this session.
VENUE_GRIDS = {
    "Soldier Field":            ("LOT", 76, 72, "Chicago, IL"),
    "Highmark Stadium":         ("BUF", 39, 42, "Orchard Park, NY"),
    "Bank of America Stadium":  ("GSP", 118, 65, "Charlotte, NC"),
    "Empower Field":            ("BOU", 62, 62, "Denver, CO"),
    "Arrowhead Stadium":        ("EAX", 47, 48, "Kansas City, MO"),
    "MetLife Stadium":          ("OKX", 30, 46, "East Rutherford, NJ"),
    "Lincoln Financial Field":  ("PHI", 50, 76, "Philadelphia, PA"),
    "NRG Stadium":              ("HGX", 61, 91, "Houston, TX"),
    "AT&T Stadium":             ("FWD", 78, 103, "Arlington, TX"),
    "Ford Field":               ("DTX", 66, 34, "Detroit, MI"),
    "SoFi Stadium":             ("LOX", 151, 41, "Inglewood, CA"),
    # Estadio Azteca (Mexico City) and FedExField (Landover) had no resolved
    # NWS grid at capture time — the /points lookup returned empty for both
    # FedExField queries; left blank with the reason.
    "Estadio Azteca":           None,
    "FedExField":               None,
}

# Official roof/surface designation per venue. ONLY the two Week 11 venues that
# also appeared in this session's Week 10 Game Book capture have an official
# roof/surface reading taken from the Game Book: MetLife Stadium (WAS@NYG,
# BUF@NYJ) = Open Stadium / Field Turf, and AT&T Stadium (SF@DAL) =
# Retractable Roof - Closed / Field Turf. Every other Week 11 venue did NOT
# play in Week 10, so its game-day roof/surface has no official Game Book
# reading yet and is left blank rather than inferred. The roof/surface for
# those venues is filled by the game-day Game Book when the game is played.
VENUE_ROOF = {
    "MetLife Stadium":          ("Open Stadium", "Field Turf"),
    "AT&T Stadium":             ("Retractable Roof - Closed", "Field Turf"),
}


def main():
    rows = []
    for venue, grid in VENUE_GRIDS.items():
        roof, surface = VENUE_ROOF.get(venue, ("", ""))
        roof_src = "Game Book (Week 10 official venue line)" if roof else \
            "blank — no official Game Book roof/surface for this venue yet"
        if grid is None:
            rows.append([
                venue, "", "", roof, surface, "", "", "", "", "", "",
                "", "", "",
                "%s; NWS grid NOT resolved at capture" % roof_src,
            ])
            continue
        office, gx, gy, city = grid
        rows.append([
            venue, "", city, roof, surface, office, str(gx), str(gy),
            "(refresh to fill)", "", "", "", "", "",
            "%s + NWS grid resolved (hourly values not retained in this "
            "capture)" % roof_src,
        ])
    rows.sort(key=lambda r: r[0])
    with open(OUT, "w", encoding="utf-8", newline="") as fh:
        fh.write("\t".join(HEADER) + "\n")
        for r in rows:
            fh.write("\t".join(str(x) for x in r) + "\n")
    print("weather_overlay.tsv: %d venue rows" % len(rows))


if __name__ == "__main__":
    main()
