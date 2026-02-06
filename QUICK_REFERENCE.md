# 🎬 Meme Museum - Quick Reference Card

## Two Versions at a Glance

```
┌─────────────────────────┬──────────────────────┬────────────────────┐
│        FEATURE          │   app.py (LOCAL)     │  aws_app.py (AWS)  │
├─────────────────────────┼──────────────────────┼────────────────────┤
│ Data Storage            │ Python Dictionaries  │ DynamoDB           │
│ Image Storage           │ Memory               │ S3 Bucket          │
│ Content Moderation      │ Auto-approve         │ Rekognition        │
│ Notifications           │ None                 │ SNS Email           │
│ Persistence             │ ❌ Lost on restart   │ ✅ Permanent       │
│ AWS Account Required    │ ❌ No                │ ✅ Yes             │
│ AWS Credentials Need    │ ❌ No                │ ✅ Yes             │
│ Production Ready        │ ❌ No                │ ✅ Yes             │
│ Scalability             │ Limited (1 process)  │ Unlimited          │
│ Cost                    │ $0                   │ Pay-as-you-go      │
└─────────────────────────┴──────────────────────┴────────────────────┘
```

---

## Starting Points

### Option 1: Quick Local Testing (15 minutes)
```bash
# Just run it
python app.py

# Visit http://localhost:5000
# Test features • All data resets on restart
```

### Option 2: Full AWS Setup (1-2 hours)
```bash
# Step 1: Create AWS resources (manual)
# - S3 bucket: meme-museum-bucket
# - DynamoDB: UsersTable, MemeTable, ActivityLogTable
# - SNS: 3 topics
# - IAM Role: MemeMuseumEC2Role
# - EC2: t2.micro with role attached

# Step 2: Configure
cp .env.example .env
# Edit .env with YOUR AWS account ID and region

# Step 3: Run
python aws_app.py
# Data persists • Email notifications • Production ready
```

---

## Database Tables

### Local (In-Memory)
```python
users_db = {}           # {email: {...}}
memes_db = {}           # {meme_id: {...}}
likes_db = {}           # {like_key: {...}}
activity_log_db = []    # [{...}, ...]
meme_images = {}        # {meme_id: bytes}
```

### AWS (DynamoDB)
```
UsersTable
  🔑 email (Partition Key: String)
  📊 password, created_at, bio

MemeTable
  🔑 meme_id (Partition Key: String)
  📊 user, title, s3_key, status, labels, likes, views, comments
  📑 GSI: user-created_at-index (for user queries)

ActivityLogTable
  🔑 log_id (Partition Key: String)
  📊 ts, action, user, meta
```

---

## Environment Variables

### For aws_app.py (.env file)
```
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=meme-museum-bucket

# DynamoDB Tables
USERS_TABLE=UsersTable
MEMES_TABLE=MemeTable
ACTIVITY_LOG_TABLE=ActivityLogTable

# SNS Topics (replace 123456789012 with YOUR account ID)
NEW_MEME_UPLOAD_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-NewMemeUpload
TRENDING_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-TrendingAlert
MODERATION_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-ContentModeration

# Flask
SECRET_KEY=your-secret-key
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
FLASK_DEBUG=False
```

---

## Running Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run local version (in-memory storage)
python app.py

# Visit http://localhost:5000
# Register • Upload • Like • Comment
# All data resets when you stop the app ⚠️
```

---

## Running on AWS EC2

```bash
# 1. SSH into EC2
ssh -i your-key.pem ec2-user@EC2_IP

# 2. Install Python
sudo yum update -y
sudo yum install python3 git -y

# 3. Setup code
git clone https://github.com/YOU/Meme_Museum.git
cd Meme_Museum
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Create .env (edit with your values)
nano .env
# Paste AWS_DEFAULT_REGION, S3_BUCKET_NAME, table names, SNS topics

# 5. Run
python aws_app.py

# 6. Access
# Open http://EC2_IP:5000 in browser
```

---

## Routes (Both Apps Support)

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Home (redirect) |
| `/about` | GET | About page |
| `/register` | GET/POST | Register new user |
| `/login` | GET/POST | Login |
| `/logout` | GET | Logout |
| `/dashboard` | GET | View your memes |
| `/upload` | GET/POST | Upload meme |
| `/view/<id>` | GET | View meme details |
| `/comment/<id>` | POST | Add comment |
| `/delete/<id>` | POST | Delete meme |
| `/like/<id>` | GET | Like meme |
| `/download/<id>` | GET | Download meme |
| `/health` | GET | Health check |

---

## Code Differences

### Image Storage
```python
# Local (app.py)
meme_images[meme_id] = image_bytes

# AWS (aws_app.py)
s3_client.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=image_bytes)
```

### User Lookup
```python
# Local (app.py)
user = users_db.get(email)

# AWS (aws_app.py)
resp = users_table.get_item(Key={"email": email})
user = resp.get("Item")
```

### Content Moderation
```python
# Local (app.py)
approved, reasons = True, []  # Always approve

# AWS (aws_app.py)
resp = rekognition_client.detect_moderation_labels(
    Image={"Bytes": image_bytes},
    MinConfidence=60.0
)
# Returns actual moderation results
```

### Notifications
```python
# Local (app.py)
# No-op (does nothing)

# AWS (aws_app.py)
sns_client.publish(
    TopicArn=SNS_TOPIC_ARN,
    Subject=subject,
    Message=message
)
```

---

## AWS Account ID Location

Where to find your 12-digit AWS Account ID:

```
1. Open AWS Console: https://console.aws.amazon.com/
2. Click Account dropdown (top right)
3. Click "Account"
4. Copy the "Account ID" number

Example format: 123456789012
```

Use this in .env:
```
NEW_MEME_UPLOAD_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-NewMemeUpload
                                          ↑
                                   Your Account ID
```

---

## Testing Checklist

### Local (app.py)
- [ ] Can register new user
- [ ] Can login with email/password
- [ ] Can upload image
- [ ] Can like meme
- [ ] Can comment on meme
- [ ] Can delete own meme
- [ ] Data resets on app restart

### AWS (aws_app.py)
- [ ] Can register (saved to DynamoDB)
- [ ] Can login (retrieved from DynamoDB)
- [ ] Can upload (image goes to S3)
- [ ] Rekognition labels are detected
- [ ] Email notification received
- [ ] Can like meme (persists in DB)
- [ ] Data survives app restart

---

## Common Errors

### Local (app.py)
```
Error: Address already in use
→ Solution: FLASK_RUN_PORT=8000 python app.py
```

### AWS (aws_app.py)
```
Error: ResourceNotFoundException: Requested resource not found
→ Solution: Check table names in .env match AWS console exactly

Error: User not authenticated
→ Solution: Ensure EC2 has MemeMuseumEC2Role attached

Error: Bucket does not exist
→ Solution: Verify S3_BUCKET_NAME in .env
```

---

## Quick Commands

```bash
# Local Development
python app.py                           # Run locally
python app.py --help                    # Flask help

# AWS Setup
aws configure                           # Setup credentials
aws s3 ls                              # List S3 buckets
aws dynamodb list-tables --region us-east-1  # List tables
aws sns list-topics --region us-east-1 # List SNS topics

# EC2 Operations
ssh -i key.pem ec2-user@IP            # Connect to EC2
python aws_app.py                      # Run on EC2
gunicorn -w 4 -b 0.0.0.0:5000 aws_app:app  # Production

# Debugging
curl http://localhost:5000/health      # Health check
tail -f /var/log/messages              # EC2 system logs
```

---

## Files to Know

```
Meme_Museum/
├── app.py                    # ← Local development (dictionaries)
├── aws_app.py               # ← AWS production (DynamoDB)
├── requirements.txt         # Python dependencies
├── .env.example            # Template for .env
├── SETUP_GUIDE.md          # Comprehensive setup
├── MIGRATION_GUIDE.md      # Migration instructions
├── templates/              # HTML templates (same for both)
├── static/                 # CSS/JS (same for both)
└── infra/                  # Infrastructure files
    └── cloudformation/
        └── meme_museum_stack.yaml
```

---

## Decision Tree

```
Start Here
    ↓
Need to test locally? ──→ python app.py (app.py)
                            ↓
                         Data resets on restart
                         No AWS needed
                         ✓ Quick testing
    ↓
Need production? ──→ Setup AWS resources (manual)
                        ↓
                     Configure .env
                     ↓
                     python aws_app.py (aws_app.py)
                     ↓
                     Data persists
                     Email notifications
                     Scalable
                     ✓ Production ready
```

---

## Support & Next Steps

1. **Read SETUP_GUIDE.md** for detailed explanations
2. **Read MIGRATION_GUIDE.md** for step-by-step migration
3. **Check .env.example** for all available options
4. **Review table schemas** in AWS console
5. **Test locally first**, then migrate to AWS

---

**Last Updated:** February 5, 2026
**Version:** 2.0 (Local + AWS)
**Author:** Your Development Team
