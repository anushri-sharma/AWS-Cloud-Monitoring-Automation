"""
Tests for aws_health_check.py

We never want tests to make real calls to AWS (that would be slow,
cost money, and require real credentials). Instead, we "mock" boto3
so it returns fake, predictable data that looks like a real AWS
response.
"""

from unittest.mock import patch, MagicMock
from botocore.exceptions import NoCredentialsError, ClientError
from aws_health_check import check_ec2_health, check_s3_health


@patch("aws_health_check.boto3.client")
def test_check_ec2_health_counts_running_and_stopped(mock_boto_client):
    # Arrange: fake EC2 client that returns two instances (1 running, 1 stopped)
    fake_ec2 = MagicMock()
    mock_boto_client.return_value = fake_ec2

    fake_page = {
        "Reservations": [
            {"Instances": [
                {"InstanceId": "i-111", "State": {"Name": "running"}, "InstanceType": "t2.micro"},
                {"InstanceId": "i-222", "State": {"Name": "stopped"}, "InstanceType": "t2.micro"},
            ]}
        ]
    }
    fake_ec2.get_paginator.return_value.paginate.return_value = [fake_page]

    # Act
    result = check_ec2_health("us-east-1")

    # Assert
    assert result["error"] is None
    assert result["running"] == 1
    assert result["stopped"] == 1
    assert len(result["instances"]) == 2


@patch("aws_health_check.boto3.client")
def test_check_ec2_health_handles_missing_credentials(mock_boto_client):
    mock_boto_client.side_effect = NoCredentialsError()

    result = check_ec2_health("us-east-1")

    assert result["instances"] == []
    assert "credentials" in result["error"].lower()


@patch("aws_health_check.boto3.client")
def test_check_s3_health_flags_unreachable_buckets(mock_boto_client):
    fake_s3 = MagicMock()
    mock_boto_client.return_value = fake_s3

    fake_s3.list_buckets.return_value = {
        "Buckets": [{"Name": "good-bucket"}, {"Name": "bad-bucket"}]
    }

    # good-bucket works, bad-bucket raises an error when we check it
    def fake_head_bucket(Bucket):
        if Bucket == "bad-bucket":
            raise ClientError(
                error_response={"Error": {"Code": "403", "Message": "Forbidden"}},
                operation_name="HeadBucket",
            )
        return {}

    fake_s3.head_bucket.side_effect = fake_head_bucket

    result = check_s3_health("us-east-1")

    statuses = {b["name"]: b["status"] for b in result["buckets"]}
    assert statuses["good-bucket"] == "OK"
    assert statuses["bad-bucket"] == "UNREACHABLE"
