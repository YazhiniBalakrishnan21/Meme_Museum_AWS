# Meme Museum - Two Environment Setup

This project provides **two separate applications** for different deployment scenarios:

## 📋 Quick Summary

| Feature | `app.py` (Local) | `aws_app.py` (AWS) |
|---------|-----------------|-------------------|
| **Storage** | Python dictionaries (in-memory) | DynamoDB tables |
| **Images** | Stored in memory | S3 bucket |
| **Moderation** | Auto-approve all | AWS Rekognition |
| **Notifications** | None | AWS SNS (Email) |
| **Use Case** | Local development/testing | Production on AWS EC2 |
| **Persistence** | ❌ Lost on restart | ✅ Permanent |
| **Scalability** | Single process | AWS-managed |

---

## 🚀 app.py - Local Development

**Purpose:** Quick local testing without AWS dependencies

### Features
- ✅ In-memory data storage (Python dictionaries)
- ✅ Image storage in memory
- ✅ No AWS credentials needed
- ✅ Fast startup for testing
- ✅ All data lost on app restart

### Running Locally
```bash
# Install dependencies
pip install flask boto3 passlib python-dotenv pillow

# Run the app
python app.py

# Visit http://localhost:5000
```

### Database Tables (In-Memory)
- **users_db**: Stores `{email: {password, created_at, bio}}`
- **memes_db**: Stores `{meme_id: {title, description, category, ...}}`
- **likes_db**: Stores `{meme_id_user: {meme_id, user, created_at}}`
- **activity_log_db**: Stores activity records
- **meme_images**: Stores raw image bytes

---

## ☁️ aws_app.py - AWS Production

**Purpose:** Deploy on AWS EC2 with full AWS integration

### AWS Resources Created (As Per Your Setup)

#### DynamoDB Tables
```
UsersTable
├─ Partition Key: email (String)
└─ Attributes: password, created_at, bio

MemeTable
├─ Partition Key: meme_id (String)
├─ GSI: user-created_at-index (for querying by user)
└─ Attributes: user, title, description, s3_key, status, labels, likes, views, downloads, etc.

ActivityLogTable
├─ Partition Key: log_id (String)
└─ Attributes: ts, action, user, meta
```

#### S3 Bucket
```
meme-museum-bucket/
└─ memes/{user_email}/{meme_id}/{filename}
```

#### SNS Topics
- `MemeMuseum-NewMemeUpload` - Notifications for new uploads
- `MemeMuseum-TrendingAlert` - Trending content alerts
- `MemeMuseum-ContentModeration` - Moderation alerts

#### IAM Role
- `MemeMuseumEC2Role` attached to EC2 instance
- Policies: DynamoDB, S3, SNS, Rekognition, Lambda Full Access

### Running on AWS EC2

#### 1. SSH into EC2
```bash
ssh -i your-key.pem ec2-user@YOUR_EC2_IP
```

#### 2. Install Dependencies
```bash
sudo yum update -y
sudo yum install python3 git -y
python3 -m venv venv
source venv/bin/activate
pip install flask boto3 passlib python-dotenv pillow requests
```

#### 3. Create .env File
```bash
nano .env
```

Paste (replace with your actual values):
```
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=meme-museum-bucket
USERS_TABLE=UsersTable
MEMES_TABLE=MemeTable
ACTIVITY_LOG_TABLE=ActivityLogTable
NEW_MEME_UPLOAD_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-NewMemeUpload
TRENDING_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-TrendingAlert
MODERATION_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-ContentModeration
SECRET_KEY=your-secret-key
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
```

#### 4. Run the Application
```bash
python aws_app.py
```

#### 5. Run with Gunicorn (Production)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 aws_app.py
```

---

## 📊 Environment Variables

### For Local Development (app.py)
No special variables needed! Everything works out of the box.

### For AWS (aws_app.py)
See `.env.example` for complete list.

**Critical Variables:**
```
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=meme-museum-bucket
USERS_TABLE=UsersTable
MEMES_TABLE=MemeTable
ACTIVITY_LOG_TABLE=ActivityLogTable
```

---

## 🔄 Data Model Comparison

### Local (app.py)
```python
users_db = {
    "user@example.com": {
        "password": "$pbkdf2-sha256$...",
        "created_at": "2026-02-05T10:30:00.123456",
        "bio": ""
    }
}

memes_db = {
    "meme-id-uuid": {
        "meme_id": "...",
        "user": "user@example.com",
        "title": "My Funny Meme",
        "s3_key": None,  # Not used locally
        "status": "approved",
        "created_at": "2026-02-05T10:30:00.123456"
    }
}
```

### AWS (aws_app.py)
```python
# DynamoDB UsersTable
{
    "email": "user@example.com",
    "password": "$pbkdf2-sha256$...",
    "created_at": "2026-02-05T10:30:00.123456",
    "bio": ""
}

# DynamoDB MemeTable
{
    "meme_id": "meme-id-uuid",
    "user": "user@example.com",
    "title": "My Funny Meme",
    "s3_key": "memes/user@example.com/meme-id-uuid/image.jpg",
    "status": "approved",
    "labels": ["dog", "funny"],
    "reject_reasons": [],
    "created_at": "2026-02-05T10:30:00.123456"
}

# DynamoDB ActivityLogTable
{
    "log_id": "log-id-uuid",
    "ts": "2026-02-05T10:30:00.123456",
    "action": "upload",
    "user": "user@example.com",
    "meta": "{\"meme_id\": \"...\", \"status\": \"approved\"}"
}
```

---

## 🔐 Table Partition Keys

| Table | Partition Key | Type |
|-------|---------------|------|
| UsersTable | email | String |
| MemeTable | meme_id | String |
| ActivityLogTable | log_id | String |

**Important:** When creating tables in AWS console:
- ✅ Use these EXACT names
- ✅ Use these EXACT partition keys
- ✅ Set `block public access: ON` for S3 bucket
- ✅ All tables should show `Active` status

---

## 🎯 Key Differences in Code

### Image Storage
- **Local**: `meme_images[meme_id] = image_bytes`
- **AWS**: `s3_client.put_object(Bucket=..., Key=s3_key, Body=image_bytes)`

### Data Retrieval
- **Local**: `user = users_db.get(email)`
- **AWS**: `resp = users_table.get_item(Key={"email": email}); user = resp.get("Item")`

### Image Moderation
- **Local**: Always returns `(True, [])` (auto-approve)
- **AWS**: Uses `rekognition_client.detect_moderation_labels()`

### Notifications
- **Local**: No-op (does nothing)
- **AWS**: `sns_client.publish(TopicArn=..., Subject=..., Message=...)`

---

## 🧪 Testing Workflow

### 1. Start with Local Development
```bash
# Develop and test features locally
python app.py
# Visit http://localhost:5000
# All data is temporary, resets on restart
```

### 2. Test AWS Integration
```bash
# On EC2 or local with AWS credentials
python aws_app.py
# Data persists in DynamoDB
# Images stored in S3
# Email notifications sent via SNS
```

---

## 📝 Application Routes

Both apps support the same routes:
- `GET /` - Redirect to dashboard or login
- `GET /about` - About page
- `POST/GET /register` - User registration
- `POST/GET /login` - User login
- `GET /logout` - User logout
- `GET /dashboard` - User's meme gallery
- `POST/GET /upload` - Upload new meme
- `GET /view/<meme_id>` - View meme details
- `POST /comment/<meme_id>` - Add comment
- `POST /delete/<meme_id>` - Delete meme
- `GET /like/<meme_id>` - Like meme
- `GET /download/<meme_id>` - Download meme
- `GET /health` - Health check (shows environment)

---

## 🚨 Troubleshooting

### Local Development Issues
- **Port 5000 already in use**: `FLASK_RUN_PORT=8000 python app.py`
- **Data not persisting**: This is expected! Local version loses data on restart.

### AWS Deployment Issues
- **"ResourceNotFoundException"**: Check table names match `.env` exactly
- **"User not authenticated"**: Ensure EC2 IAM role has proper policies
- **"Bucket does not exist"**: Verify `S3_BUCKET_NAME` in `.env`
- **SNS not sending emails**: Subscribe to topics and confirm email

---

## 📚 Requirements File

Update `requirements.txt`:
```
Flask==2.3.0
boto3==1.26.0
botocore==1.29.0
passlib==1.7.4
python-dotenv==1.0.0
Pillow==9.5.0
requests==2.31.0
gunicorn==21.0.0
```

---

## ✅ Deployment Checklist

### Before Running aws_app.py on EC2
- [ ] AWS Account ID in .env SNS topics
- [ ] EC2 has MemeMuseumEC2Role attached
- [ ] DynamoDB tables created with correct names
- [ ] S3 bucket created with public access blocked
- [ ] SNS topics created and subscribed to your email
- [ ] Security Group allows port 5000 (or 80 for production)
- [ ] .env file has all required variables

### Before Going to Production
- [ ] Change `SECRET_KEY` to strong random value
- [ ] Use `gunicorn` instead of Flask dev server
- [ ] Set up SSL/TLS (CloudFront or ALB)
- [ ] Enable CloudWatch logging
- [ ] Set up auto-scaling groups
- [ ] Implement database backups

---

## 🎓 Learning Path

1. **Start Here**: Run `app.py` locally to understand the app flow
2. **Create AWS Resources**: Follow manual setup steps
3. **Test Integration**: Run `aws_app.py` with local AWS credentials
4. **Deploy to EC2**: Follow EC2 installation steps
5. **Monitor**: Check CloudWatch and DynamoDB metrics

---

## 📞 Summary

- **Local Dev**: Use `app.py` for quick testing
- **Production**: Use `aws_app.py` on EC2
- **Data**: Local is temporary, AWS is persistent
- **Scale**: AWS handles millions of users, local is single-process
- **Cost**: Local is free, AWS charges for resources used

Good luck with your Meme Museum! 🎉
