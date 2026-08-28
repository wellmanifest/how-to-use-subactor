#!/usr/bin/env python3
"""Adversarial tests for the executable Subactor usage standard."""

from __future__ import annotations

import copy
import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("conformance.py")
SPEC = importlib.util.spec_from_file_location("subactor_usage_conformance", MODULE_PATH)
assert SPEC and SPEC.loader
conformance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(conformance)


class ConformanceTest(unittest.TestCase):
    def test_published_profiles_are_valid(self) -> None:
        result = conformance.check(run_discovery=False)
        self.assertTrue(result["valid"], result["failures"])

    def test_external_write_without_bound_evidence_is_rejected(self) -> None:
        profile = conformance.load_json(conformance.ROOT / "docs/profiles/founder-cli.v1.json")
        broken = copy.deepcopy(profile)
        operation = next(item for item in broken["operations"] if item["effect"] == "external_write")
        operation["requiredEvidence"] = ["ticket"]
        failures: list[dict[str, str]] = []
        conformance.validate_interface(broken, "fixture", failures)
        self.assertIn("USAGE-EVIDENCE-001", {item["code"] for item in failures})

    def test_hardware_write_without_device_identity_is_rejected(self) -> None:
        profile = conformance.load_json(conformance.ROOT / "docs/profiles/c2004-refactoring.v1.json")
        broken = copy.deepcopy(profile)
        flash = next(item for item in broken["stages"] if item["effect"] == "hardware_write")
        flash["requiredEvidence"].remove("device_identity_readback")
        failures: list[dict[str, str]] = []
        conformance.validate_project(broken, "fixture", failures)
        self.assertIn("USAGE-HARDWARE-001", {item["code"] for item in failures})

    def test_project_profile_cannot_embed_commands(self) -> None:
        profile = conformance.load_json(conformance.ROOT / "docs/profiles/c2004-refactoring.v1.json")
        broken = copy.deepcopy(profile)
        broken["command"] = "arbitrary-shell"
        failures: list[dict[str, str]] = []
        conformance.validate_project(broken, "fixture", failures)
        self.assertIn("USAGE-PROJECT-001", {item["code"] for item in failures})


if __name__ == "__main__":
    unittest.main()
