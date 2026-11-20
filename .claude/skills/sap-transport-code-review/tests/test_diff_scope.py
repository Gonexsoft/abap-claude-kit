"""Offline unit tests for scope_to_transport.py.

Pure text-in/JSON-out tool: no network, no SAP connection, no subprocess.

Run from the repository root:

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import tempfile
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SCOPE_PATH = (
    _REPO_ROOT / "scripts" / "scope_to_transport.py"
)


def _load_scope_module():
    spec = importlib.util.spec_from_file_location("scope_to_transport_under_test", _SCOPE_PATH)
    assert spec and spec.loader, f"could not build import spec for {_SCOPE_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scope = _load_scope_module()


BEFORE_SRC = "\n".join([
    "REPORT zexample.",
    "DATA lv_x TYPE i.",
    "SELECT SINGLE * FROM zfoo INTO lv_x WHERE id = 1.",
    "WRITE lv_x.",
])

# Line 3's SELECT was rewritten to name its fields (was select-star before);
# a brand-new line 5 was appended. Lines 1-2 and 4 are untouched.
AFTER_SRC = "\n".join([
    "REPORT zexample.",
    "DATA lv_x TYPE i.",
    "SELECT SINGLE field1 FROM zfoo INTO lv_x WHERE id = 1.",
    "WRITE lv_x.",
    "WRITE 'done'.",
])


class ChangedRangesTests(unittest.TestCase):
    def test_identical_sources_yield_no_ranges(self):
        self.assertEqual(scope.changed_ranges(BEFORE_SRC, BEFORE_SRC), [])

    def test_modified_and_appended_lines_are_ranged(self):
        ranges = scope.changed_ranges(BEFORE_SRC, AFTER_SRC)
        touched = {ln for r in ranges for ln in range(r["start"], r["end"] + 1)}
        self.assertIn(3, touched)   # the rewritten SELECT
        self.assertIn(5, touched)   # the newly appended line
        self.assertNotIn(1, touched)
        self.assertNotIn(2, touched)
        self.assertNotIn(4, touched)

    def test_pure_deletion_contributes_no_range(self):
        before = "\n".join(["A", "B", "C"])
        after = "\n".join(["A", "C"])
        # Deleting line 2 doesn't add/modify any line that exists in `after`.
        self.assertEqual(scope.changed_ranges(before, after), [])


class ScopeFindingsTests(unittest.TestCase):
    def test_finding_inside_range_is_marked_in_scope(self):
        findings = [{"id": "select-star", "line": 3}, {"id": "select-in-loop", "line": 1}]
        ranges = [{"start": 3, "end": 3}, {"start": 5, "end": 5}]
        scoped = scope.scope_findings(findings, ranges)
        by_id = {f["id"]: f for f in scoped}
        self.assertTrue(by_id["select-star"]["in_transport_scope"])
        self.assertFalse(by_id["select-in-loop"]["in_transport_scope"])

    def test_finding_without_line_is_marked_out_of_scope(self):
        findings = [{"id": "native-sql-block"}]
        scoped = scope.scope_findings(findings, [{"start": 1, "end": 100}])
        self.assertFalse(scoped[0]["in_transport_scope"])

    def test_original_finding_fields_are_preserved(self):
        findings = [{"id": "select-star", "line": 3, "severity": "low", "message": "m"}]
        scoped = scope.scope_findings(findings, [{"start": 3, "end": 3}])
        self.assertEqual(scoped[0]["severity"], "low")
        self.assertEqual(scoped[0]["message"], "m")


class ReadSourceTests(unittest.TestCase):
    def test_reads_plain_abap_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".abap", delete=False, encoding="utf-8") as f:
            f.write(BEFORE_SRC)
            path = f.name
        self.assertEqual(scope._read_source(path), BEFORE_SRC)

    def test_reads_source_field_from_json_file(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"name": "ZEXAMPLE", "type": "PROG/P", "source": BEFORE_SRC}, f)
            path = f.name
        self.assertEqual(scope._read_source(path), BEFORE_SRC)


class MainEndToEndTests(unittest.TestCase):
    def test_reports_no_changes_when_sources_identical(self):
        import contextlib
        import io
        import sys

        with tempfile.NamedTemporaryFile("w", suffix=".abap", delete=False, encoding="utf-8") as fb:
            fb.write(BEFORE_SRC)
            before_path = fb.name
        with tempfile.NamedTemporaryFile("w", suffix=".abap", delete=False, encoding="utf-8") as fa:
            fa.write(BEFORE_SRC)
            after_path = fa.name

        old_argv = sys.argv
        try:
            sys.argv = ["scope_to_transport.py", "--before", before_path, "--after", after_path]
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = scope.main()
        finally:
            sys.argv = old_argv
        self.assertEqual(rc, 0)
        result = json.loads(buf.getvalue())
        self.assertFalse(result["has_changes"])

    def test_tags_findings_end_to_end(self):
        import contextlib
        import io
        import sys

        with tempfile.NamedTemporaryFile("w", suffix=".abap", delete=False, encoding="utf-8") as fb:
            fb.write(BEFORE_SRC)
            before_path = fb.name
        with tempfile.NamedTemporaryFile("w", suffix=".abap", delete=False, encoding="utf-8") as fa:
            fa.write(AFTER_SRC)
            after_path = fa.name
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as ff:
            json.dump({"findings": [
                {"id": "select-star", "line": 3},
                {"id": "unrelated-old-finding", "line": 1},
            ]}, ff)
            findings_path = ff.name

        old_argv = sys.argv
        try:
            sys.argv = ["scope_to_transport.py", "--before", before_path, "--after", after_path,
                        "--findings", findings_path]
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                rc = scope.main()
        finally:
            sys.argv = old_argv

        self.assertEqual(rc, 0)
        result = json.loads(buf.getvalue())
        self.assertTrue(result["has_changes"])
        by_id = {f["id"]: f for f in result["findings"]}
        self.assertTrue(by_id["select-star"]["in_transport_scope"])
        self.assertFalse(by_id["unrelated-old-finding"]["in_transport_scope"])
        self.assertEqual(result["summary"]["in_transport_scope"], 1)
        self.assertEqual(result["summary"]["outside_transport_scope"], 1)


if __name__ == "__main__":
    unittest.main()
