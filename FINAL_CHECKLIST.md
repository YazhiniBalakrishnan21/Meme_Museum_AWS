# Final Deployment Checklist (what *you* must do in AWS) ✅

1. Prepare account values
   - EC2 KeyPair name (KeyName)
   - VPC ID and Public Subnet IDs (PublicSubnetIds)
   - Admin IP / CIDR (AdminCIDR) for SSH access
   - Admin email (AdminEmail) to receive SNS subscription confirmation

2. Set AWS CLI or GitHub secrets
   - AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
   - Optionally set stack parameters in GitHub Actions secrets if you want CI-driven deploy

3. Deploy the CloudFormation stack
   - Locally: run `.\	ests\deploy_cf.ps1` or the AWS CLI command shown in `DEPLOY.md`

4. Confirm SNS subscription
   - Open your admin email inbox and click the confirmation sent by SNS

5. Run validation
   - `python scripts/validate_lab.py --stack MemeMuseumStack --region us-east-1 --admin-email you@example.com`

6. Manual tests
   - Open the ALB DNS in browser and test register/login/upload flow, and verify DynamoDB and CloudWatch entries

7. Capture evidence for the lab (optional)
   - ALB DNS, CloudFormation stack name, screenshots of site and CloudWatch logs, and the `validate_lab.py` output

If anything fails, collect CloudFormation events and CloudWatch logs and re-run the validation script. If you want, paste the outputs here and I will help interpret them.