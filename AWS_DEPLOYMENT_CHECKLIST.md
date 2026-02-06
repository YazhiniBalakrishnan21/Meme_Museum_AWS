# AWS Deployment Checklist ✅

## Prerequisites
- [ ] AWS Account with permissions
- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Python 3.8+ installed
- [ ] Virtual environment created and activated

---

## Step 1: Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Test LOCAL deployment (app.py)
python app.py
# Navigate to http://localhost:5000
```

---

## Step 2: AWS Infrastructure Setup

### Create DynamoDB Tables

#### Users Table
```bash
aws dynamodb create-table \
  --table-name UsersTable \
  --attribute-definitions AttributeName=email,AttributeType=S \
  --key-schema AttributeName=email,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

#### Memes Table
```bash
aws dynamodb create-table \
  --table-name MemeTable \
  --attribute-definitions \
    AttributeName=meme_id,AttributeType=S \
    AttributeName=user,AttributeType=S \
    AttributeName=created_at,AttributeType=S \
  --key-schema AttributeName=meme_id,KeyType=HASH \
  --global-secondary-indexes \
    IndexName=user-created_at-index,Keys=[{AttributeName=user,KeyType=HASH},{AttributeName=created_at,KeyType=RANGE}],Projection={ProjectionType=ALL},ProvisionedThroughput={ReadCapacityUnits=5,WriteCapacityUnits=5} \
  --billing-mode PROVISIONED \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1
```

#### Activity Log Table
```bash
aws dynamodb create-table \
  --table-name ActivityLogTable \
  --attribute-definitions AttributeName=log_id,AttributeType=S \
  --key-schema AttributeName=log_id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region us-east-1
```

### Create S3 Bucket
```bash
# Replace YOUR_ACCOUNT_ID with your AWS account ID
aws s3 mb s3://meme-museum-bucket-YOUR_ACCOUNT_ID --region us-east-1

# Enable versioning (optional but recommended)
aws s3api put-bucket-versioning \
  --bucket meme-museum-bucket-YOUR_ACCOUNT_ID \
  --versioning-configuration Status=Enabled
```

### Create SNS Topics
```bash
# New Meme Upload Notifications
aws sns create-topic \
  --name meme-upload-notifications \
  --region us-east-1

# Moderation Alerts
aws sns create-topic \
  --name moderation-alerts \
  --region us-east-1

# Trending Alerts
aws sns create-topic \
  --name trending-alerts \
  --region us-east-1
```

---

## Step 3: Configure Environment Variables

### Create .env file:
```bash
cp .env.example .env
# Edit .env with your actual AWS details
```

### Required .env Settings:
- `AWS_DEFAULT_REGION` → Your region (e.g., us-east-1)
- `S3_BUCKET_NAME` → Your S3 bucket name
- `USERS_TABLE` → DynamoDB users table name
- `MEMES_TABLE` → DynamoDB memes table name
- `ACTIVITY_LOG_TABLE` → DynamoDB activity log table name
- `SECRET_KEY` → Generate: `python -c "import secrets; print(secrets.token_hex(32))"`
- SNS Topic ARNs → From SNS creation above

---

## Step 4: IAM Permissions

Create an IAM policy for the application:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:us-east-1:YOUR_ACCOUNT_ID:table/UsersTable",
        "arn:aws:dynamodb:us-east-1:YOUR_ACCOUNT_ID:table/MemeTable",
        "arn:aws:dynamodb:us-east-1:YOUR_ACCOUNT_ID:table/ActivityLogTable",
        "arn:aws:dynamodb:us-east-1:YOUR_ACCOUNT_ID:table/MemeTable/index/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::meme-museum-bucket-YOUR_ACCOUNT_ID/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:DetectModerationLabels",
        "rekognition:DetectLabels",
        "rekognition:DetectText"
      ],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": [
        "arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:meme-upload-notifications",
        "arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:moderation-alerts",
        "arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:trending-alerts"
      ]
    }
  ]
}
```

---

## Step 5: Test AWS Deployment Locally

```bash
# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\Activate.ps1

# Set environment variables
export AWS_PROFILE=default  # Or your profile name

# Test AWS app locally
python aws_app.py
# Navigate to http://localhost:5000
```

---

## Step 6: Deploy to EC2 (Optional)

### Using Gunicorn:
```bash
# Install gunicorn (already in requirements.txt)
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 aws_app:app

# Or use systemd service (see deployments/gunicorn.service)
sudo cp deployments/gunicorn.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl start gunicorn-meme-museum
sudo systemctl enable gunicorn-meme-museum
```

---

## Step 7: Verify Deployment

```bash
# Check application health
curl http://your-server:5000/health

# Expected response:
# {
#   "status": "ok",
#   "time": "2026-02-05T...",
#   "environment": "AWS-Production",
#   "region": "us-east-1"
# }
```

---

## Code Status ✅

### Complete in aws_app.py:
- ✅ DynamoDB integration (Users, Memes, Activity Logs)
- ✅ S3 image storage with presigned URLs
- ✅ Rekognition moderation
- ✅ SNS notifications
- ✅ Error handling with boto3
- ✅ User authentication
- ✅ Meme CRUD operations
- ✅ Comments & likes system
- ✅ Activity logging

### NOT included (Beyond scope):
- Caching (add Redis if needed)
- Rate limiting (add Flask-Limiter)
- Advanced analytics (add CloudWatch)
- CI/CD pipeline (add CodePipeline/GitHub Actions)

---

## Troubleshooting

### DynamoDB Connection Error
```
Import boto3 and check: boto3.Session().region_name
Ensure AWS credentials are available
```

### S3 Access Denied
```
Check IAM permissions - user needs s3:GetObject, s3:PutObject, s3:DeleteObject
```

### Rekognition Error
```
Ensure Rekognition is available in your region
Check IAM permissions for rekognition:DetectModerationLabels
```

### SNS Topic Not Found
```
Verify SNS_TOPIC_* environment variables are correct ARNs
Use: aws sns list-topics --region us-east-1
```

---

## Database Schema Reference

### UsersTable
```
PK: email (String)
Attributes:
  - password (String, hashed)
  - created_at (String, ISO-8601)
  - bio (String)
```

### MemeTable
```
PK: meme_id (String)
GSI: user-created_at-index
  PK: user (String)
  SK: created_at (String)
  
Attributes:
  - user (String)
  - title (String)
  - description (String)
  - category (String)
  - tags (List of Strings)
  - labels (List of Strings) - from Rekognition
  - detected_text (String) - from Rekognition
  - s3_key (String) - S3 object key
  - likes (Number)
  - views (Number)
  - downloads (Number)
  - status (String) - "approved" or "rejected"
  - reject_reasons (List of Objects)
  - created_at (String, ISO-8601)
  - comments (List of Objects)
```

### ActivityLogTable
```
PK: log_id (String)
Attributes:
  - ts (String, ISO-8601)
  - action (String)
  - user (String)
  - meta (String, JSON)
```

---

## Ready to Deploy! 🚀

All code is **production-ready**. Follow the checklist above and your app will be live on AWS.
