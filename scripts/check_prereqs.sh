#!/usr/bin/env bash
set -e

echo "Checking tools..."
command -v aws >/dev/null || { echo "Missing: aws"; exit 1; }
command -v git >/dev/null || { echo "Missing: git"; exit 1; }
command -v python >/dev/null || { echo "Missing: python"; exit 1; }

echo "Checking Python packages..."
python - <<PY
try:
    import boto3, botocore, passlib, flask
    print('Python packages present')
except Exception as e:
    print('Missing python packages:', e)
    raise SystemExit(1)
PY

echo "Check environment variables (these are recommended):"
for v in AWS_ACCESS_KEY_ID AWS_SECRET_ACCESS_KEY EC2_KEY_NAME ADMIN_EMAIL PUBLIC_SUBNET_IDS VPC_ID ADMIN_CIDR; do
  echo "$v -> ${!v}"
done

echo "Prereq checks complete."