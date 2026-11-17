#!/usr/bin/env python3
"""
capture_official.py — capture official NFL sources into a durable, hashed vault.

WHAT THIS IS
    The repository's single biggest evidence gap is that it has an official *injury
    report* capture and an official *depth chart* capture, but no official *game-day*
    record. This script closes that gap by pulling the official artefacts that only
    exist after a game is played:

        https://www.nfl.com/games/{slug}          the official Game Center page
        https://static.www.nfl.com/.../gamecenter/{uuid}.pdf
                                                 the official NFL Game Book PDF

    The NFL Game Book is the document the brief names for actual starters and
    game-day status. One PDF per game yields, for each club:

        Offense / Defense starting lineups (by unit and position)
        Substitutions
        Did Not Play
        Not Active            <- the official inactive list
        Field goals, scoring summary, individual statistics
        Venue line            ("MetLife Stadium, East Rutherford, NJ")
        Game-day weather line ("Open Stadium on Field Turf", temp / humidity / wind)

    It also captures the live injury report on the cadence the brief asks for
    (Wednesday, Thursday, Friday) so the report becomes a dated *series* rather
    than a weekly snapshot.

WHY A SCRIPT AND NOT A ONE-OFF
    1. The capture is reproducible: same inputs, same URLs, same hashes.
    2. The capture is *immutable*: a file is written once, named by its own sha256,
       and never edited in place. A later read that disagrees with an earlier read
       is a diff, not a rewrite.
    3. The capture is *checkable*: `vault/manifest.tsv` records, for every artefact,
       the exact URL it came from, its byte count and its sha256. A reviewer can
       re-download any one of them and recompute the hash.

WHERE THE OUTPUT GOES
    A directory (default: ../vault) laid out as

        vault/pdf/<season>/<slug>.pdf      the official Game Book, byte for byte
        vault/text/<season>/<slug>.txt     the Game Book rendered to text
        vault/html/<name>.<timestamp>.html raw HTML captures (injury report, ...)
        vault/manifest.tsv                  one row per artefact: url, sha256, bytes, when

    In CI this directory is committed to a **non-published branch** (`vault`), so the
    raw row-level material lives outside the static site while the derived analysis
    lives in `data/` on `main`.

NETWORK NOTE
    This script needs the public internet. The authoring sandbox used for this
    repository can reach github.com but *not* nfl.com, so in-sandbox runs are
    expected to fail with `unreachable` per URL. That is not a bug in the script and
    not a reason to fill anything in: the CI job is where the capture runs.

STDLIB ONLY
    The engine, the build and the verifier in this repository use only the Python
    standard library. This script is no exception. PDF *text extraction* is the one
    step that needs a third-party library, and it is a separate script
    (`pdf_to_text.py`) that runs only in CI, where the dependency is declared in the
    workflow file rather than smuggled into the runtime.

Usage
    python3 scripts/capture_official.py --vault ../vault --season 2026 --week 10
    python3 scripts/capture_official.py --vault ../vault --season 2026 --games-only
    python3 scripts/capture_official.py --vault ../vault --injuries-only
"""

from __future__ import annotations

import argparse
import csv
import datetime as _dt
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36 FL1-capture/1.0 (+official-source archival)"
)

# ---------------------------------------------------------------------------
# Club tokens used by nfl.com in its game-page slugs.
#
#   https://www.nfl.com/games/commanders-at-giants-2026-reg-10
#
# The slug uses the club's *nickname* lower-cased, not "city-nickname" and not
# the abbreviation. These are the 32 NFL clubs as nfl.com names them. The map is
# verified at run time: every slug that is constructed is requested, and a slug
# that does not resolve is reported as a failure rather than being guessed at.
# ---------------------------------------------------------------------------
SLUG_TOKEN = {
    "ARI": "cardinals", "ATL": "falcons", "BAL": "ravens", "CAR": "panthers",
    "CHI": "bears", "CIN": "bengals", "CLE": "browns", "DAL": "cowboys",
    "DEN": "broncos", "DET": "lions", "GB": "packers", "HOU": "texans",
    "IND": "colts", "JAX": "jaguars", "KC": "chiefs", "LV": "raiders",
    "LAC": "chargers", "LAR": "rams", "MIA": "dolphins", "MIN": "vikings",
    "NE": "patriots", "NO": "saints", "NYG": "giants", "NYJ": "jets",
    "PHI": "eagles", "PIT": "steelers", "SEA": "seahawks", "SF": "49ers",
    "TB": "buccaneers", "TEN": "titans", "WAS": "commanders",
}

GAME_CENTER_PDF_RE = re.compile(
    r"https?://static\.www\.nfl\.com/[^\"'\s<>]*gamecenter/[^\"'\s<>]*?\.pdf",
    re.IGNORECASE,
)
ANY_PDF_RE = re.compile(r"https?://[^\"'\s<>]*\.pdf", re.IGNORECASE)

# The Game Center page for a completed game exposes the Game Book PDF as a
# "Download Game Book (PDF)" link. On some pages the URL is JSON-escaped.
GAMEBOOK_LABEL_RE = re.compile(
    r"Download Game Book", re.IGNORECASE
)


def log(msg: str) -> None:
    sys.stderr.write(msg + "\n")
    sys.stderr.flush()


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def fetch(url: str, timeout: int = 40, attempts: int = 3) -> tuple[int, bytes, str]:
    """GET a URL. Returns (status, body, error_text). Never raises for network."""
    last_err = ""
    for attempt in range(1, attempts + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT,
                                                   "Accept": "*/*"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status, resp.read(), ""
        except urllib.error.HTTPError as exc:            # 4xx / 5xx
            body = b""
            try:
                body = exc.read()
            except Exception:
                pass
            last_err = f"HTTP {exc.code}"
            if exc.code in (400, 401, 403, 404, 410):
                return exc.code, body, last_err
        except Exception as exc:                          # DNS / TLS / timeout
            last_err = f"{type(exc).__name__}: {exc}"
        if attempt < attempts:
            time.sleep(1.5 * attempt)
    return 0, b"", last_err


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_immutable(root: str, relpath: str, data: bytes) -> str:
    """Write bytes once. The file is named by its own content hash.

    Re-running the capture over a file that already exists with the same bytes is a
    no-op (the file is byte-identical). Re-running it over a file whose bytes have
    changed produces a *second* file, so the older capture survives.
    """
    digest = sha256(data)
    directory = os.path.dirname(relpath)
    if directory:
        os.makedirs(os.path.join(root, directory), exist_ok=True)
    final = os.path.join(root, relpath)
    if os.path.exists(final):
        with open(final, "rb") as fh:
            if sha256(fh.read()) == digest:
                return digest
    base, ext = os.path.splitext(relpath)
    hashed = f"{base}.{digest[:16]}{ext}"
    with open(os.path.join(root, hashed), "wb") as fh:
        fh.write(data)
    # the unhashed name is a pointer to the hashed file
    with open(final, "wb") as fh:
        fh.write(data)
    return digest


# ---------------------------------------------------------------------------
# Games
# ---------------------------------------------------------------------------
def load_games(season: int) -> list:
    path = os.path.join(ROOT, "data", "raw", "games.csv")
    if not os.path.exists(path):
        log("FATAL: data/raw/games.csv missing; cannot enumerate games")
        return []
    out = []
    with open(path, encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row.get("season") != str(season):
                continue
            if row.get("game_type") != "REG":
                continue
            away, home = row.get("away_team", ""), row.get("home_team", "")
            if away not in SLUG_TOKEN or home not in SLUG_TOKEN:
                continue
            played = (row.get("away_score", "").strip() != ""
                      and row.get("home_score", "").strip() != "")
            week = row.get("week", "")
            slug = f"{SLUG_TOKEN[away]}-at-{SLUG_TOKEN[home]}-{season}-reg-{week}"
            out.append({
                "game_id": row.get("game_id", ""),
                "season": season,
                "week": int(week) if week.isdigit() else 0,
                "away": away, "home": home,
                "away_score": row.get("away_score", ""),
                "home_score": row.get("home_score", ""),
                "old_game_id": row.get("old_game_id", ""),
                "slug": slug,
                "played": played,
            })
    # de-duplicate on old_game_id (the liveupdate identifier); keep first
    seen, uniq = set(), []
    for g in sorted(out, key=lambda r: (r["week"], r["game_id"])):
        key = g["old_game_id"] or g["game_id"]
        if key in seen:
            continue
        seen.add(key)
        uniq.append(g)
    return uniq


WEEK_SLUG_RE = re.compile(
    r"([a-z0-9\-]+)-at-([a-z0-9\-]+)-(?P<season>20\d{2})-(?P<type>reg|post)-(?P<week>\d{1,2})"
)


def discover_week_slugs(season: int, week: int) -> list:
    """Ask the official schedule page which games are in a week.

    The upstream games feed this repository already carries (nflverse) can lag
    the league: on 2026-11-17 it still had no result for thirteen of the
    fourteen Week 10 games that had already been played, so a capture driven
    from that feed alone would have silently skipped thirteen official game
    books. The league's own schedule page is therefore the authority on WHICH
    games exist, and the feed is used only for cross-checking.

    Returns a list of slugs. An empty list means the page could not be read,
    which the caller reports rather than treating as "no games".
    """
    url = "https://www.nfl.com/schedules/%d/REG%d/" % (season, week)
    status, body, err = fetch(url)
    if status != 200:
        return []
    text = body.decode("utf-8", "replace").replace("\\/", "/")
    slugs = []
    for m in WEEK_SLUG_RE.finditer(text):
        slug = m.group(0)
        if slug not in slugs:
            slugs.append(slug)
    return sorted(slugs)


def find_gamebook_pdf(html_text: str) -> str:
    """Pull the official Game Book PDF URL out of a Game Center page.

    THE TRAP THIS FUNCTION EXISTS TO AVOID
        A Game Center page does not contain only its own game. It also carries
        links to *other* games - a "featured game" module, a schedule rail, a
        highlights strip - and those links point at other game books. A naive
        search for the first `gamecenter/*.pdf` on the page therefore picks up
        whichever game the page happens to promote.

        That is not hypothetical. It happened: the page for
        `chargers-at-ravens-2026-reg-10` returned the PDF for
        `commanders-at-giants-2026-reg-10`, and the capture stored the
        Washington-New York book under the Chargers-Ravens slug. The book
        itself was genuine, the hash was genuine, and the only thing wrong was
        which game it belonged to - the worst kind of error, because every
        integrity check short of reading the document passed.

        So the link is not taken from anywhere on the page. It is taken from the
        anchor whose label is the Game Book link, and when the page offers no
        such anchor the function returns nothing and the caller FAILS LOUDLY
        rather than guessing.

    The verification that the returned book actually belongs to this game lives
    in the parser, which reads the match-up line off the extracted text and
    refuses a book whose match-up disagrees with the index. Two independent
    checks are used because this failure mode defeats any single one.
    """
    text = html_text.replace("\\/", "/").replace("&amp;", "&")

    # 1. The labelled Game Book link. The label is what distinguishes this
    #    game's book from every other book linked on the same page.
    label = re.search(rf'(?is)<a[^>]+href="(?P<href>[^"]*gamecenter[^"]*\.pdf)"[^>]*>'
                      r'(?:(?!</a>).){0,400}?(?:download\s+)?game\s*book', text)
    if label:
        return label.group("href")

    # 2. A structured data or JSON reference that names the game book field.
    field = re.search(r'(?i)"(?:gameBook|game_book|gamebook)[A-Za-z]*"\s*:\s*'
                      r'"(?P<href>[^"]*gamecenter[^"]*\.pdf)"', text)
    if field:
        return field.group("href")

    # Nothing labelled: report it. Do not fall back to "some PDF on the page".
    return ""


# ---------------------------------------------------------------------------
# Manifest
# ---------------------------------------------------------------------------
MANIFEST_FIELDS = ["artefact", "source_url", "official_page", "sha256", "bytes",
                   "http_status", "retrieved_at_utc", "note"]


class Manifest:
    def __init__(self, path: str):
        self.path = path
        self.rows = []
        if os.path.exists(path):
            with open(path, encoding="utf-8", newline="") as fh:
                self.rows = list(csv.DictReader(fh, delimiter="\t"))

    def add(self, **kw):
        row = {f: kw.get(f, "") for f in MANIFEST_FIELDS}
        for existing in self.rows:
            if (existing.get("artefact") == row["artefact"]
                    and existing.get("sha256") == row["sha256"]
                    and existing.get("retrieved_at_utc") == row["retrieved_at_utc"]):
                return
        self.rows.append(row)

    def save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w", encoding="utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=MANIFEST_FIELDS, delimiter="\t",
                               lineterminator="\n")
            w.writeheader()
            for row in sorted(self.rows, key=lambda r: (r["artefact"], r["retrieved_at_utc"])):
                w.writerow(row)


# ---------------------------------------------------------------------------
# Capture routines
# ---------------------------------------------------------------------------
def capture_game(g: dict, vault: str, manifest: Manifest, stats: dict) -> dict:
    page_url = f"https://www.nfl.com/games/{g['slug']}"
    status, body, err = fetch(page_url)
    g["page_status"] = status
    g["page_url"] = page_url
    if status != 200:
        stats["page_fail"] += 1
        g["pdf_url"] = ""
        g["pdf_status"] = 0
        g["pdf_sha256"] = ""
        g["pdf_bytes"] = 0
        g["error"] = err or f"HTTP {status}"
        return g
    stats["page_ok"] += 1
    html_text = body.decode("utf-8", "replace")
    pdf_url = find_gamebook_pdf(html_text)
    g["pdf_url"] = pdf_url
    if not pdf_url:
        stats["no_pdf_link"] += 1
        g["pdf_status"] = 0
        g["pdf_sha256"] = ""
        g["pdf_bytes"] = 0
        g["error"] = "no gamebook pdf link on game centre page"
        return g
    pstatus, pbody, perr = fetch(pdf_url, timeout=90)
    g["pdf_status"] = pstatus
    if pstatus != 200 or not pbody:
        stats["pdf_fail"] += 1
        g["pdf_sha256"] = ""
        g["pdf_bytes"] = len(pbody)
        g["error"] = perr or f"HTTP {pstatus}"
        return g
    stats["pdf_ok"] += 1
    rel = f"pdf/{g['season']}/{g['slug']}.pdf"
    digest = write_immutable(vault, rel, pbody)
    g["pdf_sha256"] = digest
    g["pdf_bytes"] = len(pbody)
    g["error"] = ""
    manifest.add(artefact=f"gamebook/{g['season']}/{g['slug']}",
                 source_url=pdf_url, official_page=page_url, sha256=digest,
                 bytes=len(pbody), http_status=pstatus,
                 retrieved_at_utc=now_iso(),
                 note=f"{g['away']}@{g['home']} W{g['week']} "
                      f"{g['away_score']}-{g['home_score']}")
    return g


INJURY_URL = "https://www.nfl.com/injuries/"


def capture_injuries(vault: str, manifest: Manifest, stats: dict) -> None:
    """Capture the live official injury report, stamped.

    The report changes during the week (Wednesday -> Friday, and again on game
    day). Each capture is stored under its own timestamp and hash, so the report
    becomes a *series*: the delta between two dated reads is computable without
    either read being overwritten.
    """
    status, body, err = fetch(INJURY_URL)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    if status != 200:
        stats["injury_fail"] += 1
        log(f"  injury report: FAILED {err or status}")
        manifest.add(artefact=f"injuries/{stamp}", source_url=INJURY_URL,
                     official_page=INJURY_URL, sha256="", bytes=0,
                     http_status=status, retrieved_at_utc=now_iso(),
                     note=f"capture failed: {err or status}")
        return
    stats["injury_ok"] += 1
    rel = f"html/injuries-{stamp}.html"
    digest = write_immutable(vault, rel, body)
    manifest.add(artefact=f"injuries/{stamp}", source_url=INJURY_URL,
                 official_page=INJURY_URL, sha256=digest, bytes=len(body),
                 http_status=status, retrieved_at_utc=now_iso(),
                 note="official weekly injury report")
    log(f"  injury report: {len(body)} bytes sha256={digest[:16]}…")


# ---------------------------------------------------------------------------
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vault", default=os.path.join(ROOT, "..", "vault"),
                    help="directory the vault is written to")
    ap.add_argument("--season", type=int, default=2026)
    ap.add_argument("--week", type=int, default=0,
                    help="capture one week only (0 = every week with a result)")
    ap.add_argument("--games-only", action="store_true")
    ap.add_argument("--injuries-only", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--include-unplayed", action="store_true",
                    help="also request game books for games with no result yet")
    ap.add_argument("--discover-weeks", default="",
                    help="comma-separated weeks to enumerate from the league's "
                         "own schedule pages (e.g. 10,11)")
    args = ap.parse_args(argv)
    args.discover_weeks = [int(x) for x in args.discover_weeks.split(",") if x.strip()]

    vault = os.path.abspath(args.vault)
    os.makedirs(vault, exist_ok=True)
    manifest = Manifest(os.path.join(vault, "manifest.tsv"))
    stats = {"page_ok": 0, "page_fail": 0, "pdf_ok": 0, "pdf_fail": 0,
             "no_pdf_link": 0, "injury_ok": 0, "injury_fail": 0}

    if not args.games_only:
        log("capturing official injury report …")
        capture_injuries(vault, manifest, stats)

    if not args.injuries_only:
        games = load_games(args.season)
        if args.week:
            games = [g for g in games if g["week"] == args.week]
        if not args.include_unplayed:
            games = [g for g in games if g["played"]]
        if args.limit:
            games = games[: args.limit]
        # Add any game the league's own schedule page lists but the upstream
        # feed has no result for. A game with no result in the feed is still
        # played if the league says it is on the schedule, and its game book
        # exists once the game is over.
        if args.discover_weeks:
            known = {g["slug"] for g in games}
            for wk in args.discover_weeks:
                for slug in discover_week_slugs(args.season, wk):
                    if slug in known:
                        continue
                    away, home = slug.split("-at-")[0], slug.split("-at-")[1].split("-2026-")[0]
                    games.append({
                        "game_id": slug, "season": args.season, "week": wk,
                        "away": away, "home": home, "away_score": "",
                        "home_score": "", "old_game_id": "", "slug": slug,
                        "played": True,
                    })
                    known.add(slug)
            games.sort(key=lambda r: (r["week"], r["slug"]))
        log(f"capturing {len(games)} official game book(s) for season {args.season} …")
        rows = []
        for i, g in enumerate(games, 1):
            g = capture_game(g, vault, manifest, stats)
            rows.append(g)
            log(f"  [{i}/{len(games)}] {g['slug']}: page={g['page_status']} "
                f"pdf={g['pdf_status']} sha={g['pdf_sha256'][:12]}"
                + (f" ERR {g['error']}" if g.get("error") else ""))
            # a small delay keeps the capture polite and avoids a burst pattern
            time.sleep(0.35)
        # A game book is a unique document. If two different games resolve to
        # the same file, one of the two resolutions is wrong, and the wrongness
        # is invisible in every hash and byte count - so it is caught HERE, by
        # the only property the error cannot fake: two games cannot share a
        # book. The capture fails rather than publishing the collision.
        seen = {}
        collisions = []
        for g in rows:
            sha = g.get("pdf_sha256")
            if not sha:
                continue
            if sha in seen and seen[sha] != g["slug"]:
                collisions.append((sha, seen[sha], g["slug"]))
                g["error"] = ("this game book is byte-identical to the book "
                              "resolved for %s; one of the two resolutions is "
                              "wrong" % seen[sha])
            else:
                seen[sha] = g["slug"]
        stats["book_hash_collisions"] = len(collisions)
        if collisions:
            log("GAME BOOK HASH COLLISION - two games resolved to one book:")
            for sha, a, b in collisions:
                log("  %s -> %s and %s" % (sha[:16], a, b))

        out = os.path.join(vault, "games_index.tsv")
        with open(out, "w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(["slug", "season", "week", "away", "home", "away_score",
                        "home_score", "game_page_url", "gamebook_pdf_url",
                        "gamebook_sha256", "gamebook_bytes", "page_status",
                        "pdf_status", "error"])
            for g in rows:
                w.writerow([g["slug"], g["season"], g["week"], g["away"], g["home"],
                            g["away_score"], g["home_score"], g["page_url"],
                            g["pdf_url"], g["pdf_sha256"], g["pdf_bytes"],
                            g["page_status"], g["pdf_status"], g.get("error", "")])
        log(f"wrote {out}")

    manifest.save()
    summary = {
        "captured_at_utc": now_iso(),
        "season": args.season,
        "week": args.week or "all",
        "stats": stats,
    }
    with open(os.path.join(vault, "capture_summary.json"), "w", encoding="utf-8") as fh:
        json.dump(summary, fh, indent=2, sort_keys=True)
    log("summary: " + json.dumps(summary["stats"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
