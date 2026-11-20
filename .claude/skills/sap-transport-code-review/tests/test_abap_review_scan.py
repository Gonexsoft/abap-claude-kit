"""Offline unit tests for the sap-transport-code-review ABAP scanner.

Pure text-in/JSON-out tool: no network, no SAP connection, no subprocess.
These tests exercise the rule set directly against small ABAP snippets.

Run from the repository root:

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import sys
import unittest

_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
_SCANNER_PATH = (
    _REPO_ROOT / "scripts" / "abap_review_scan.py"
)


def _load_scanner_module():
    spec = importlib.util.spec_from_file_location("abap_review_scan_under_test", _SCANNER_PATH)
    assert spec and spec.loader, f"could not build import spec for {_SCANNER_PATH}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


scanner = _load_scanner_module()


def _ids(findings):
    return [f["id"] for f in findings]


class CommentAndStringHandlingTests(unittest.TestCase):
    def test_full_line_comment_stripped(self):
        self.assertEqual(scanner.strip_comment('* SELECT * FROM zfoo.'), "")

    def test_inline_comment_stripped(self):
        cleaned = scanner.strip_comment("DATA(lv_x) = 1. \" trailing remark")
        self.assertEqual(cleaned, "DATA(lv_x) = 1. ")

    def test_quote_inside_string_not_treated_as_comment(self):
        # ABAP has no double-quote string delimiter, but a comment marker
        # inside a single-quoted literal must not truncate the statement.
        cleaned = scanner.strip_comment("lv_x = 'a \" b'.")
        self.assertEqual(cleaned, "lv_x = 'a \" b'.")

    def test_escaped_quote_inside_string(self):
        literals = scanner.extract_string_literals("lv_x = 'it''s fine'.")
        self.assertEqual(literals, ["it's fine"])


class PerformanceRuleTests(unittest.TestCase):
    def test_select_in_loop_flagged(self):
        source = "\n".join([
            "LOOP AT lt_items INTO ls_item.",
            "  SELECT SINGLE * FROM zfoo INTO ls_foo WHERE id = ls_item-id.",
            "ENDLOOP.",
        ])
        findings = scanner.scan_source(source)
        self.assertIn("select-in-loop", _ids(findings))

    def test_select_outside_loop_not_flagged(self):
        source = "SELECT SINGLE * FROM zfoo INTO ls_foo WHERE id = 1."
        findings = scanner.scan_source(source)
        self.assertNotIn("select-in-loop", _ids(findings))

    def test_nested_loop_flagged(self):
        source = "\n".join([
            "LOOP AT lt_outer INTO ls_outer.",
            "  LOOP AT lt_inner INTO ls_inner.",
            "  ENDLOOP.",
            "ENDLOOP.",
        ])
        findings = scanner.scan_source(source)
        self.assertIn("nested-loop", _ids(findings))

    def test_select_star_flagged(self):
        source = "SELECT * FROM zfoo INTO TABLE lt_foo WHERE id = 1."
        findings = scanner.scan_source(source)
        self.assertIn("select-star", _ids(findings))

    def test_select_named_fields_not_flagged_as_star(self):
        source = "SELECT id name FROM zfoo INTO TABLE lt_foo WHERE id = 1."
        findings = scanner.scan_source(source)
        self.assertNotIn("select-star", _ids(findings))

    def test_select_without_where_flagged(self):
        source = "SELECT id FROM zfoo INTO TABLE lt_foo."
        findings = scanner.scan_source(source)
        self.assertIn("select-without-where", _ids(findings))

    def test_select_with_where_not_flagged(self):
        source = "SELECT id FROM zfoo INTO TABLE lt_foo WHERE id = 1."
        findings = scanner.scan_source(source)
        self.assertNotIn("select-without-where", _ids(findings))

    def test_select_with_up_to_rows_not_flagged(self):
        source = "SELECT id FROM zfoo INTO TABLE lt_foo UP TO 10 ROWS."
        findings = scanner.scan_source(source)
        self.assertNotIn("select-without-where", _ids(findings))

    def test_select_endselect_flagged(self):
        source = "\n".join([
            "SELECT * FROM zfoo INTO ls_foo.",
            "  WRITE ls_foo-id.",
            "ENDSELECT.",
        ])
        findings = scanner.scan_source(source)
        self.assertIn("select-endselect-loop", _ids(findings))

    def test_select_into_table_not_flagged_as_endselect_candidate(self):
        source = "\n".join([
            "SELECT * FROM zfoo INTO TABLE lt_foo.",
            "LOOP AT lt_foo INTO ls_foo.",
            "  WRITE ls_foo-id.",
            "ENDLOOP.",
        ])
        findings = scanner.scan_source(source)
        self.assertNotIn("select-endselect-loop", _ids(findings))


class CrudRuleTests(unittest.TestCase):
    def test_insert_into_flagged(self):
        findings = scanner.scan_source("INSERT INTO zfoo VALUES @ls_foo.")
        self.assertIn("db-insert", _ids(findings))

    def test_insert_from_flagged(self):
        findings = scanner.scan_source("INSERT zfoo FROM ls_foo.")
        self.assertIn("db-insert", _ids(findings))

    def test_insert_into_internal_table_not_flagged(self):
        findings = scanner.scan_source("INSERT ls_foo INTO TABLE lt_foo.")
        self.assertNotIn("db-insert", _ids(findings))

    def test_update_flagged(self):
        findings = scanner.scan_source("UPDATE zfoo SET status = 'X' WHERE id = 1.")
        self.assertIn("db-update", _ids(findings))

    def test_delete_from_flagged(self):
        findings = scanner.scan_source("DELETE FROM zfoo WHERE id = 1.")
        self.assertIn("db-delete", _ids(findings))

    def test_delete_ambiguous_flagged(self):
        findings = scanner.scan_source("DELETE zfoo FROM wa_foo.")
        self.assertIn("db-delete-ambiguous", _ids(findings))

    def test_delete_internal_table_by_index_not_flagged(self):
        findings = scanner.scan_source("DELETE lt_foo INDEX 1.")
        ids = _ids(findings)
        self.assertNotIn("db-delete", ids)
        self.assertNotIn("db-delete-ambiguous", ids)

    def test_modify_ambiguous_flagged(self):
        findings = scanner.scan_source("MODIFY zfoo FROM ls_foo.")
        self.assertIn("db-modify", _ids(findings))

    def test_native_sql_block_flagged(self):
        source = "\n".join(["EXEC SQL.", "  UPDATE zfoo SET a = 1", "ENDEXEC."])
        findings = scanner.scan_source(source)
        self.assertIn("native-sql-block", _ids(findings))

    def test_crud_findings_are_alerts_not_issues(self):
        findings = scanner.scan_source("DELETE FROM zfoo WHERE id = 1.")
        crud = [f for f in findings if f["category"] == "crud"]
        self.assertTrue(crud)
        self.assertTrue(all(f["kind"] == "alert" for f in crud))


class EmbeddedApiRuleTests(unittest.TestCase):
    def test_hardcoded_url_flagged(self):
        findings = scanner.scan_source("lv_url = 'https://api.example.com/v1/orders'.")
        self.assertIn("hardcoded-url", _ids(findings))

    def test_hardcoded_ip_flagged(self):
        findings = scanner.scan_source("lv_host = '192.168.1.10'.")
        self.assertIn("hardcoded-host-ip", _ids(findings))

    def test_hardcoded_credential_flagged(self):
        findings = scanner.scan_source("lv_password = 'Welcome1'.")
        self.assertIn("hardcoded-credential", _ids(findings))

    def test_hardcoded_credential_in_constant_declaration_flagged(self):
        findings = scanner.scan_source("CONSTANTS c_api_key TYPE string VALUE 'abcd1234efgh'.")
        self.assertIn("hardcoded-credential", _ids(findings))

    def test_ordinary_string_literal_not_flagged(self):
        findings = scanner.scan_source("lv_message = 'Hello world'.")
        ids = _ids(findings)
        self.assertNotIn("hardcoded-url", ids)
        self.assertNotIn("hardcoded-credential", ids)
        self.assertNotIn("hardcoded-host-ip", ids)


class BatchAndCliShapeTests(unittest.TestCase):
    def test_single_object_payload(self):
        payload = {"name": "ZFOO", "type": "PROG/P", "source": "SELECT * FROM zfoo INTO TABLE lt_foo."}
        result = scanner.run_json_payload(payload)
        self.assertEqual(result["name"], "ZFOO")
        self.assertIn("gate", result)

    def test_list_payload_is_batched(self):
        payload = [
            {"name": "ZFOO", "type": "PROG/P", "source": "SELECT * FROM zfoo INTO TABLE lt_foo."},
            {"name": "ZBAR", "type": "PROG/P", "source": "WRITE 'hello'."},
        ]
        result = scanner.run_json_payload(payload)
        self.assertEqual(len(result["objects"]), 2)
        self.assertEqual(result["gate"], "REVIEW_NEEDED")

    def test_objects_wrapper_payload_keeps_transport(self):
        payload = {
            "transport": "DEVK900001",
            "objects": [{"name": "ZFOO", "type": "PROG/P", "source": "WRITE 'hello'."}],
        }
        result = scanner.run_json_payload(payload)
        self.assertEqual(result["transport"], "DEVK900001")
        self.assertEqual(result["gate"], "CLEAN")

    def test_clean_source_has_clean_gate(self):
        result = scanner.review_object("ZFOO", "PROG/P", "WRITE 'hello world'.")
        self.assertEqual(result["gate"], "CLEAN")
        self.assertEqual(result["findings"], [])

    def test_output_is_json_serializable(self):
        result = scanner.review_object(
            "ZFOO", "PROG/P",
            "LOOP AT lt_items INTO ls_item.\n"
            "  SELECT SINGLE * FROM zfoo INTO ls_foo WHERE id = ls_item-id.\n"
            "ENDLOOP.\n"
            "lv_password = 'Welcome1'.\n",
        )
        json.dumps(result)  # must not raise


if __name__ == "__main__":
    unittest.main()
