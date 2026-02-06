# Migration Guide: Local → AWS

This guide explains how to transition from local development (`app.py`) to AWS production (`aws_app.py`).

## Phase 1: Local Development (app.py)

### What You Get
- No AWS account needed
- No external dependencies
- Data stored in memory (Python dictionaries)
- Images stored in memory
- Automatic approval for all uploads
- No email notifications

### When to Use
- Learning Flask and the application flow
- Testing UI/UX locally
- Rapid prototyping
- CI/CD testing in pipelines

### Running
```bash
python app.py
# Application runs at http://localhost:5000
```

### Data Persistence
❌ **All data is lost when the app restarts**
- Good for testing: upload an image, test features, restart app, clean slate
- Bad for: keeping user accounts or meme collections

---

## Phase 2: Prepare for AWS

### Prerequisites
1. **AWS Account** with admin access
2. **AWS Credentials** (Access Key + Secret Key)
3. **Local AWS CLI** configured (optional but helpful)

### AWS Configuration
```bash
# Configure AWS credentials locally
aws configure
# You'll be prompted for:
# AWS Access Key ID: [enter yours]
# AWS Secret Access Key: [enter yours]
# Default region: us-east-1
# Default output format: json
```

---

## Phase 3: Create AWS Resources

Follow the original setup instructions:

### Step 1: S3 Bucket
```
Name: meme-museum-bucket
Region: us-east-1
Block public access: ON ✓
```

### Step 2: DynamoDB Tables
```
UsersTable
  - Partition Key: email (String)

MemeTable
  - Partition Key: meme_id (String)
  - GSI: user-created_at-index (for user queries)

ActivityLogTable
  - Partition Key: log_id (String)
```

### Step 3: SNS Topics
```
MemeMuseum-NewMemeUpload
MemeMuseum-TrendingAlert
MemeMuseum-ContentModeration

✓ Subscribe to each with your email
✓ Confirm subscriptions in inbox
```

### Step 4: IAM Role
```
Name: MemeMuseumEC2Role
Policies:
  - AmazonDynamoDBFullAccess
  - AmazonS3FullAccess
  - AmazonSNSFullAccess
  - AmazonRekognitionFullAccess
  - AWSLambdaFullAccess
```

### Step 5: Get Your AWS Account ID
```
AWS Console > Account > Account ID
Copy this 12-digit number: 123456789012
```

---

## Phase 4: Local Testing with AWS (Optional)

Before deploying to EC2, test the AWS app locally:

### 1. Create .env File
```bash
cp .env.example .env
```

### 2. Edit .env
```
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=meme-museum-bucket
USERS_TABLE=UsersTable
MEMES_TABLE=MemeTable
ACTIVITY_LOG_TABLE=ActivityLogTable
NEW_MEME_UPLOAD_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-NewMemeUpload
TRENDING_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-TrendingAlert
MODERATION_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-ContentModeration
SECRET_KEY=dev-secret-key-here
```

### 3. Run AWS App Locally
```bash
python aws_app.py
# Application runs at http://localhost:5000
# Data goes to AWS DynamoDB
# Images upload to AWS S3
# Notifications sent via SNS
```

### 4. Test Full Flow
- Register a new user
- Upload a meme (check S3 bucket)
- Check email for SNS notification
- Like/comment on meme
- Verify data in DynamoDB console

---

## Phase 5: Deploy to EC2

### 1. Launch EC2 Instance
```
OS: Amazon Linux 2
Instance Type: t2.micro (free tier)
Attach Role: MemeMuseumEC2Role
Security Group:
  - SSH (22) from your IP
  - HTTP (80) or Custom TCP 5000 (0.0.0.0/0)
```

### 2. Connect via SSH
```bash
ssh -i your-key.pem ec2-user@YOUR_EC2_IP
```

### 3. Install Python & Git
```bash
sudo yum update -y
sudo yum install python3 git -y
```

### 4. Clone or Upload Code
```bash
# Option A: Clone from GitHub
git clone https://github.com/yourusername/Meme_Museum.git
cd Meme_Museum

# Option B: Upload files via SCP
scp -i your-key.pem -r ./Meme_Museum ec2-user@YOUR_EC2_IP:~/
```

### 5. Set Up Virtual Environment
```bash
cd ~/Meme_Museum
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install flask boto3 passlib python-dotenv pillow requests
```

### 6. Create .env on EC2
```bash
nano .env
```

Paste (with YOUR account ID):
```
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=meme-museum-bucket
USERS_TABLE=UsersTable
MEMES_TABLE=MemeTable
ACTIVITY_LOG_TABLE=ActivityLogTable
NEW_MEME_UPLOAD_SNS_TOPIC=arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-NewMemeUpload
TRENDING_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-TrendingAlert
MODERATION_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-ContentModeration
SECRET_KEY=your-production-secret-key
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
```

Press Ctrl+X, then Y, then Enter to save.

### 7. Run Application
```bash
python aws_app.py
```

You should see:
```
==============================================================
MEME MUSEUM - AWS PRODUCTION DEPLOYMENT
==============================================================
Running on http://0.0.0.0:5000
Region: us-east-1
DynamoDB Tables: UsersTable, MemeTable, ActivityLogTable
S3 Bucket: meme-museum-bucket
==============================================================
```

### 8. Access Application
Open browser and go to:
```
http://YOUR_EC2_IP:5000
```

---

## Phase 6: Production Hardening

### Option A: Use Gunicorn (Recommended)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 aws_app.py
```

### Option B: Set Up Systemd Service
Create `/etc/systemd/system/meme-museum.service`:
```ini
[Unit]
Description=Meme Museum Flask Application
After=network.target

[Service]
User=ec2-user
WorkingDirectory=/home/ec2-user/Meme_Museum
ExecStart=/home/ec2-user/Meme_Museum/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 aws_app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable meme-museum
sudo systemctl start meme-museum
```

### Option C: Use Nginx as Reverse Proxy
```bash
sudo yum install nginx -y
sudo systemctl start nginx
```

Create `/etc/nginx/conf.d/meme-museum.conf`:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

Then:
```bash
sudo systemctl reload nginx
```

---

## Comparison: Before & After

### Before (app.py - Local)
```
Browser → Flask (localhost:5000) → Python Dict → Memory
         (all data lost on restart)
```

### After (aws_app.py - EC2)
```
Browser → Nginx (port 80) → Gunicorn → Flask (port 5000)
         ↓
    AWS Services:
    - DynamoDB (users, memes, logs)
    - S3 (image storage)
    - Rekognition (content moderation)
    - SNS (email notifications)
```

---

## Data Migration (if needed)

If you want to migrate data from local to AWS:

### Export Local Data
```python
# Add to app.py temporarily
import json

@app.route('/export')
def export_data():
    return jsonify({
        'users': users_db,
        'memes': memes_db,
        'likes': likes_db,
        'activity_log': activity_log_db
    })

# Visit http://localhost:5000/export
# Save JSON to file
```

### Import to AWS
```python
# Manual DynamoDB import using AWS CLI or SDK
import boto3
import json

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
users_table = dynamodb.Table('UsersTable')

with open('exported_users.json') as f:
    for user in json.load(f):
        users_table.put_item(Item=user)
```

---

## Troubleshooting Checklist

### Local Development (app.py)
- [ ] Python 3.8+ installed
- [ ] All packages installed (`pip install -r requirements.txt`)
- [ ] Port 5000 is free
- [ ] Flask app starts without errors

### AWS Integration (aws_app.py)
- [ ] AWS credentials configured (`aws configure`)
- [ ] `.env` file exists and populated
- [ ] All table names match `.env` exactly
- [ ] S3 bucket exists and is accessible
- [ ] EC2 role has correct policies attached

### EC2 Deployment
- [ ] SSH connection works
- [ ] Python 3 and pip installed
- [ ] Virtual environment created
- [ ] All dependencies installed
- [ ] .env file on EC2 has correct values
- [ ] Security group allows port 5000
- [ ] IAM role gives EC2 access to AWS services

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `python app.py` | Run locally with in-memory storage |
| `python aws_app.py` | Run with AWS DynamoDB (requires .env) |
| `aws configure` | Set up AWS credentials |
| `aws s3 ls` | List S3 buckets |
| `aws dynamodb list-tables` | List DynamoDB tables |
| `gunicorn -w 4 -b 0.0.0.0:5000 aws_app:app` | Production server |

---

## Support

- Check `.env.example` for required variables
- Review `SETUP_GUIDE.md` for detailed explanations
- Look at CloudWatch logs if AWS services fail
- Test locally first before deploying to EC2

Good luck! 🚀
