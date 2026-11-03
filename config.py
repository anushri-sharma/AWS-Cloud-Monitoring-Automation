"""
config.py
---------
All the "settings" for this project live here, in one place, so you
never have to hunt through the code to change something.

Beginner note: keeping configuration separate from logic is a common
real-world pattern — it makes the project easier to read and easier
to reuse in a different AWS account/region.
"""

# Which AWS region to check resources in
AWS_REGION = "us-east-1"

# --- Local system health thresholds (percent) ---
# If usage goes above these numbers, we flag it as an incident.
CPU_THRESHOLD = 80
MEMORY_THRESHOLD = 85
DISK_THRESHOLD = 90

# Folder where incident reports (CSV files) get saved
REPORT_FOLDER = "reports"
