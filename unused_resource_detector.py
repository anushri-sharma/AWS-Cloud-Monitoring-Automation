"""
unused_resource_detector.py
----------------------------
Looks for AWS resources that are sitting idle and quietly costing money.
This is a classic "cost optimization" task that cloud support/junior
cloud engineers get asked to do.

We check for three common culprits:
  1. Unattached EBS volumes   (not connected to any EC2 instance)
  2. Unused Elastic IPs        (allocated but not attached to anything)
  3. Stopped EC2 instances     (not running, but still worth reviewing)
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError


def find_unattached_ebs_volumes(region):
    """Find EBS volumes that are not attached to any instance."""
    volumes = []
    try:
        ec2 = boto3.client("ec2", region_name=region)
        response = ec2.describe_volumes(
            Filters=[{"Name": "status", "Values": ["available"]}]
        )
        for vol in response["Volumes"]:
            volumes.append({
                "id": vol["VolumeId"],
                "size_gb": vol["Size"],
            })
        return volumes, None

    except (NoCredentialsError, EndpointConnectionError, ClientError) as e:
        return [], str(e)


def find_unused_elastic_ips(region):
    """Find Elastic IPs that are allocated but not attached to an instance."""
    unused_ips = []
    try:
        ec2 = boto3.client("ec2", region_name=region)
        response = ec2.describe_addresses()
        for address in response["Addresses"]:
            if "InstanceId" not in address:
                unused_ips.append({
                    "public_ip": address.get("PublicIp"),
                    "allocation_id": address.get("AllocationId"),
                })
        return unused_ips, None

    except (NoCredentialsError, EndpointConnectionError, ClientError) as e:
        return [], str(e)


def find_stopped_ec2_instances(region):
    """Find EC2 instances that are currently stopped (candidates for cleanup)."""
    stopped = []
    try:
        ec2 = boto3.client("ec2", region_name=region)
        response = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
        )
        for reservation in response["Reservations"]:
            for instance in reservation["Instances"]:
                stopped.append({
                    "id": instance["InstanceId"],
                    "type": instance.get("InstanceType", "unknown"),
                })
        return stopped, None

    except (NoCredentialsError, EndpointConnectionError, ClientError) as e:
        return [], str(e)
