#!/usr/bin/env python3
"""
fetch_prop_mirror_m.py — session M: restore the pinned prop-correlation input
mirror so session D's V9 check can run in a fresh workspace.

What and why
------------
scripts/build_prop_correlations_d.py (session D) rebuilds
data/prop-correlations-d.csv from an out-of-repo parquet mirror:

    /home/user/datawork/player_stats_weekly_archive.parquet

The parquet is deliberately not in Git (dataset kept external per the repo
convention). In a fresh sandbox the file is absent and V9 FAILS for
environmental reasons, not data reasons. This script fetches the EXACT pinned
blob from the allowlisted mirror github.com/Beexly/Sports by its git blob sha
(git is content-addressed: the sha IS the verification), writes it to the path
session D's script expects, and re-checks size + sha before declaring success.

Pinned:  repo   Beexly/Sports
         path   data/nflverse/player_stats_weekly_archive.parquet
         blob   adc42c07f2befa3e984a8c123d2861ba9bfb6f1f
         size   5621855
         (as recorded by data/verification-d.tsv V9 lineage; mirror note in
          data/sources.tsv S48: file commit 2026-11-07)

Run:  python3 scripts/fetch_prop_mirror_m.py
Then: python3 scripts/build_prop_correlations_d.py
      python3 scripts/verify_d.py
"""
import hashlib
import os
import subprocess
import sys

REPO = "Beexly/Sports"
PATH = "data/nflverse/player_stats_weekly_archive.parquet"
BLOB_SHA = "adc42c07f2befa3e984a8c123d2861ba9bfb6f1f"
SIZE = 5621855
DEST = "/home/user/datawork/player_stats_weekly_archive.parquet"


def git_blob_sha(data: bytes) -> str:
    header = b"blob %d\x00" % len(data)
    return hashlib.sha1(header + data).hexdigest()


def main() -> int:
    if os.path.exists(DEST):
        with open(DEST, "rb") as fh:
            data = fh.read()
        if len(data) == SIZE and git_blob_sha(data) == BLOB_SHA:
            print("already present and pinned: %s" % DEST)
            return 0
        print("existing file does not match the pin; refetching")

    os.makedirs(os.path.dirname(DEST), exist_ok=True)
    proc = subprocess.run(
        ["gh", "api", "repos/%s/git/blobs/%s" % (REPO, BLOB_SHA),
         "-H", "Accept: application/vnd.github.raw"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if proc.returncode != 0:
        print("FETCH FAILED:", proc.stderr.decode()[:400], file=sys.stderr)
        return 1
    data = proc.stdout
    if len(data) != SIZE:
        print("SIZE MISMATCH: got %d want %d" % (len(data), SIZE), file=sys.stderr)
        return 1
    sha = git_blob_sha(data)
    if sha != BLOB_SHA:
        print("SHA MISMATCH: got %s want %s" % (sha, BLOB_SHA), file=sys.stderr)
        return 1
    with open(DEST, "wb") as fh:
        fh.write(data)
    print("fetched and pinned OK: %s (%d bytes, blob %s)" % (DEST, SIZE, sha))
    return 0


if __name__ == "__main__":
    sys.exit(main())
