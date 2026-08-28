#!/usr/bin/env python3
"""Adversarial tests for the executable Subactor usage standard."""

from __future__ import annotations

import copy
import importlib.util
import subprocess
import tempfile
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

    def test_remote_url_variants_resolve_to_same_identity(self) -> None:
        expected = ("github.com", "wellmanifest/how-to-use-subactor")
        self.assertEqual(conformance.parse_repository_remote("git@github.com:wellmanifest/how-to-use-subactor.git"), expected)
        self.assertEqual(conformance.parse_repository_remote("https://github.com/wellmanifest/how-to-use-subactor.git"), expected)
        self.assertEqual(conformance.parse_repository_remote("ssh://git@github.com/wellmanifest/how-to-use-subactor.git"), expected)

    def test_local_path_is_not_repository_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            checkout = workspace / "subactor" / "how-to-use-subactor"
            checkout.mkdir(parents=True)
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            subprocess.run(
                ["git", "-C", str(checkout), "remote", "add", "origin", "git@github.com:wellmanifest/how-to-use-subactor.git"],
                check=True,
            )
            result = conformance.inspect_repository_identity(
                checkout,
                workspace_root=workspace,
                expected_ref="wellmanifest/how-to-use-subactor",
            )
            self.assertFalse(result["valid"])
            self.assertEqual(result["repositoryRef"], "wellmanifest/how-to-use-subactor")
            self.assertEqual(result["expectedPath"], str(workspace / "wellmanifest" / "how-to-use-subactor"))
            self.assertIn("USAGE-REPOSITORY-PATH-001", {item["code"] for item in result["failures"]})

    def test_arbitrary_checkout_path_is_valid_without_layout_policy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "arbitrary-name"
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            subprocess.run(
                ["git", "-C", str(checkout), "remote", "add", "origin", "https://github.com/wellmanifest/how-to-use-subactor.git"],
                check=True,
            )
            result = conformance.inspect_repository_identity(
                checkout,
                expected_ref="wellmanifest/how-to-use-subactor",
            )
            self.assertTrue(result["valid"], result["failures"])
            self.assertFalse(result["pathPolicyChecked"])
            self.assertIsNone(result["placementConformant"])

    def test_expected_repository_ref_is_checked_independently_of_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            checkout = Path(temporary) / "checkout"
            subprocess.run(["git", "init", "-q", str(checkout)], check=True)
            subprocess.run(
                ["git", "-C", str(checkout), "remote", "add", "origin", "git@github.com:subactor/how-to-use-subactor.git"],
                check=True,
            )
            result = conformance.inspect_repository_identity(
                checkout,
                expected_ref="wellmanifest/how-to-use-subactor",
            )
            self.assertFalse(result["valid"])
            self.assertIn("USAGE-REPOSITORY-REF-001", {item["code"] for item in result["failures"]})

    def test_linked_worktree_uses_primary_checkout_for_layout(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            primary = workspace / "wellmanifest" / "demo"
            linked = workspace / ".worktrees" / "demo--ticket-001"
            subprocess.run(["git", "init", "-q", str(primary)], check=True)
            subprocess.run(["git", "-C", str(primary), "config", "user.email", "test@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(primary), "config", "user.name", "Test"], check=True)
            subprocess.run(["git", "-C", str(primary), "commit", "--allow-empty", "-qm", "seed"], check=True)
            subprocess.run(["git", "-C", str(primary), "remote", "add", "origin", "git@github.com:wellmanifest/demo.git"], check=True)
            subprocess.run(["git", "-C", str(primary), "worktree", "add", "-qb", "ticket/001", str(linked)], check=True)
            result = conformance.inspect_repository_identity(
                linked,
                workspace_root=workspace,
                expected_ref="wellmanifest/demo",
            )
            self.assertTrue(result["valid"], result["failures"])
            self.assertEqual(result["checkoutKind"], "linked")
            self.assertEqual(result["primaryCheckoutPath"], str(primary))


if __name__ == "__main__":
    unittest.main()
