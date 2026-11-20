"""fetch_source.py: sayfalama, satir sayisi kontrolu, izin listesi ve cikti klasoru (ag yok)."""
import argparse
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import fetch_source as fs  # noqa: E402

LINES = [f"line {i}" for i in range(1, 4502)]          # 4501 satir -> 3 sayfa


def fake_read_page(arguments):
    start = arguments["offset"]
    chunk = LINES[start - 1:start - 1 + arguments["limit"]]
    end = start + len(chunk) - 1
    page = {"content": "\n".join(chunk) + "\n", "totalLines": len(LINES),
            "lineRange": {"start": start, "end": end}, "truncated": end < len(LINES)}
    if page["truncated"]:
        page["continuation"] = {"nextOffset": end + 1}
    return page


def allowed_system():
    with open(fs.SYSTEMS_JSON, encoding="utf-8") as handle:
        return json.load(handle)["systems"][0]


class FetchSourceTest(unittest.TestCase):
    def setUp(self):
        fs.LOG_FILE = os.path.join(tempfile.gettempdir(), "fetch-source-test.log")

    def args(self, out_dir, objects, dest=None, json_out=None):
        return argparse.Namespace(dest=dest or allowed_system()["destination"], out_dir=out_dir,
                                  version="ACTIVE", json_out=json_out, transport="TR1",
                                  objects=objects)

    def test_pagination_writes_full_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            summary = fs.run(self.args(tmp, ["zprog:prog"], json_out="objeler.json"), fake_read_page)
            self.assertEqual(summary["errors"], [])
            self.assertEqual(summary["files"][0]["totalLines"], 4501)
            with open(os.path.join(tmp, "ZPROG.abap"), encoding="utf-8") as handle:
                self.assertEqual(handle.read().splitlines(), LINES)
            with open(summary["json_out"], encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["transport"], "TR1")
            self.assertEqual(payload["objects"][0]["name"], "ZPROG")
            self.assertEqual(payload["objects"][0]["type"], "PROG")

    def test_line_count_mismatch_is_error(self):
        def short_page(arguments):
            return {"content": "a\nb\n", "totalLines": 3, "truncated": False}
        with tempfile.TemporaryDirectory() as tmp:
            summary = fs.run(self.args(tmp, ["ZX:CLAS"]), short_page)
            self.assertEqual(summary["files"], [])
            self.assertIn("satir sayisi", summary["errors"][0]["error"])
            self.assertFalse(os.path.exists(os.path.join(tmp, "ZX.abap")))

    def test_sid_resolves_to_listed_destination(self):
        system = allowed_system()
        self.assertEqual(fs.resolve_destination(system["sid"]), system["destination"])

    def test_unlisted_destination_rejected_before_any_call(self):
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(fs.FetchError):
                fs.run(self.args(tmp, ["ZPROG"], dest="PRD_100_X"), calls.append)
        self.assertEqual(calls, [])

    def test_out_dir_outside_allowed_roots_rejected(self):
        with self.assertRaises(fs.FetchError):
            fs.check_out_dir(os.path.join(fs.WORKSPACE, ".claude", "hooks"))

    def test_aff_file_name_spec(self):
        ident, name, kind, file_name = fs.parse_spec("zcl_x.clas.locals_imp.abap")
        self.assertEqual(ident, {"affFileName": "zcl_x.clas.locals_imp.abap"})
        self.assertEqual((name, kind, file_name), ("ZCL_X", "CLAS", "zcl_x.clas.locals_imp.abap"))


if __name__ == "__main__":
    unittest.main()
