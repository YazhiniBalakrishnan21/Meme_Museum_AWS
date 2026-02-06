# Meme Museum — Deployment Guide

This guide walks you through deploying the full stack using the provided CloudFormation template, validating the deployment, and verifying SNS/CloudWatch.

Prerequisites
- AWS account with permissions to create CloudFormation stacks, EC2, IAM, S3, SNS, DynamoDB, CloudWatch
- EC2 KeyPair in us-east-1
- AWS CLI configured locally (aws configure) OR set GitHub Actions secrets
- (Optional) GitHub repo hosting this project

1) From local (PowerShell)
```powershell
# Edit the default values
.\scripts\deploy_cf.ps1 -KeyName "my-keypair" -AdminEmail "me@example.com" -GitRepo "https://github.com/<you>/<repo>.git" -Region "us-east-1" -AdminCIDR "YOUR_IP/32" -PublicSubnetIds "subnet-aaaa,subnet-bbbb"
```

2) Or using AWS CLI
```bash
aws cloudformation deploy \
  --stack-name MemeMuseumStack \
  --template-file infra/cloudformation/meme_museum_stack.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides KeyName=my-keypair AdminEmail=me@example.com GitRepo=https://github.com/<you>/<repo>.git PublicSubnetIds="subnet-aaa,subnet-bbb" VpcId="vpc-xxxx" AdminCIDR="YOUR_IP/32" \
  --region us-east-1
```

3) Validate the stack & reachability
```bash
# Wait for stack to finish then get outputs
aws cloudformation describe-stacks --stack-name MemeMuseumStack --region us-east-1 --query "Stacks[0].Outputs"
# Use the ALB_DNS output to test
curl http://$(aws cloudformation describe-stacks --stack-name MemeMuseumStack --region us-east-1 --query "Stacks[0].Outputs[?OutputKey=='ALB_DNS'].OutputValue" --output text)/health
# or run the included lightweight validator (checks ALB /health):
python scripts/validate_deployment.py --stack MemeMuseumStack --region us-east-1
# or run the comprehensive lab validator (checks ALB, target health, DynamoDB tables, SNS, CloudWatch):
python scripts/validate_lab.py --stack MemeMuseumStack --region us-east-1 --admin-email you@example.com
```

4) Confirm SNS subscription
- An email will be sent to the `AdminEmail` address; **you must click confirm**. Without confirmation, SNS will not deliver messages to that address.

5) Check CloudWatch logs
- Log Group: `/aws/mememuseum/gunicorn`
- Access via AWS Console or AWS CLI
```bash
aws logs describe-log-groups --log-group-name-prefix /aws/mememuseum --region us-east-1
```

6) Post-deploy items to configure
- SECRET_KEY: a random value is generated during instance startup and stored in `.env`. If you prefer to set your own, SSH to the instance and update `/home/ec2-user/app/.env`.
- Confirm `SNS_TOPIC_ARN` present in CloudFormation outputs.

Notes & recommendations
- Replace the EC2-based deployment with ALB + AutoScaling or ECS/Fargate for production.
- Add ingress restrictions in the security group for SSH (limit your IP).
- Implement HTTPS using an ALB and ACM certificate.

If you want, I can also:
- Add Route53 + ALB + Health Checks to CloudFormation. 
- Convert the stack to Terraform.
- Containerize the app and provide ECS/Fargate deployment.
