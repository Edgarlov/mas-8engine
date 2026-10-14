"""Validate UNI-AI-001 records without changing frozen KBS RC1/M7."""
import json
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from src.shared.references import validate_references

SCHEMA_PATH = Path(__file__).resolve().parents[2] / 'contracts/v1/record.schema.json'

def validate_records(records):
    """Validate record shapes and cross-record references; return IDs on success."""
    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    for record in records:
        validator.validate(record)
    return validate_references(records)
