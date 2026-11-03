# AWS Cloud Health Check & Unused Resource Detection Tool

A simple Python + boto3 automation tool that checks the health of AWS
resources (EC2, S3), finds unused resources that are quietly costing
money, and logs any problems found as "incidents" in a report file.

Built with: **Python**, **boto3(AWS's Python SDK)**, **psutil**, **Pytest**

---

## Why I built this

Imagine a company that uses AWS (Amazon's cloud). Over time, people create servers, disks, and IP addresses, then forget about them. Those forgotten resources still cost money every month.

Also, someone needs to regularly check: "Are my servers running? Can I reach my storage buckets?"

Doing this by clicking through the AWS website every day is slow and boring. So I wrote a Python script that does it automatically in a few seconds.


---

## What it does

1. **Local System Health Check** — checks CPU, memory, and disk usage
   on the machine running the script (using `psutil`).

2. **AWS Health Check** — checks whether EC2 instances are running/stopped
   and whether S3 buckets are reachable (using `boto3`).

3. **Unused Resource Detection (Cost Optimization)** — finds:
   - EBS volumes that aren't attached to any instance (wasted storage cost)
   - Elastic IPs that are allocated but not attached to anything (wasted cost)
   - EC2 instances that are stopped but still around (candidates for cleanup)

4. **Incident Logging** — turns every problem found into a simple
   "incident" record (timestamp, resource, issue, severity), prints a
   summary, and saves everything to a CSV report.

---

## How it works (architecture)

```
You run:  python main.py
              |
              v
   1. Check local CPU / memory / disk        (system_utils.py)
              |
              v  
   2. Connect to AWS using boto3
      - List EC2 servers and their state     (aws_health_check.py)
      - List S3 buckets and test access
              |
              v
   3. Look for unused resources              (unused_resource_detector.py)
      - Unattached disks
      - Unused IP addresses
      - Stopped servers
              |
              v
   4. Turn every problem into an "incident"  (incident_manager.py)
      and save them in reports/incident_log_<date>.csv
```
**If AWS credentials are missing**, the script does not crash. It prints a message like "_EC2 check skipped_" and continues with the other checks.

---

## Tech stack

- **Python 3**
- **boto3** — AWS SDK for Python (talks to EC2 and S3)
- **psutil** — reads local system metrics (CPU/memory/disk)
- **AWS IAM** — for secure, limited-permission access to AWS
- **CSV** — simple, universal format for the incident report

---

## Project structure

```
cloud-infra-monitor/
├── main.py                      # Entry point — runs everything
├── config.py                    # Settings: AWS region, alert thresholds
├── system_utils.py              # Local system health (CPU/memory/disk)
├── aws_health_check.py          # EC2 & S3 health checks
├── unused_resource_detector.py  # Finds unused/wasted AWS resources
├── incident_manager.py          # Creates, prints, and saves incidents
├── requirements.txt              # Python dependencies
├── requirements-dev.txt          # + pytest, for running tests
├── tests/                        # pytest unit tests (mocked AWS calls)
│   ├── test_system_utils.py
│   ├── test_aws_health_check.py
│   ├── test_unused_resource_detector.py
│   └── test_incident_manager.py
└── reports/                       # Generated incident CSV reports
```

Each part of the system is its own small file with one job — this makes
it easy to read, test, and extend (a common real-world practice called
**separation of concerns**).

---

## Setup & Usage

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure AWS credentials
- In the AWS Console, open IAM and create a new user.
- Give it read-only permissions: `AmazonEC2ReadOnlyAccess` and `AmazonS3ReadOnlyAccess`.
- Create an access key for that user.
- Install the AWS CLI and run:

```bash
aws configure
```
Enter your Access Key ID, Secret Access Key, and default region.

Paste the access key, secret key, and your region.

> Safety tip: Never put your access keys in your code or upload them to GitHub. aws configure stores them safely on your own computer.

> Why read-only? The script only looks at resources. It never deletes or changes anything, so it only needs permission to read.

### 3. Set your region (optional)
Edit `AWS_REGION` in `config.py` if you're not using `us-east-1`.

#### Settings you can change (config.py)
AWS_REGION = "us-east-1"   # which AWS region to check
CPU_THRESHOLD = 80         # flag if CPU is above 80%
MEMORY_THRESHOLD = 85      # flag if memory is above 85%
DISK_THRESHOLD = 90        # flag if disk is above 90%

### 4. Run it

```bash
python main.py
```

### Example output
```
Cloud Infrastructure Monitoring & Incident Management System
============================================================
== 1. Local System Health ==
   CPU: 4.2%  |  Memory: 38.1%  |  Disk: 61.5%

== 2. AWS Health Check (EC2 & S3) ==
   EC2 instances found: 3 (running: 1, stopped: 2)
   S3 buckets found: 4

== 3. Unused Resource Detection (Cost Optimization) ==
   Unattached EBS volumes: 1
   Unused Elastic IPs: 1
   Stopped EC2 instances: 2

== 4. Incident Report ==
⚠️  4 incident(s) found:
   HIGH: 0  |  MEDIUM: 1  |  LOW: 3

   [MEDIUM] EBS Volume (vol-0abc123): Unattached volume (20 GB) still incurring cost
   [LOW] Elastic IP (3.90.1.2): Allocated but not attached to any instance
   [LOW] EC2 Instance (i-0def456): Instance is stopped — review if still needed
   [LOW] EC2 Instance (i-0ghi789): Instance is stopped — review if still needed

📄 Full report saved to: reports/incident_log_20260927_101530.csv
```

If AWS credentials aren't configured, the AWS checks are skipped with a
clear message instead of crashing — the local system check still runs.

### What the CSV report looks like

| timestamp | resource_type | resource_id | issue | severity |
|-----------|---------------|-------------|-------|----------|
| 2026-09-27 10:15:30 | EBS Volume | vol-0abc123 | Unattached volume (20 GB) still incurring cost | MEDIUM |
| 2026-09-27 10:15:30 | Elastic IP | 3.90.1.2 | Allocated but not attached to any instance | LOW |


---

## Running the tests

The project includes a `pytest` test suite (14 tests) that checks each
module works correctly — without ever making a real AWS call. Real AWS
responses are "mocked" (faked) so the tests are fast, free, and don't
need credentials to run.

```bash
pip install -r requirements-dev.txt
pytest -v
```

```
tests/test_aws_health_check.py::test_check_ec2_health_counts_running_and_stopped PASSED
tests/test_aws_health_check.py::test_check_ec2_health_handles_missing_credentials PASSED
tests/test_aws_health_check.py::test_check_s3_health_flags_unreachable_buckets PASSED
tests/test_incident_manager.py::test_create_incident_has_all_expected_fields PASSED
tests/test_incident_manager.py::test_save_incidents_returns_none_when_list_is_empty PASSED
tests/test_incident_manager.py::test_save_incidents_writes_a_csv_file PASSED
tests/test_incident_manager.py::test_print_summary_with_no_incidents PASSED
tests/test_incident_manager.py::test_print_summary_with_incidents PASSED
tests/test_system_utils.py::test_get_system_details_returns_expected_keys PASSED
tests/test_system_utils.py::test_get_system_details_calls_psutil_correctly PASSED
tests/test_unused_resource_detector.py::test_find_unattached_ebs_volumes PASSED
tests/test_unused_resource_detector.py::test_find_unused_elastic_ips_only_returns_unattached PASSED
tests/test_unused_resource_detector.py::test_find_stopped_ec2_instances PASSED
tests/test_unused_resource_detector.py::test_find_unattached_ebs_volumes_handles_missing_credentials PASSED

14 passed in 0.31s
```

| Test file | What it checks |
|-----------|----------------|
| `test_system_utils.py` | CPU/memory/disk values are read and returned correctly |
| `test_aws_health_check.py` | Running/stopped servers are counted; unreachable buckets are flagged; missing credentials are handled |
| `test_unused_resource_detector.py` | Unused disks, IPs, and stopped servers are found correctly |
| `test_incident_manager.py` | Incidents are created, saved to CSV, and summarized correctly |

---

## What I learned / skills demonstrated

- Using **boto3** to interact with real AWS services (EC2, S3)
- Setting up **IAM users** with least-privilege access
- Writing **modular, reusable Python functions**
- Basic **error handling** for network/credential failures
- A simple version of **cost optimization** — a task cloud teams do
  regularly to reduce unnecessary AWS spend
- A simple version of **incident tracking/logging**, similar in spirit
  to how support teams document issues
- Writing **unit tests with pytest**, including **mocking** external
  services (AWS) so tests are fast, free, and don't need real credentials

---

## Possible future improvements

- Send alerts automatically via **AWS SNS** or **email** when a HIGH
  severity incident is found
- Add **CloudWatch** metrics instead of/alongside local `psutil` checks
- Check more services (RDS, Lambda, Load balancers) 
- Turn this into a scheduled job (cron / EventBridge) that runs daily

---

- **AWS (Amazon Web Services):** Amazon's cloud. You rent computers, storage, and networking instead of buying them.
- **EC2:** A virtual server (computer) in AWS. It can be *running* or *stopped*.
- **S3:** Storage for files. Files live inside containers called **buckets**.
- **EBS volume:** A virtual hard disk that you attach to an EC2 server.
- **Elastic IP:** A fixed public IP address you reserve in AWS.
- **IAM:** The AWS service that controls *who* can do *what*. I created an IAM user for my script so it does not use my main account.
- **boto3:** The official Python library for talking to AWS from code.
- **psutil:** A Python library that reads CPU, memory, and disk usage of the computer.
- **Incident:** In this project, a problem that was detected and recorded (for example "unattached volume").
- **Severity:** How serious the problem is: HIGH, MEDIUM, or LOW.
- **Pytest:** A tool for writing automatic tests for Python code.
- **Mocking:** Using fake data in tests instead of calling the real service.
