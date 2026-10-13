"""Regression coverage for catalog CSV, audit signatures and validation."""
import csv
import pytest
from pydantic import ValidationError
from cyp_checker import CYP_DRUG_DATABASE, lookup, process_csv
from agents.base import AuditTrail
from agents.models import SystemTaskPayload
from agents.api import api_lookup, app

def test_phrase_boundary():
    assert lookup("notketoconazolexyz")["top_hit"] == "no match"
    assert lookup("ketoconazole inhibitor")["interaction_type"] == "inhibitor"

def test_catalog_api_and_static_route():
    assert len(CYP_DRUG_DATABASE) == 25
    assert api_lookup(query="tamoxifen")["top_hit"].startswith("Tamoxifen")
    assert any(route.path == "/" for route in app.routes)

def test_duplicate_output_header(tmp_path):
    source, target = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text("query,top_hit\nwarfarin,ignored\n")
    process_csv(source, target)
    with target.open(newline="") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames.count("top_hit") == 1
        assert next(reader)["top_hit"].startswith("Warfarin")

@pytest.mark.parametrize("contents", [
    "drug,drug\nwarfarin,other\n",
    "drug,\nwarfarin,other\n",
    "drug\nwarfarin,extra\n",
    'drug\n"unterminated\n',
])
def test_invalid_csv(tmp_path, contents):
    source, target = tmp_path / "in.csv", tmp_path / "out.csv"
    source.write_text(contents)
    with pytest.raises(ValueError):
        process_csv(source, target)
    assert not target.exists()

def test_audit_signatures_catch_tampering():
    trail = AuditTrail(secret_key="test")
    trail.log("actor", "tier", "event", {"value": 1})
    trail.log("actor", "tier", "event", {"value": 2})
    assert trail.verify_integrity()
    trail.logs[0]["current_hash"] = "0" * 64
    trail.logs[1]["prev_hash"] = "0" * 64
    assert not trail.verify_integrity()

def test_exposed_trail_is_copy():
    trail = AuditTrail(secret_key="test")
    trail.log("actor", "tier", "event", {})
    trail.get_trail()[0]["actor"] = "changed"
    assert trail.verify_integrity()

@pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_metric(value):
    with pytest.raises(ValidationError):
        SystemTaskPayload(task_id="case", target_identifier="research", primary_metric=value)
