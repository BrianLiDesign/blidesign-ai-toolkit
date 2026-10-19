"""Verify owned additions survive upstream regeneration without duplication."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from provenance import apply_skill_overlays, digest_directory
from update_upstreams import flatten_skills
from verify import VerificationError, validate_source_provenance


class SkillOverlayTests(unittest.TestCase):
    def test_regeneration_preserves_source_and_repeat_application_is_identical(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source/one"
            source.mkdir(parents=True)
            original = "---\nname: one\n---\n\nOriginal upstream body.\n"
            (source / "SKILL.md").write_text(original, encoding="utf-8")
            overlay = root / "overlay.json"
            overlay.write_text(json.dumps({"schemaVersion": 1, "skills": {"one": "Owned guidance."}}))
            stage = root / "stage"
            flatten_skills(root / "source", stage)
            apply_skill_overlays(stage, overlay)
            generated = (stage / "one/SKILL.md").read_text()
            self.assertTrue(generated.startswith(original.rstrip()))
            self.assertIn("Owned guidance.", generated)
            digest = digest_directory(stage)
            apply_skill_overlays(stage, overlay)
            self.assertEqual(digest_directory(stage), digest)
            self.assertEqual((source / "SKILL.md").read_text(), original)

    def test_invalid_target_rejects_all_overlays_before_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / "skills/one/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("original")
            overlay = root / "overlay.json"
            for name in ["missing", "../outside"]:
                overlay.write_text(json.dumps({"schemaVersion": 1, "skills": {"one": "new", name: "bad"}}))
                with self.assertRaises(ValueError):
                    apply_skill_overlays(root / "skills", overlay)
                self.assertEqual(target.read_text(), "original")

    def test_verifier_detects_overlay_drift_even_if_content_digest_was_updated(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            skills = root / "skills"
            target = skills / "one/SKILL.md"
            target.parent.mkdir(parents=True)
            target.write_text("upstream body")
            (root / "LICENSE").write_text("fixture license")
            overlay = root / "overlay.json"
            overlay.write_text(json.dumps({"schemaVersion": 1, "skills": {"one": "owned guidance"}}))
            source = {"commit": "a" * 40, "destination": "skills", "license": "MIT", "licensePath": "LICENSE", "overlayPath": "overlay.json", "contentSha256": digest_directory(skills)}
            with self.assertRaisesRegex(VerificationError, "overlay differs"):
                validate_source_provenance(root, "fixture", source)
            apply_skill_overlays(skills, overlay)
            source["contentSha256"] = digest_directory(skills)
            validate_source_provenance(root, "fixture", source)
