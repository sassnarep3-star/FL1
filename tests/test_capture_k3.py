"""K3 (R73/R74 partial): injury capture logs metadata only and fails loudly."""
import datetime
import hashlib
import importlib.util
import io
import os
import tempfile
import unittest
import urllib.error

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "capture_injury_meta_k3.py")
WORKFLOW = os.path.join(ROOT, ".github", "workflows", "injury-capture-k3.yml")

spec = importlib.util.spec_from_file_location("capture_injury_meta_k3", SCRIPT)
cap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cap)

NOW = datetime.datetime(2026, 11, 19, 14, 0, 0, tzinfo=datetime.timezone.utc)


class FakeResp(io.BytesIO):
    def __init__(self, body, status=200):
        super().__init__(body)
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def opener_ok(body=b"<html>injury hub</html>", status=200):
    def _open(req, timeout=None):
        return FakeResp(body, status)
    return _open


def opener_http(code):
    def _open(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, code, "boom", {}, None)
    return _open


def opener_unreachable(req, timeout=None):
    raise OSError("TLS handshake failed")


class CaptureK3(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.log = os.path.join(self.tmp.name, "captures", "injury_capture_log.tsv")

    def tearDown(self):
        self.tmp.cleanup()

    def rows(self):
        with open(self.log, encoding="utf-8") as fh:
            return fh.read().splitlines()

    def test_success_logs_status_bytes_and_hash(self):
        body = b"<html>injury hub</html>"
        rc = cap.capture(log_path=self.log, opener=opener_ok(body), now=NOW)
        self.assertEqual(rc, 0)
        lines = self.rows()
        self.assertEqual(lines[0], cap.HEADER.rstrip("\n"))
        utc, url, status, nbytes, sha, result = lines[1].split("\t")
        self.assertEqual(utc, "2026-11-19T14:00:00Z")
        self.assertEqual(url, cap.URL)
        self.assertEqual(status, "200")
        self.assertEqual(int(nbytes), len(body))
        self.assertEqual(sha, hashlib.sha256(body).hexdigest())
        self.assertEqual(result, "OK")

    def test_no_page_content_written_to_repo_or_log(self):
        body = b"UNIQUE-PAGE-MARKER-7f3a"
        cap.capture(log_path=self.log, opener=opener_ok(body), now=NOW)
        with open(self.log, encoding="utf-8") as fh:
            self.assertNotIn("UNIQUE-PAGE-MARKER", fh.read())
        self.assertEqual(os.listdir(os.path.dirname(self.log)), ["injury_capture_log.tsv"])

    def test_http_error_fails_and_logs_failure(self):
        rc = cap.capture(log_path=self.log, opener=opener_http(503), now=NOW)
        self.assertEqual(rc, 1)
        utc, url, status, nbytes, sha, result = self.rows()[1].split("\t")
        self.assertEqual(status, "503")
        self.assertEqual(result, "FAIL_HTTP")
        self.assertEqual(sha, "")
        self.assertEqual(nbytes, "0")

    def test_unreachable_fails_loudly_and_logs(self):
        rc = cap.capture(log_path=self.log, opener=opener_unreachable, now=NOW)
        self.assertEqual(rc, 1)
        fields = self.rows()[1].split("\t")
        self.assertEqual(fields[2], "ERR")
        self.assertEqual(fields[5], "FAIL_UNREACHABLE")

    def test_empty_body_is_a_failure(self):
        rc = cap.capture(log_path=self.log, opener=opener_ok(b"", status=200), now=NOW)
        self.assertEqual(rc, 1)
        self.assertEqual(self.rows()[1].split("\t")[5], "FAIL_STATUS_OR_EMPTY")

    def test_non_200_success_status_is_a_failure(self):
        rc = cap.capture(log_path=self.log, opener=opener_ok(b"x", status=204), now=NOW)
        self.assertEqual(rc, 1)

    def test_log_appends_without_duplicating_header(self):
        cap.capture(log_path=self.log, opener=opener_ok(), now=NOW)
        cap.capture(log_path=self.log, opener=opener_ok(), now=NOW)
        lines = self.rows()
        self.assertEqual(len(lines), 3)
        self.assertEqual(sum(1 for l in lines if l.startswith("utc_time")), 1)

    def test_make_row_has_six_fields(self):
        row = cap.make_row("t", "u", 200, b"ab", "OK")
        self.assertEqual(len(row.rstrip("\n").split("\t")), 6)

    def test_workflow_is_scheduled_and_commits_even_on_failure(self):
        with open(WORKFLOW, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("schedule:", text)
        self.assertIn("cron:", text)
        self.assertIn("contents: write", text)
        self.assertIn("python3 scripts/capture_injury_meta_k3.py", text)
        self.assertIn("if: always()", text)
        self.assertIn("data/captures/injury_capture_log.tsv", text)
        self.assertNotIn("raw/", text)

    def test_committed_log_exists_with_header(self):
        path = os.path.join(ROOT, "data", "captures", "injury_capture_log.tsv")
        self.assertTrue(os.path.exists(path))
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.readline(), cap.HEADER)


if __name__ == "__main__":
    unittest.main()
