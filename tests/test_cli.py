"""Tests for the CLI."""

import json
import os

import pytest
from click.testing import CliRunner

from rothos.cli import main


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "..", "fixtures")


def test_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Analyze" in result.output


def test_analyze_empty_directory(tmp_path):
    """Should handle a directory with no PDFs gracefully."""
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path)])
    assert result.exit_code == 0
    assert "No PDF files found" in result.output


def test_analyze_fixtures_dir():
    """Should analyze fixture PDFs."""
    if not os.path.exists(FIXTURES_DIR):
        pytest.skip("Fixtures directory not available")

    runner = CliRunner()
    result = runner.invoke(main, [FIXTURES_DIR])
    assert result.exit_code == 0
    # Should show the basis table
    assert "IRA Basis History" in result.output


def test_json_output():
    """--json flag should output valid JSON."""
    if not os.path.exists(FIXTURES_DIR):
        pytest.skip("Fixtures directory not available")

    runner = CliRunner()
    result = runner.invoke(main, [FIXTURES_DIR, "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert "years" in parsed
    assert len(parsed["years"]) > 0


def test_json_output_has_correct_years():
    """JSON output should contain the years from fixture PDFs."""
    if not os.path.exists(FIXTURES_DIR):
        pytest.skip("Fixtures directory not available")

    runner = CliRunner()
    result = runner.invoke(main, [FIXTURES_DIR, "--json"])
    parsed = json.loads(result.output)
    years = [y["tax_year"] for y in parsed["years"]]
    assert 2020 in years
    assert 2021 in years
    assert 2023 in years
    assert 2024 in years


def test_single_file():
    """Should analyze a single PDF file."""
    pdf_path = os.path.join(FIXTURES_DIR, "2021_transcript_with_8606.pdf")
    if not os.path.exists(pdf_path):
        pytest.skip("Fixture PDF not available")

    runner = CliRunner()
    result = runner.invoke(main, [pdf_path, "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert len(parsed["years"]) == 1
    assert parsed["years"][0]["tax_year"] == 2021


def test_json_empty_dir(tmp_path):
    """--json with empty dir should output empty JSON."""
    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--json"])
    assert result.exit_code == 0
    parsed = json.loads(result.output)
    assert parsed["years"] == []
