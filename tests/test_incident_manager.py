"""
Tests for incident_manager.py
"""

import csv
import os
from incident_manager import create_incident, save_incidents, print_summary


def test_create_incident_has_all_expected_fields():
    incident = create_incident("EC2 Instance", "i-12345", "Instance is stopped", "LOW")

    assert incident["resource_type"] == "EC2 Instance"
    assert incident["resource_id"] == "i-12345"
    assert incident["issue"] == "Instance is stopped"
    assert incident["severity"] == "LOW"
    assert "timestamp" in incident  # exact value isn't important, just that it exists


def test_save_incidents_returns_none_when_list_is_empty(tmp_path):
    result = save_incidents([], folder=str(tmp_path))
    assert result is None


def test_save_incidents_writes_a_csv_file(tmp_path):
    incidents = [
        create_incident("EBS Volume", "vol-1", "Unattached volume", "MEDIUM"),
        create_incident("Elastic IP", "1.2.3.4", "Unused IP", "LOW"),
    ]

    filepath = save_incidents(incidents, folder=str(tmp_path))

    # The file should actually exist on disk
    assert os.path.exists(filepath)

    # And it should contain the same data we passed in
    with open(filepath, newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 2
    assert rows[0]["resource_id"] == "vol-1"
    assert rows[1]["severity"] == "LOW"


def test_print_summary_with_no_incidents(capsys):
    print_summary([])
    output = capsys.readouterr().out
    assert "No incidents found" in output


def test_print_summary_with_incidents(capsys):
    incidents = [
        create_incident("EC2 Instance", "i-1", "Stopped", "LOW"),
        create_incident("EBS Volume", "vol-1", "Unattached", "MEDIUM"),
    ]

    print_summary(incidents)
    output = capsys.readouterr().out

    assert "2 incident(s) found" in output
    assert "MEDIUM: 1" in output
    assert "LOW: 1" in output
