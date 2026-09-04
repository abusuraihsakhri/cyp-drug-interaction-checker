"""
Tests for cyp_checker module - CYP Drug Interaction Checker core functionality.
"""
import sys
import os
import tempfile
import csv
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import cyp_checker as m


class TestLookup:
    """Tests for the lookup() function."""

    def test_lookup_returns_required_fields(self):
        r = m.lookup("ketoconazole")
        assert "top_hit" in r
        assert "score" in r
        assert "interaction_type" in r
        assert "severity" in r
        assert "all" in r

    def test_lookup_finds_cyp3a4_inhibitor(self):
        r = m.lookup("ketoconazole")
        assert "CYP3A4" in r["top_hit"]
        assert r["interaction_type"] == "inhibitor"
        assert r["severity"] == "major"

    def test_lookup_finds_cyp2d6_inhibitor(self):
        r = m.lookup("fluoxetine")
        assert "CYP2D6" in r["top_hit"]
        assert r["interaction_type"] == "inhibitor"

    def test_lookup_finds_substrate(self):
        r = m.lookup("simvastatin")
        assert "substrate" in r["interaction_type"]

    def test_lookup_finds_inducer(self):
        r = m.lookup("carbamazepine")
        assert r["interaction_type"] == "inducer"

    def test_lookup_empty_query(self):
        r = m.lookup("")
        assert r["top_hit"] == "no match"
        assert r["score"] == 0

    def test_lookup_no_match(self):
        r = m.lookup("zzzznotarealdrug")
        assert r["top_hit"] == "no match"
        assert r["score"] == 0

    def test_lookup_case_insensitive(self):
        r1 = m.lookup("KETOCONAZOLE")
        r2 = m.lookup("ketoconazole")
        assert r1["top_hit"] == r2["top_hit"]

    def test_lookup_with_extra(self):
        extra = {"source": "test"}
        r = m.lookup("ketoconazole", extra=extra)
        assert r["extra"] == extra

    def test_lookup_returns_multiple_results(self):
        r = m.lookup("inhibitor")
        assert len(r["all"]) > 0
        assert len(r["all"]) <= 5

    def test_lookup_partial_match(self):
        # Search with full drug name plus extra terms to trigger substring match
        r = m.lookup("fluoxetine inhibitor")
        assert r["score"] > 0
        assert "fluoxetine" in r["top_hit"].lower()


class TestProcessCsv:
    """Tests for the process_csv() function."""

    def test_process_csv_basic(self, tmp_path):
        # Create a test CSV
        input_csv = tmp_path / "input.csv"
        output_csv = tmp_path / "output.csv"

        with open(input_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["query", "drug"])
            writer.writerow(["ketoconazole", "drug1"])
            writer.writerow(["simvastatin", "drug2"])

        results = m.process_csv(str(input_csv), str(output_csv))

        assert len(results) == 2
        assert results[0]["top_hit"] != "no match"
        assert results[1]["top_hit"] != "no match"
        assert "interaction_type" in results[0]
        assert "severity" in results[0]

    def test_process_csv_file_not_found(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            m.process_csv(str(tmp_path / "nonexistent.csv"), str(tmp_path / "out.csv"))

    def test_process_csv_empty_file(self, tmp_path):
        input_csv = tmp_path / "empty.csv"
        output_csv = tmp_path / "output.csv"
        input_csv.write_text("")

        with pytest.raises(ValueError, match="empty or has no headers"):
            m.process_csv(str(input_csv), str(output_csv))

    def test_process_csv_creates_output(self, tmp_path):
        input_csv = tmp_path / "input.csv"
        output_csv = tmp_path / "output.csv"

        with open(input_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["drug"])
            writer.writerow(["warfarin"])

        m.process_csv(str(input_csv), str(output_csv))

        assert output_csv.exists()
        with open(output_csv) as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert "top_hit" in rows[0]
            assert "lookup_score" in rows[0]


class TestMain:
    """Tests for the main() CLI entry point."""

    def test_single_lookup(self, capsys):
        assert m.main(["single", "ketoconazole"]) == 0
        captured = capsys.readouterr()
        assert "ketoconazole" in captured.out

    def test_single_lookup_with_q2(self, capsys):
        assert m.main(["single", "--query", "simvastatin"]) == 0

    def test_batch_success(self, tmp_path, capsys):
        input_csv = tmp_path / "input.csv"
        output_csv = tmp_path / "output.csv"

        with open(input_csv, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["query"])
            writer.writerow(["ketoconazole"])

        assert m.main(["batch", "--input", str(input_csv), "--output", str(output_csv)]) == 0

    def test_batch_file_not_found(self, capsys):
        assert m.main(["batch", "--input", "/nonexistent/path.csv", "--output", "/tmp/out.csv"]) == 1

    def test_default_query(self):
        assert m.main(["single"]) == 0
