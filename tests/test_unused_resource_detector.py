"""
Tests for unused_resource_detector.py

Same approach as test_aws_health_check.py: mock boto3 so no real AWS
calls happen, and check that our functions correctly interpret the
(fake) AWS responses.
"""

from unittest.mock import patch, MagicMock
from botocore.exceptions import NoCredentialsError
from unused_resource_detector import (
    find_unattached_ebs_volumes,
    find_unused_elastic_ips,
    find_stopped_ec2_instances,
)


@patch("unused_resource_detector.boto3.client")
def test_find_unattached_ebs_volumes(mock_boto_client):
    fake_ec2 = MagicMock()
    mock_boto_client.return_value = fake_ec2
    fake_ec2.describe_volumes.return_value = {
        "Volumes": [{"VolumeId": "vol-1", "Size": 20}]
    }

    volumes, error = find_unattached_ebs_volumes("us-east-1")

    assert error is None
    assert volumes == [{"id": "vol-1", "size_gb": 20}]
    # Confirm we only asked AWS for volumes in "available" (unattached) state
    _, kwargs = fake_ec2.describe_volumes.call_args
    assert kwargs["Filters"][0]["Values"] == ["available"]


@patch("unused_resource_detector.boto3.client")
def test_find_unused_elastic_ips_only_returns_unattached(mock_boto_client):
    fake_ec2 = MagicMock()
    mock_boto_client.return_value = fake_ec2
    fake_ec2.describe_addresses.return_value = {
        "Addresses": [
            {"PublicIp": "1.1.1.1", "AllocationId": "eipalloc-1", "InstanceId": "i-1"},  # attached
            {"PublicIp": "2.2.2.2", "AllocationId": "eipalloc-2"},  # NOT attached
        ]
    }

    unused_ips, error = find_unused_elastic_ips("us-east-1")

    assert error is None
    assert len(unused_ips) == 1
    assert unused_ips[0]["public_ip"] == "2.2.2.2"


@patch("unused_resource_detector.boto3.client")
def test_find_stopped_ec2_instances(mock_boto_client):
    fake_ec2 = MagicMock()
    mock_boto_client.return_value = fake_ec2
    fake_ec2.describe_instances.return_value = {
        "Reservations": [
            {"Instances": [{"InstanceId": "i-999", "InstanceType": "t2.micro"}]}
        ]
    }

    stopped, error = find_stopped_ec2_instances("us-east-1")

    assert error is None
    assert stopped == [{"id": "i-999", "type": "t2.micro"}]


@patch("unused_resource_detector.boto3.client")
def test_find_unattached_ebs_volumes_handles_missing_credentials(mock_boto_client):
    mock_boto_client.side_effect = NoCredentialsError()

    volumes, error = find_unattached_ebs_volumes("us-east-1")

    assert volumes == []
    assert error is not None
