"""Contract validation for UNI-AI-001 (Draft 2020-12).

These tests exercise the transfer contract, not scientific truth or RC1/M7.
"""
import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts" / "v1"


def load_json(relative_path):
    return json.loads((CONTRACTS / relative_path).read_text(encoding="utf-8"))


class TestIntegrationContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.schema = load_json("record.schema.json")
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(
            cls.schema, format_checker=FormatChecker()
        )

    def test_declared_dialect(self):
        self.assertEqual(
            self.schema["$schema"], "https://json-schema.org/draft/2020-12/schema"
        )

    def test_positive_fixtures(self):
        records = load_json("examples/valid_records.json")
        self.assertTrue(records)
        for record in records:
            with self.subTest(record_id=record["record_id"]):
                errors = list(self.validator.iter_errors(record))
                self.assertEqual([], errors, [e.message for e in errors])

    def test_negative_fixtures(self):
        cases = load_json("examples/invalid_cases.json")["cases"]
        self.assertTrue(cases)
        for case in cases:
            with self.subTest(case_id=case["case_id"]):
                errors = list(self.validator.iter_errors(case["record"]))
                self.assertTrue(errors, "Invalid fixture unexpectedly passed schema")

    def test_fixture_record_ids_unique(self):
        records = load_json("examples/valid_records.json")
        ids = [r["record_id"] for r in records]
        self.assertEqual(len(ids), len(set(ids)))

    def test_fixture_references_resolve(self):
        records = load_json("examples/valid_records.json")
        by_id = {r["record_id"]: r for r in records}
        for record in records:
            refs = list(record.get("evidence_refs", []))
            refs += record.get("depends_on", [])
            payload = record["payload"]
            for key in ("subject_id", "object_id", "target_id"):
                if key in payload:
                    refs.append(payload[key])
            for key in ("premise_ids", "rival_ids", "input_ids", "dependency_ids"):
                refs += payload.get(key, [])
            for ref in refs:
                with self.subTest(record_id=record["record_id"], ref=ref):
                    self.assertIn(ref, by_id)
            for ref in record.get("evidence_refs", []):
                self.assertEqual("evidence", by_id[ref]["record_type"])


if __name__ == "__main__":
    unittest.main()
