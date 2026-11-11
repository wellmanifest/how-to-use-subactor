#!/usr/bin/env python3
"""Adversarial unit tests for Subactor communication conformance."""

from __future__ import annotations

import copy
import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("conformance.py")
SPEC = importlib.util.spec_from_file_location("subactor_comm_conformance", MODULE_PATH)
assert SPEC and SPEC.loader
conformance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(conformance)


def _valid_case(case_id: str) -> dict:
    suite = conformance.load_json(conformance.ROOT / "fixtures" / "valid.json")
    case = next(item for item in suite["cases"] if item["id"] == case_id)
    return copy.deepcopy(case["document"])


class CommunicationConformanceHardeningTest(unittest.TestCase):
    def test_self_test_passes(self) -> None:
        self.assertEqual(conformance.self_test(), 0)

    def test_utc_instant_rejects_impossible_calendar_dates(self) -> None:
        self.assertEqual(conformance.utc_instant("2026-08-28T19:25:09Z"), "2026-08-28T19:25:09")
        self.assertEqual(
            conformance.utc_instant("2026-08-28T19:25:09.447Z"), "2026-08-28T19:25:09"
        )
        self.assertIsNone(conformance.utc_instant("2026-02-30T12:00:00Z"))
        self.assertIsNone(conformance.utc_instant("2026-99-99T99:99:99Z"))
        self.assertIsNone(conformance.utc_instant("2026-08-28T24:00:00Z"))

    def test_delegation_rejects_unknown_authority_mode_and_unhashable_lists(self) -> None:
        doc = _valid_case("outcome-delegation-over-mcp")
        doc["authority"]["mode"] = "root_bypass"
        doc["evidence"]["required"] = [{}]
        findings = conformance.validate_delegation(doc)
        codes = {item["code"] for item in findings}
        self.assertIn("COMM-AUTHORITY-001", codes)
        self.assertIn("COMM-EVIDENCE-001", codes)

    def test_autonomous_delegation_rejects_invalid_calendar_and_unhashable_ops(self) -> None:
        doc = _valid_case("bounded-autonomous-contract-delegation")
        doc["authority"]["contractBounds"]["expiresAt"] = "2026-09-31T00:00:00Z"
        doc["authority"]["contractBounds"]["allowedOperations"] = [{}]
        findings = conformance.validate_delegation(doc)
        codes = {item["code"] for item in findings}
        self.assertIn("COMM-CONTRACT-001", codes)

    def test_runtime_replan_rejects_bool_as_int_revisions(self) -> None:
        doc = _valid_case("admitted-completion")
        doc["state"] = "replan_required"
        doc["admission"]["decision"] = "REJECTED"
        doc["queue"]["revision"] = True
        doc["queue"]["previousRevision"] = False
        doc["plan"]["planHash"] = "sha256:new-plan"
        doc["plan"]["previousPlanHash"] = "sha256:old-plan"
        findings = conformance.validate_runtime(doc)
        codes = {item["code"] for item in findings}
        self.assertIn("POA-REPLAN-001", codes)
        self.assertIn("COMM-SHAPE-001", codes)

    def test_runtime_rejects_unknown_state_and_bool_bound_revision(self) -> None:
        doc = _valid_case("admitted-completion")
        doc["queue"]["revision"] = 1
        doc["admission"]["boundQueueRevision"] = True
        findings = conformance.validate_runtime(doc)
        self.assertIn("POA-ADMISSION-001", {item["code"] for item in findings})

        unknown_state = _valid_case("admitted-completion")
        unknown_state["state"] = "bypassed"
        state_findings = conformance.validate_runtime(unknown_state)
        self.assertIn("COMM-SHAPE-001", {item["code"] for item in state_findings})

    def test_mcp_rejects_empty_name_invalid_operation_class_and_non_bool_mutates(self) -> None:
        doc = _valid_case("bounded-mcp-observation")
        doc["name"] = "   "
        doc["operationClass"] = "arbitrary_exec"
        doc["mutates"] = "yes"
        findings = conformance.validate_mcp(doc)
        codes = {item["code"] for item in findings}
        self.assertIn("MCP-CAPABILITY-001", codes)
        self.assertIn("MCP-MUTATION-001", codes)

    def test_load_json_rejects_duplicate_keys_nan_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            dup = root / "dup.json"
            dup.write_text('{"a": 1, "a": 2}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                conformance.load_json(dup)

            nan_file = root / "nan.json"
            nan_file.write_text('{"a": NaN}\n', encoding="utf-8")
            with self.assertRaises(ValueError):
                conformance.load_json(nan_file)

            real_file = root / "real.json"
            real_file.write_text('{"ok": true}\n', encoding="utf-8")
            link_file = root / "link.json"
            link_file.symlink_to(real_file)
            with self.assertRaises((OSError, ValueError)):
                conformance.load_json(link_file)
            self.assertEqual(conformance.main(["check", "mcp", str(link_file)]), 2)

            outside_dir = root.parent / f"{root.name}-outside"
            outside_dir.mkdir(exist_ok=True)
            try:
                outside_json = outside_dir / "escape.json"
                outside_json.write_text('{"ok": true}\n', encoding="utf-8")
                sym_dir = root / "nested_link"
                sym_dir.symlink_to(outside_dir, target_is_directory=True)
                with self.assertRaises(ValueError):
                    conformance._rt.strict_load_json(sym_dir / "escape.json", root=root)
                with self.assertRaises(ValueError):
                    conformance._rt.strict_load_json(Path("../escape.json"), root=root)
            finally:
                for child in outside_dir.glob("*"):
                    child.unlink()
                outside_dir.rmdir()

    def test_all_docs_python_modules_stay_under_500_lines(self) -> None:
        docs_root = conformance.ROOT.parent
        for py_file in sorted(docs_root.rglob("*.py")):
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            self.assertLess(line_count, 500, f"{py_file} has {line_count} lines (>= 500)")


if __name__ == "__main__":
    unittest.main()
