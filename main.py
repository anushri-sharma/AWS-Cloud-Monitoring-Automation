"""
main.py
-------
Entry point for the Cloud Infrastructure Monitoring & Incident
Management System.

Run this file to:
  1. Check local system health (CPU / memory / disk)
  2. Check AWS EC2 and S3 health
  3. Detect unused/wasted AWS resources
  4. Turn any problems found into "incidents" and save them to a CSV report

Usage:
    python main.py
"""

import config
from system_utils import get_system_details
from aws_health_check import check_ec2_health, check_s3_health
from unused_resource_detector import (
    find_unattached_ebs_volumes,
    find_unused_elastic_ips,
    find_stopped_ec2_instances,
)
from incident_manager import create_incident, save_incidents, print_summary


def run_system_health_check(incidents):
    print("== 1. Local System Health ==")
    info = get_system_details()
    print(f"   CPU: {info['cpu']}%  |  Memory: {info['memory']}%  |  Disk: {info['disk']}%")

    if info["cpu"] > config.CPU_THRESHOLD:
        incidents.append(create_incident("System", "localhost", f"High CPU usage: {info['cpu']}%", "HIGH"))
    if info["memory"] > config.MEMORY_THRESHOLD:
        incidents.append(create_incident("System", "localhost", f"High memory usage: {info['memory']}%", "HIGH"))
    if info["disk"] > config.DISK_THRESHOLD:
        incidents.append(create_incident("System", "localhost", f"High disk usage: {info['disk']}%", "MEDIUM"))


def run_aws_health_check(incidents):
    print("\n== 2. AWS Health Check (EC2 & S3) ==")

    ec2_result = check_ec2_health(config.AWS_REGION)
    if ec2_result["error"]:
        print(f"   EC2 check skipped: {ec2_result['error']}")
    else:
        print(f"   EC2 instances found: {len(ec2_result['instances'])} "
              f"(running: {ec2_result['running']}, stopped: {ec2_result['stopped']})")

    s3_result = check_s3_health(config.AWS_REGION)
    if s3_result["error"]:
        print(f"   S3 check skipped: {s3_result['error']}")
    else:
        print(f"   S3 buckets found: {len(s3_result['buckets'])}")
        for bucket in s3_result["buckets"]:
            if bucket["status"] != "OK":
                incidents.append(create_incident("S3 Bucket", bucket["name"], "Bucket is unreachable", "HIGH"))


def run_unused_resource_check(incidents):
    print("\n== 3. Unused Resource Detection (Cost Optimization) ==")

    volumes, err = find_unattached_ebs_volumes(config.AWS_REGION)
    if err:
        print(f"   EBS check skipped: {err}")
    else:
        print(f"   Unattached EBS volumes: {len(volumes)}")
        for vol in volumes:
            incidents.append(create_incident(
                "EBS Volume", vol["id"], f"Unattached volume ({vol['size_gb']} GB) still incurring cost", "MEDIUM"
            ))

    ips, err = find_unused_elastic_ips(config.AWS_REGION)
    if err:
        print(f"   Elastic IP check skipped: {err}")
    else:
        print(f"   Unused Elastic IPs: {len(ips)}")
        for ip in ips:
            incidents.append(create_incident(
                "Elastic IP", ip["public_ip"], "Allocated but not attached to any instance", "LOW"
            ))

    stopped, err = find_stopped_ec2_instances(config.AWS_REGION)
    if err:
        print(f"   Stopped instance check skipped: {err}")
    else:
        print(f"   Stopped EC2 instances: {len(stopped)}")
        for inst in stopped:
            incidents.append(create_incident(
                "EC2 Instance", inst["id"], "Instance is stopped — review if still needed", "LOW"
            ))


def main():
    print("Cloud Infrastructure Monitoring & Incident Management System")
    print("=" * 60)

    incidents = []

    run_system_health_check(incidents)
    run_aws_health_check(incidents)
    run_unused_resource_check(incidents)

    print("\n== 4. Incident Report ==")
    print_summary(incidents)

    report_path = save_incidents(incidents, config.REPORT_FOLDER)
    if report_path:
        print(f"\n📄 Full report saved to: {report_path}")


if __name__ == "__main__":
    main()
