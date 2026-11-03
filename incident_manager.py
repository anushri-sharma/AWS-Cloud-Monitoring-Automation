"""
incident_manager.py
--------------------
A very simple "incident management" layer.

Instead of a full ticketing system, this module does the core idea of
incident management on a small scale:
  1. Turn a detected problem into a structured "incident" record
  2. Assign it a severity
  3. Save all incidents from a run into a CSV report (like a log a
     support team could review, or attach to a Jira ticket)
"""

import csv
import os
from datetime import datetime


def create_incident(resource_type, resource_id, issue, severity):
    """Build a single incident record with a timestamp."""
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "resource_type": resource_type,
        "resource_id": resource_id,
        "issue": issue,
        "severity": severity,
    }


def save_incidents(incidents, folder):
    """
    Write all incidents to a timestamped CSV file.

    Returns:
        str: path to the saved file (or None if there were no incidents)
    """
    if not incidents:
        return None

    os.makedirs(folder, exist_ok=True)
    filename = f"incident_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = os.path.join(folder, filename)

    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(incidents[0].keys()))
        writer.writeheader()
        writer.writerows(incidents)

    return filepath


def print_summary(incidents):
    """Print a quick, readable summary of incidents grouped by severity."""
    if not incidents:
        print("\n✅ No incidents found. Everything looks healthy.")
        return

    counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for incident in incidents:
        counts[incident["severity"]] = counts.get(incident["severity"], 0) + 1

    print(f"\n⚠️  {len(incidents)} incident(s) found:")
    print(f"   HIGH: {counts.get('HIGH', 0)}  |  MEDIUM: {counts.get('MEDIUM', 0)}  |  LOW: {counts.get('LOW', 0)}")
    print()
    for incident in incidents:
        print(f"   [{incident['severity']}] {incident['resource_type']} "
              f"({incident['resource_id']}): {incident['issue']}")
