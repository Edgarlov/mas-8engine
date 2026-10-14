"""Cross-record reference checks for UNI-AI-001 contract v1.

This complements, but never replaces, JSON Schema Draft 2020-12 validation.
It checks graph consistency, not whether evidence is factually true.
"""
from collections.abc import Mapping


class ReferenceViolation(ValueError):
    """A cross-record invariant failed; ``code`` identifies the invariant."""

    def __init__(self, code, record_id, target_id=None):
        self.code = code
        self.record_id = record_id
        self.target_id = target_id
        super().__init__(f"{code}: {record_id} -> {target_id}")


def validate_references(records):
    """Check references within a complete list of versioned records.

    Run the official JSON Schema validator separately for individual shapes.
    Records are neither altered nor reclassified by this function.
    """
    if not isinstance(records, list):
        raise ReferenceViolation("RECORD_SET_NOT_LIST", "<root>")
    by_id = {}
    for position, record in enumerate(records):
        if not isinstance(record, Mapping) or not isinstance(record.get("record_id"), str):
            raise ReferenceViolation("MALFORMED_RECORD", str(position))
        record_id = record["record_id"]
        if record_id in by_id:
            raise ReferenceViolation("DUPLICATE_ID", record_id)
        by_id[record_id] = record

    def check(source_id, target_id, expected_type=None):
        if target_id not in by_id:
            raise ReferenceViolation("MISSING_REFERENCE", source_id, target_id)
        if expected_type and by_id[target_id].get("record_type") != expected_type:
            raise ReferenceViolation("WRONG_REFERENCE_TYPE", source_id, target_id)

    dependencies = {}
    for record_id, record in by_id.items():
        payload = record.get("payload", {})
        if not isinstance(payload, Mapping):
            raise ReferenceViolation("MALFORMED_PAYLOAD", record_id)
        for target_id in record.get("evidence_refs", []):
            check(record_id, target_id, "evidence")
        for target_id in record.get("depends_on", []):
            check(record_id, target_id)
        for key in ("subject_id", "object_id", "target_id"):
            if key in payload:
                check(record_id, payload[key])
        for key, expected in (
            ("premise_ids", "claim"),
            ("rival_ids", "hypothesis"),
            ("input_ids", None),
            ("dependency_ids", "work_item"),
        ):
            for target_id in payload.get(key, []):
                check(record_id, target_id, expected)
        if record.get("record_type") == "work_item":
            dependencies[record_id] = payload.get("dependency_ids", [])

    visiting = set()
    visited = set()

    def visit(node):
        if node in visiting:
            raise ReferenceViolation("WORK_DEPENDENCY_CYCLE", node)
        if node in visited:
            return
        visiting.add(node)
        for predecessor in dependencies[node]:
            visit(predecessor)
        visiting.remove(node)
        visited.add(node)

    for record_id in dependencies:
        visit(record_id)
    return tuple(by_id)
