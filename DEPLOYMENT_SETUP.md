# Deployment Setup - Two Separate Environments

## File Structure

You have **two separate deployment files** for different environments:

### 1. **app.py** - Local Development
- **Location**: Root directory
- **Storage**: Python in-memory dictionaries
- **Data Structure**:
  - `users_db{}` - User accounts (email, password, bio)
  - `memes_db{}` - Meme records (title, description, images in memory)
  - `likes_db{}` - Like tracking
  - `activity_log_db[]` - Activity logging (list)
  - `meme_images{}` - Image binary storage
- **No AWS Dependencies**: No boto3, no AWS credentials needed
- **Quick Local Testing**: Run directly with `python app.py`
- **Port**: 5000 (default)

**Key Features:**
- ✅ Simple in-memory storage (loses data on restart)
- ✅ No external dependencies
- ✅ Fast local development
- ✅ Mock moderation/labeling

---

### 2. **aws_app.py** - AWS Production Deployment
- **Location**: Root directory  
- **Storage**: Full AWS services
  - **DynamoDB**: Users, Memes, Activity Logs
  - **S3**: Image storage with presigned URLs
  - **Rekognition**: AI image moderation & label detection
  - **SNS**: Email/notification alerts
- **Environment Variables Required**:
  - `AWS_DEFAULT_REGION` (default: us-east-1)
  - `S3_BUCKET_NAME` (required)
  - `USERS_TABLE` (default: UsersTable)
  - `MEMES_TABLE` (default: MemeTable)
  - `ACTIVITY_LOG_TABLE` (default: ActivityLogTable)
  - `SECRET_KEY` (required in production)
  - `NEW_MEME_UPLOAD_SNS_TOPIC`
  - `MODERATION_ALERT_SNS_TOPIC`
  - `TRENDING_ALERT_SNS_TOPIC`

**Key Features:**
- ✅ Persistent DynamoDB storage
- ✅ S3 image hosting with presigned URLs
- ✅ Real AI-powered content moderation
- ✅ SNS notifications
- ✅ Production-ready with error handling
- ✅ Query indexes for user-based searches

---

## How to Switch Between Deployments

### Run Local Development:
```bash
python app.py
```
- No AWS setup needed
- Data stored in memory
- Resets on restart

### Run AWS Production:
```bash
python aws_app.py
```
- Requires AWS credentials (via `~/.aws/credentials` or environment)
- Requires `.env` file with AWS configuration
- Data persists in DynamoDB
- Real Rekognition moderation
- Real S3 storage

---

## Quick Comparison

| Feature | app.py (Local) | aws_app.py (AWS) |
|---------|---|---|
| **User Storage** | Python dict | DynamoDB |
| **Meme Storage** | Python dict | DynamoDB |
| **Images** | Memory | S3 |
| **Activity Logs** | List | DynamoDB |
| **Moderation** | Mock (always approve) | Rekognition |
| **Labels/Text** | None | Rekognition |
| **Notifications** | None | SNS |
| **Persistence** | No (in-memory) | Yes (DynamoDB) |
| **Setup Complexity** | None | AWS credentials + resources |
| **Cost** | Free | AWS billing applies |

---

## Running Both Simultaneously

You **cannot run both on port 5000** at the same time. To run both locally:

```bash
# Terminal 1 - Local development
python app.py

# Terminal 2 - AWS app locally (for testing)
FLASK_RUN_PORT=5001 python aws_app.py
```

Add to `.env` for AWS app:
```
FLASK_RUN_PORT=5001
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
SECRET_KEY=your-secret-key
```

---

## Next Steps

✅ **Local Development Ready**: Start with `python app.py`
✅ **AWS Production Ready**: Configure `.env` and run `python aws_app.py`
✅ **Both Files Separate**: No conflicts - clean architecture

