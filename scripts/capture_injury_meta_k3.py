#!/usr/bin/env python3
"""K3 (R73/R74 partial): capture injury-hub metadata, not content.

Fetches the official NFL injury hub, records UTC time, HTTP status, byte count and
SHA-256 of the response body, and appends one row to data/captures/injury_capture_log.tsv.
The response body is hashed in memory and discarded. Raw page content is never written
into the repository.

Fails loudly (non-zero exit) if the page is unreachable or returns a non-200 status.
A failure row is still logged so the gap is visible in history. Stdlib only.
"""
import datetime
import hashlib
import os
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG = os.path.join(ROOT, "data", "captures", "injury_capture_log.tsv")
URL = "https://www.nfl.com/injuries/"
USER_AGENT = "FL1-injury-capture/1.0 (+https://github.com/sassnarep3-star/FL1)"
TIMEOUT_S = 30
HEADER = "utc_time\turl\thttp_status\tbytes\tsha256\tresult\n"


def fetch(url=URL, opener=urllib.request.urlopen):
    """Return (status, body_bytes). Raises on transport errors."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener(req, timeout=TIMEOUT_S) as resp:
        status = resp.status
        body = resp.read()
    return status, body


def make_row(utc_time, url, status, body, result):
    sha = hashlib.sha256(body).hexdigest() if body is not None else ""
    nbytes = len(body) if body is not None else 0
    return "\t".join([utc_time, url, str(status), str(nbytes), sha, result]) + "\n"


def append_row(row, log_path=LOG):
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    new = not os.path.exists(log_path) or os.path.getsize(log_path) == 0
    with open(log_path, "a", encoding="utf-8", newline="\n") as fh:
        if new:
            fh.write(HEADER)
        fh.write(row)


def capture(url=URL, log_path=LOG, opener=urllib.request.urlopen, now=None):
    """Run one capture. Returns 0 on success, 1 on failure. Never writes page content."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        status, body = fetch(url, opener=opener)
    except urllib.error.HTTPError as exc:
        append_row(make_row(stamp, url, exc.code, None, "FAIL_HTTP"), log_path)
        print("FAIL: %s returned HTTP %s" % (url, exc.code))
        return 1
    except Exception as exc:  # transport, TLS, DNS, timeout
        append_row(make_row(stamp, url, "ERR", None, "FAIL_UNREACHABLE"), log_path)
        print("FAIL: %s unreachable: %s" % (url, type(exc).__name__))
        return 1
    if status != 200 or len(body) == 0:
        append_row(make_row(stamp, url, status, body, "FAIL_STATUS_OR_EMPTY"), log_path)
        print("FAIL: %s status %s, %d bytes" % (url, status, len(body)))
        return 1
    append_row(make_row(stamp, url, status, body, "OK"), log_path)
    print("OK: %s HTTP %s, %d bytes, sha256 %s" % (url, status, len(body),
                                                  hashlib.sha256(body).hexdigest()[:16]))
    return 0


if __name__ == "__main__":
    sys.exit(capture())
