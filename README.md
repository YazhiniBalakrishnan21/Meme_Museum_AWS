# Meme Museum

A cloud-deployable meme management platform using AWS (S3, Rekognition, DynamoDB, Lambda optional).

## Features
- Secure user registration & login (PBKDF2-SHA256)
- Meme upload with automatic moderation via AWS Rekognition
- Metadata storage in DynamoDB and media storage in S3
- Presigned URLs for secure access
- Like/view/download counters and basic activity logging

---

## AWS Preparation
1. Use the included CloudFormation template to provision the stack (S3, DynamoDB tables, SNS topic + subscription, ALB + Auto Scaling Group with IAM role):
   - `aws cloudformation deploy --stack-name MemeMuseumStack --template-file infra/cloudformation/meme_museum_stack.yaml --capabilities CAPABILITY_NAMED_IAM --parameter-overrides KeyName=<YourKeyPair> AdminEmail=<your-email@example.com> PublicSubnetIds="subnet-aaa,subnet-bbb" AdminCIDR="<your-ip>/32"`
   - Note: you must confirm the SNS subscription by clicking the confirmation email sent to `AdminEmail`. Make sure to provide two or more public subnet IDs in `PublicSubnetIds` and set `AdminCIDR` to your IP range for SSH access.
2. If you prefer not to use CloudFormation, create an S3 bucket and the DynamoDB tables manually: `MemeUsers` (PK: `email`), `MemeItems` (PK: `meme_id`, GSI `by_user` on `user`), `MemeLikes` (PK: `meme_id`, SK: `user`), and `MemeLogs` (PK: `id`).
3. Provision an IAM role/user with permissions: s3:PutObject, s3:GetObject, rekognition:DetectLabels, rekognition:DetectModerationLabels, rekognition:DetectText, dynamodb:PutItem/GetItem/UpdateItem/Query/Scan, sns:Publish.

Tip: A convenience script is provided at `scripts/create_resources.py` to bootstrap the DynamoDB tables (run with AWS credentials or on EC2 with an IAM role).
4. Set environment variables on your EC2/host (the CloudFormation template writes a `.env` during UserData):
   - `AWS_REGION`
   - `S3_BUCKET`
   - `DYNAMO_USERS_TABLE` (default `MemeUsers`)
   - `DYNAMO_MEMES_TABLE` (default `MemeItems`)
   - `DYNAMO_LIKES_TABLE` (default `MemeLikes`)
   - `DYNAMO_LOGS_TABLE` (default `MemeLogs`)
   - `SECRET_KEY` (set a strong secret for Flask sessions)
   - `SNS_TOPIC_ARN` (provided by CloudFormation outputs)

**Tip:** The CloudFormation template includes an EC2 instance which clones your GitHub repo — update the `git clone` URL in the template's `UserData` before deployment to point to your repository.

## Local Setup
1. python -m venv venv && venv\Scripts\activate
2. pip install -r requirements.txt
3. Create a `.env` file for local development with the variables above (or set env vars in your shell).
4. Run `python app.py` to start the dev server.

## Deployment Tips
- Run on EC2 with an IAM role attached for secure credentials instead of environment-based AWS keys.
- Use a process manager (systemd) or containerize with Docker for production. This repo includes a `deployments/gunicorn.service` file that the CloudFormation `UserData` copies to the instance and systemd starts.
- CloudWatch: the CloudFormation template now creates a CloudWatch Log Group `/aws/mememuseum/gunicorn` and the EC2 instance installs the Amazon CloudWatch Agent to push `access.log` and `error.log` from `/var/log/gunicorn/`.

## Validation & CI
- The GitHub Actions workflow will deploy the CloudFormation stack when you push to `main`. Set the following repository secrets before pushing:
  - `AWS_ACCESS_KEY_ID`
  - `AWS_SECRET_ACCESS_KEY`
  - `EC2_KEY_NAME` (your EC2 KeyPair name)
  - `ADMIN_EMAIL` (for SNS subscription)
  - `PUBLIC_SUBNET_IDS` (comma-separated public subnet IDs for ALB / ASG)
  - `VPC_ID` (the VPC id where subnets exist)
  - `ADMIN_CIDR` (CIDR allowed to SSH to instances)
- The workflow passes the repository URL to the CloudFormation `GitRepo` parameter, so the instance will clone the repository automatically.

## VS Code Quick Actions
- Open the Command Palette (Ctrl+Shift+P) and run `Tasks: Run Task` → **Start App (Local)** to start the app locally for development.
- Run `Tasks: Run Task` → **Check Prereqs (PowerShell)** to confirm your machine is ready.
- Run `Tasks: Run Task` → **Deploy to AWS (PowerShell)** to run the deployment script (edit the parameters in the task or run in the terminal with your values).
- Use **Run and Debug** (F5) to launch the app with the provided debug configuration (`.vscode/launch.json`).

## Notes
- This refactor focuses on AWS integration; further hardening (rate limiting, CSRF, input sanitization) is recommended before public launch.
- After deployment, confirm your SNS subscription (open the email sent to `ADMIN_EMAIL` and click confirm), then check CloudWatch Log Group `/aws/mememuseum/gunicorn` for app logs and the validation scripts (`scripts/validate_deployment.py` for simple ALB /health checks and the more comprehensive `scripts/validate_lab.py` for ALB, target health, DynamoDB, SNS, and CloudWatch verification).
