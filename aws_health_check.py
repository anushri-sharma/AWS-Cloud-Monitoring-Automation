"""
aws_health_check.py
--------------------
Checks the health of core AWS resources:
  1. EC2 instances  -> are they running or stopped?
  2. S3 buckets      -> can we actually reach/list them?

This mimics what a cloud support engineer does daily: log in (or run a
script) and confirm resources are up and reachable.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError


def check_ec2_health(region):
    """
    List all EC2 instances and their current state.

    Returns:
        dict: {
            "instances": [ {"id": ..., "state": ..., "type": ...}, ... ],
            "running": int,
            "stopped": int,
            "error": str or None
        }
    """
    result = {"instances": [], "running": 0, "stopped": 0, "error": None}

    try:
        ec2 = boto3.client("ec2", region_name=region)
        paginator = ec2.get_paginator("describe_instances")

        for page in paginator.paginate():
            for reservation in page["Reservations"]:
                for instance in reservation["Instances"]:
                    state = instance["State"]["Name"]
                    result["instances"].append({
                        "id": instance["InstanceId"],
                        "state": state,
                        "type": instance.get("InstanceType", "unknown"),
                    })
                    if state == "running":
                        result["running"] += 1
                    elif state == "stopped":
                        result["stopped"] += 1

    except (NoCredentialsError, EndpointConnectionError) as e:
        result["error"] = f"Could not reach AWS (check credentials/network): {e}"
    except ClientError as e:
        result["error"] = f"AWS rejected the request: {e}"

    return result


def check_s3_health(region):
    """
    List all S3 buckets and confirm each one is reachable.

    Returns:
        dict: {
            "buckets": [ {"name": ..., "status": "OK" or "UNREACHABLE"}, ... ],
            "error": str or None
        }
    """
    result = {"buckets": [], "error": None}

    try:
        s3 = boto3.client("s3", region_name=region)
        buckets = s3.list_buckets()["Buckets"]

        for bucket in buckets:
            name = bucket["Name"]
            try:
                # A lightweight call just to confirm we can actually access it
                s3.head_bucket(Bucket=name)
                status = "OK"
            except ClientError:
                status = "UNREACHABLE"

            result["buckets"].append({"name": name, "status": status})

    except (NoCredentialsError, EndpointConnectionError) as e:
        result["error"] = f"Could not reach AWS (check credentials/network): {e}"
    except ClientError as e:
        result["error"] = f"AWS rejected the request: {e}"

    return result
