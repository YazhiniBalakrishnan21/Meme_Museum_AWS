# Architecture Diagrams - Meme Museum

## Overview: Two Deployment Models

```
┌─────────────────────────────────────────────────────────────────────┐
│                      MEME MUSEUM ARCHITECTURE                        │
└─────────────────────────────────────────────────────────────────────┘

                              LOCAL vs AWS
                              
    app.py (Local)              vs             aws_app.py (AWS)
    ──────────────                             ──────────────
    
    • Python                                   • Python + AWS
    • In-Memory                                • DynamoDB
    • No Persistence                           • S3 Storage
    • Auto-approve images                      • Rekognition
    • No notifications                         • SNS Email
```

---

## LOCAL DEVELOPMENT ARCHITECTURE (app.py)

```
┌─────────────────────────────────────────────────────────────┐
│                   LOCAL DEVELOPMENT STACK                    │
└─────────────────────────────────────────────────────────────┘

                        Browser (localhost:5000)
                               ↓
                    ┌──────────────────────┐
                    │   Flask Application   │
                    │   (app.py - local)    │
                    └──────────────────────┘
                               ↓
            ┌──────────────────┴──────────────────┐
            ↓                                     ↓
      ┌──────────────┐              ┌─────────────────────┐
      │ In-Memory DB │              │  Image Storage      │
      ├──────────────┤              ├─────────────────────┤
      │ users_db     │              │ meme_images (RAM)   │
      │ memes_db     │              └─────────────────────┘
      │ likes_db     │
      │ activity_log │
      └──────────────┘

┌─────────────────────────────────────────────────────────────┐
│ Data Flow (app.py):                                         │
│ 1. User registers → Stored in users_db dictionary          │
│ 2. User uploads image → Stored in meme_images dictionary   │
│ 3. Auto-approve all images (no Rekognition)                │
│ 4. Like/comment → Update memes_db                          │
│ 5. App restarts → ALL DATA LOST ⚠️                          │
└─────────────────────────────────────────────────────────────┘
```

---

## AWS PRODUCTION ARCHITECTURE (aws_app.py)

```
┌─────────────────────────────────────────────────────────────┐
│                   AWS PRODUCTION STACK                       │
└─────────────────────────────────────────────────────────────┘

┌────────────────────────┐
│   Internet Browser     │
│  (http://EC2_IP:5000)  │
└───────────┬────────────┘
            │
    ┌───────▼────────┐
    │  AWS Route 53  │   (Optional: Domain DNS)
    └───────┬────────┘
            │
    ┌───────▼────────────────┐
    │   AWS Security Group    │
    │  (Allow SSH, HTTP/5000) │
    └───────┬────────────────┘
            │
┌───────────▼──────────────────────────────────────────────┐
│                   EC2 Instance (t2.micro)                 │
├──────────────────────────────────────────────────────────┤
│                                                            │
│  ┌─────────────────────────────────────────┐              │
│  │   Flask Application (aws_app.py)        │              │
│  │   Gunicorn/WSGI Server                  │              │
│  └────────────┬────────────────────────────┘              │
│               │                                            │
│   ┌───────────┼───────────┬────────────────┐              │
│   ↓           ↓           ↓                ↓              │
│ ┌─────┐   ┌──────┐   ┌──────┐   ┌──────────┐             │
│ │ S3  │   │ DDB  │   │ SNS  │   │ Rekog.   │             │
│ │ API │   │ API  │   │ API  │   │ API      │             │
│ └──┬──┘   └──┬───┘   └──┬───┘   └──┬───────┘             │
│    │        │          │           │                      │
│  EC2 IAM Role (MemeMuseumEC2Role)                         │
│    └────────┴──────────┴───────────┘                      │
│                                                            │
└────────────────────────────────────────────────────────────┘
            │                  │              │
            ↓                  ↓              ↓
    ┌──────────────┐  ┌─────────────┐  ┌──────────────┐
    │   S3 Bucket  │  │  DynamoDB   │  │ SNS Topics   │
    ├──────────────┤  │             │  ├──────────────┤
    │ memes/       │  │ UsersTable  │  │ NewUpload    │
    │ {user}/      │  │ MemeTable   │  │ Trending     │
    │ {meme_id}/   │  │ LogTable    │  │ Moderation   │
    │ image.jpg    │  └─────────────┘  └──────────────┘
    └──────────────┘        ↓                  ↓
         (Storage)    (Persistence)      (Notifications)
```

---

## Data Flow - Local (app.py)

```
USER REGISTRATION:
─────────────────

1. Browser
   ↓
POST /register (email, password)
   ↓
app.py
   ├─ Validate email format ✓
   ├─ Check duplicate in users_db ✓
   ├─ Hash password (PBKDF2) ✓
   └─ Store in users_db[email] ✓
      ↓
   Redirect to /login
   ↓
Browser


USER UPLOAD:
───────────

1. Browser
   ↓
POST /upload (image, title, description)
   ↓
app.py
   ├─ Generate meme_id ✓
   ├─ Read image bytes ✓
   ├─ Moderate image (auto-approve) ✓
   ├─ Detect labels/text (empty) ✓
   ├─ Store in meme_images[meme_id] ✓
   └─ Store metadata in memes_db[meme_id] ✓
      ↓
   Redirect to /dashboard
   ↓
Browser
   ↓
GET /view/<meme_id>
   ├─ Retrieve from memes_db ✓
   └─ Display meme ✓
      ↓
Browser


DATA PERSISTENCE:
────────────────

❌ All data in memory
❌ Lost on app restart
✓ Fast access
✓ Perfect for testing
```

---

## Data Flow - AWS (aws_app.py)

```
USER REGISTRATION:
─────────────────

1. Browser (EC2 IP:5000)
   ↓
POST /register (email, password)
   ↓
aws_app.py (on EC2)
   ├─ Validate email format ✓
   ├─ Query UsersTable (email) → DynamoDB ✓
   ├─ Hash password (PBKDF2) ✓
   └─ put_item → UsersTable ✓
      ↓
   Publish to SNS
   ├─ Topic: NewMemeUpload
   └─ Email sent ✓
      ↓
   Redirect to /login
   ↓
Browser


USER UPLOAD:
───────────

1. Browser
   ↓
POST /upload (image, title, description, tags, category)
   ↓
aws_app.py (on EC2)
   ├─ Generate meme_id ✓
   ├─ Read image bytes ✓
   ├─ Rekognition.detect_moderation_labels() → approve/reject ✓
   ├─ Rekognition.detect_labels() → get labels ✓
   ├─ Rekognition.detect_text() → extract text ✓
   ├─ S3.put_object() → Store image ✓
   │  └─ S3: memes/{user}/{meme_id}/image.jpg
   ├─ DynamoDB.put_item() → Store metadata ✓
   │  └─ MemeTable: meme_id, user, title, s3_key, status, labels...
   └─ Log activity → ActivityLogTable ✓
      ↓
   Publish to SNS
   ├─ If approved: NewMemeUpload topic → Email sent ✓
   └─ If rejected: Moderation topic → Email sent ✓
      ↓
   Redirect to /dashboard
   ↓
Browser
   ↓
GET /dashboard
   ├─ Query MemeTable (user-created_at-index)
   ├─ Get all memes by current user
   ├─ Generate presigned URLs for each → S3 ✓
   └─ Display meme gallery ✓
      ↓
GET /view/<meme_id>
   ├─ Get meme from MemeTable → DynamoDB ✓
   ├─ Update views counter → DynamoDB ✓
   ├─ Generate presigned URL → S3 ✓
   │  └─ URL valid for 1 hour (PRESIGNED_EXPIRATION)
   └─ Display meme + comments ✓
      ↓
Browser


DATA PERSISTENCE:
─────────────────

✓ All data in DynamoDB (survives restarts)
✓ All images in S3 (permanent storage)
✓ All activity logs in ActivityLogTable
✓ Email notifications via SNS
✓ Production ready
```

---

## Database Schema Comparison

```
┌─────────────────────────────────────────────────────────┐
│           LOCAL (app.py) vs AWS (aws_app.py)            │
└─────────────────────────────────────────────────────────┘

USERS STORAGE:
──────────────

Local (app.py):
users_db = {
    "john@example.com": {
        "password": "$pbkdf2-sha256$...",
        "created_at": "2026-02-05T10:00:00.000000",
        "bio": "My bio"
    }
}
✓ Dictionary access: users_db.get(email)
✓ In memory
✗ Lost on restart


AWS (aws_app.py):
DynamoDB → UsersTable
{
    "email": "john@example.com" [Partition Key]
    "password": "$pbkdf2-sha256$...",
    "created_at": "2026-02-05T10:00:00.000000",
    "bio": "My bio"
}
✓ Query: users_table.get_item(Key={"email": email})
✓ Persistent
✓ Backup available


MEMES STORAGE:
──────────────

Local (app.py):
memes_db = {
    "meme-uuid": {
        "meme_id": "meme-uuid",
        "user": "john@example.com",
        "title": "Funny cat",
        "s3_key": None,  [unused]
        "labels": [],
        "likes": 5,
        "views": 100,
        "comments": [...]
    }
}
meme_images = {
    "meme-uuid": b'\x89PNG...'  [Raw bytes in memory]
}
✓ Quick access
✗ All images in RAM
✗ Lost on restart


AWS (aws_app.py):
DynamoDB → MemeTable
{
    "meme_id": "meme-uuid" [Partition Key]
    "user": "john@example.com" [GSI Key]
    "created_at": "2026-02-05T10:00:00" [GSI Sort Key]
    "title": "Funny cat",
    "s3_key": "memes/john@example.com/meme-uuid/image.jpg",
    "labels": ["cat", "funny"],
    "detected_text": "LOL",
    "likes": 5,
    "views": 100,
    "comments": [{"user": "jane@...", "text": "Hilarious!"}],
    "status": "approved",
    "reject_reasons": []
}

S3 Storage:
└─ memes/john@example.com/meme-uuid/image.jpg [Binary data]

✓ Metadata in DynamoDB
✓ Images in S3
✓ GSI for user queries
✓ Permanent storage
✓ Scalable
```

---

## AWS IAM Role Permissions

```
MemeMuseumEC2Role (Attached to EC2 Instance)
├─ AmazonDynamoDBFullAccess
│  └─ Allows: read/write to DynamoDB tables
│     ├─ dynamodb:GetItem
│     ├─ dynamodb:PutItem
│     ├─ dynamodb:UpdateItem
│     ├─ dynamodb:DeleteItem
│     ├─ dynamodb:Query
│     └─ dynamodb:Scan
│
├─ AmazonS3FullAccess
│  └─ Allows: read/write to S3 buckets
│     ├─ s3:GetObject
│     ├─ s3:PutObject
│     ├─ s3:DeleteObject
│     └─ s3:GeneratePresignedUrl
│
├─ AmazonSNSFullAccess
│  └─ Allows: publish to SNS topics
│     ├─ sns:Publish
│     └─ sns:GetTopicAttributes
│
├─ AmazonRekognitionFullAccess
│  └─ Allows: content moderation
│     ├─ rekognition:DetectModerationLabels
│     ├─ rekognition:DetectLabels
│     └─ rekognition:DetectText
│
└─ AWSLambdaFullAccess
   └─ Allows: Lambda invocation (for future)
```

---

## Request/Response Flow

```
BROWSER REQUEST:
────────────────

1. Browser (localhost:5000 or EC2_IP:5000)
2. HTTP Request (GET/POST)
3. Flask Route Handler (@app.route)
4. Business Logic
   │
   ├─ Local (app.py)
   │  └─ Python Dictionary Operations
   │
   └─ AWS (aws_app.py)
      └─ AWS API Calls (boto3)
5. Response (HTML/JSON/Redirect)
6. Browser Renders


EXAMPLE: GET /dashboard
─────────────────────

Browser
  │
  ├─ Request: GET /dashboard
  │
  ↓
Flask Route Handler
  │
  ├─ Check session["user"] ✓
  │
  ├─ Get user's memes
  │  │
  │  ├─ Local: [m for m in memes_db.values() if m["user"] == user]
  │  │
  │  └─ AWS: memes_table.query(user=session["user"])
  │
  ├─ For each meme (local) - no URL needed (data in memory)
  ├─ For each meme (AWS) - generate presigned URL for S3
  │
  ├─ Render template with memes
  │
  ↓
Browser
  │
  ├─ Displays meme gallery
  └─ Shows images (local: from memory, AWS: from S3)
```

---

## SNS Topic Architecture (AWS Only)

```
SNS TOPICS:
───────────

┌──────────────────────────────────────────────────────┐
│  MemeMuseum-NewMemeUpload                            │
├──────────────────────────────────────────────────────┤
│  Triggered When:                                     │
│  • User registers                                    │
│  • Meme approved                                     │
│                                                      │
│  Subscribers:                                        │
│  • your-email@example.com ✓                          │
│                                                      │
│  SNS → Send Email                                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  MemeMuseum-TrendingAlert                            │
├──────────────────────────────────────────────────────┤
│  Triggered When:                                     │
│  • Meme gets X likes                                 │
│  • Meme gets X views                                 │
│                                                      │
│  Subscribers:                                        │
│  • your-email@example.com ✓                          │
│                                                      │
│  SNS → Send Email                                   │
└──────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────┐
│  MemeMuseum-ContentModeration                        │
├──────────────────────────────────────────────────────┤
│  Triggered When:                                     │
│  • Meme rejected (explicit, violence, etc.)          │
│                                                      │
│  Subscribers:                                        │
│  • your-email@example.com ✓                          │
│                                                      │
│  SNS → Send Email                                   │
└──────────────────────────────────────────────────────┘

EMAIL FLOW:
───────────

AWS SNS Topic
  │
  ├─ Publish(message)
  │
  ├─ SNS Service
  │
  ├─ Look up subscribers
  │
  ├─ Send to email
  │
  ├─ Email provider (AWS SES)
  │
  ├─ Internet
  │
  └─ your-email@example.com ✓
```

---

## Deployment Timeline

```
PHASE 1: LOCAL DEVELOPMENT (15 mins)
────────────────────────────────

1. Install Python packages
   └─ pip install -r requirements.txt

2. Run locally
   └─ python app.py

3. Test features
   └─ Register, upload, like, comment

PHASE 2: AWS SETUP (1-2 hours)
──────────────────────────────

1. Create S3 bucket
2. Create DynamoDB tables
3. Create SNS topics
4. Create IAM role
5. Launch EC2 instance

PHASE 3: EC2 DEPLOYMENT (30 mins)
─────────────────────────────────

1. SSH into EC2
2. Install Python
3. Clone/upload code
4. Set up virtual environment
5. Create .env file
6. Run aws_app.py

PHASE 4: PRODUCTION (optional)
──────────────────────────────

1. Install Gunicorn
2. Set up systemd service
3. Configure Nginx
4. Enable auto-scaling
5. Set up monitoring


TOTAL TIME: ~2-3 hours for full production deployment
```

---

## Monitoring & Scaling (AWS Only)

```
CLOUDWATCH MONITORING:
──────────────────────

EC2 Instance
  ├─ CPU Usage
  ├─ Memory Usage
  ├─ Network In/Out
  └─ Disk I/O

DynamoDB
  ├─ Read Capacity
  ├─ Write Capacity
  ├─ Item Count
  └─ Throttled Requests

S3
  ├─ Bucket Size
  ├─ Request Count
  └─ Data Transfer

SNS
  ├─ Messages Published
  ├─ Messages Delivered
  └─ Message Failures

SCALING:
────────

DynamoDB → Auto-scale writes/reads
S3 → Unlimited storage
SNS → Unlimited topics
EC2 → Add more instances (via Auto Scaling Group)
```

---

**Last Updated:** February 5, 2026
**Version:** 1.0
**Status:** Complete ✓
