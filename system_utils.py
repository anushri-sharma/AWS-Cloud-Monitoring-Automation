"""
system_utils.py
----------------
Checks the health of the LOCAL machine (the server this script runs on):
CPU usage, memory usage, and disk usage.

This is the "server health check" part of the monitoring system —
in a real job, this is the same kind of check a monitoring agent
(like CloudWatch Agent or Datadog agent) does on an EC2 instance.

Install dependency:
    pip install psutil
"""

import psutil


def get_system_details():
    """
    Collect basic system health metrics.

    Returns:
        dict: {
            "cpu": float,     # CPU usage percent
            "memory": float,  # RAM usage percent
            "disk": float     # Disk usage percent (root partition)
        }
    """
    cpu = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent  # On Windows, use "C:\\" instead

    return {
        "cpu": cpu,
        "memory": memory,
        "disk": disk,
    }


# Allows this file to still be run on its own for a quick check
if __name__ == "__main__":
    print(get_system_details())
