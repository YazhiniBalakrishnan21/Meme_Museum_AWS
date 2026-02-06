# AWS Setup Instructions - Step by Step

Follow these instructions **in order** to set up all AWS resources for Meme Museum.

## Prerequisites
- AWS Account (free tier eligible)
- Email address for SNS subscriptions
- AWS region: **us-east-1** (N. Virginia)

---

## STEP 1: Create S3 Bucket

### Where to Start
1. Go to **AWS Console** → search **"S3"** → click **S3**
2. Click **"Create bucket"** button

### Configuration
| Field | Value |
|-------|-------|
| **Bucket name** | `meme-museum-bucket` |
| **Region** | `us-east-1` (N. Virginia) |
| **Block Public Access** | ✅ ON (all settings checked) |

### Steps
1. Enter bucket name: `meme-museum-bucket`
2. Select region: `us-east-1`
3. Scroll down → **"Block Public Access settings"**
4. ✅ Check: Block all public access
5. Click **"Create bucket"**
6. **Status**: Should show in bucket list

---

## STEP 2: Create DynamoDB Tables

### Go to DynamoDB
1. AWS Console → search **"DynamoDB"** → click **DynamoDB**
2. Click **"Create table"** button

### Table 1: UsersTable

| Field | Value |
|-------|-------|
| Table name | `UsersTable` |
| Partition key | `email` (String) |

**Steps:**
1. Enter table name: `UsersTable`
2. Partition key: `email` (type: String)
3. Click **"Create"**
4. Wait until status = **"Active"** ✅

### Table 2: MemeTable

| Field | Value |
|-------|-------|
| Table name | `MemeTable` |
| Partition key | `meme_id` (String) |

**Steps:**
1. Click **"Create table"** again
2. Enter table name: `MemeTable`
3. Partition key: `meme_id` (type: String)
4. Click **"Create"**
5. Wait until status = **"Active"** ✅

**Note:** For GSI (Global Secondary Index) to query by user:
- Table: MemeTable
- Edit table settings
- Add GSI with partition key `user` and sort key `created_at`

### Table 3: ActivityLogTable

| Field | Value |
|-------|-------|
| Table name | `ActivityLogTable` |
| Partition key | `log_id` (String) |

**Steps:**
1. Click **"Create table"** again
2. Enter table name: `ActivityLogTable`
3. Partition key: `log_id` (type: String)
4. Click **"Create"**
5. Wait until status = **"Active"** ✅

### Verify All Tables
```
✅ UsersTable - Active
✅ MemeTable - Active
✅ ActivityLogTable - Active
```

---

## STEP 3: Create SNS Topics & Subscriptions

### Go to SNS
1. AWS Console → search **"SNS"** → click **SNS**
2. Click **"Topics"** (left sidebar)
3. Click **"Create topic"** button

### Topic 1: MemeMuseum-NewMemeUpload

**Create Topic:**
1. Name: `MemeMuseum-NewMemeUpload`
2. Type: **Standard**
3. Click **"Create topic"**

**Subscribe to Topic:**
1. Click topic name
2. Click **"Create subscription"** button
3. Protocol: **Email**
4. Endpoint: `your-email@example.com`
5. Click **"Create subscription"**
6. **Go to your email inbox**
7. Find AWS SNS confirmation email
8. Click **"Confirm subscription"** link

### Topic 2: MemeMuseum-TrendingAlert

**Create Topic:**
1. Click **"Create topic"** button
2. Name: `MemeMuseum-TrendingAlert`
3. Type: **Standard**
4. Click **"Create topic"**

**Subscribe to Topic:**
1. Click topic name
2. Click **"Create subscription"** button
3. Protocol: **Email**
4. Endpoint: `your-email@example.com`
5. Click **"Create subscription"**
6. **Confirm in your email**

### Topic 3: MemeMuseum-ContentModeration

**Create Topic:**
1. Click **"Create topic"** button
2. Name: `MemeMuseum-ContentModeration`
3. Type: **Standard**
4. Click **"Create topic"**

**Subscribe to Topic:**
1. Click topic name
2. Click **"Create subscription"** button
3. Protocol: **Email**
4. Endpoint: `your-email@example.com`
5. Click **"Create subscription"**
6. **Confirm in your email**

### Verify All Topics
```
✅ MemeMuseum-NewMemeUpload - subscribed
✅ MemeMuseum-TrendingAlert - subscribed
✅ MemeMuseum-ContentModeration - subscribed
```

---

## STEP 4: Create IAM Role

### Go to IAM
1. AWS Console → search **"IAM"** → click **IAM**
2. Click **"Roles"** (left sidebar)
3. Click **"Create role"** button

### Configuration
| Field | Value |
|-------|-------|
| Trusted entity | AWS service |
| Use case | EC2 |
| Role name | `MemeMuseumEC2Role` |

### Steps
1. **Select trusted entity:**
   - Trusted entity type: **AWS service**
   - Use case: **EC2**
   - Click **"Next"**

2. **Add permissions:**
   - Search and add these policies (check all):
     - [ ] AmazonDynamoDBFullAccess
     - [ ] AmazonS3FullAccess
     - [ ] AmazonSNSFullAccess
     - [ ] AmazonRekognitionFullAccess
     - [ ] AWSLambdaFullAccess
   - Click **"Next"**

3. **Name the role:**
   - Role name: `MemeMuseumEC2Role`
   - Click **"Create role"**

### Verify Role
```
✅ MemeMuseumEC2Role created with 5 policies attached
```

---

## STEP 5: Launch EC2 Instance

### Go to EC2
1. AWS Console → search **"EC2"** → click **EC2**
2. Click **"Launch instances"** button

### Configuration

| Setting | Value |
|---------|-------|
| **OS/AMI** | Amazon Linux 2 (free tier) |
| **Instance type** | t2.micro (free tier) |
| **Name** | MemeMuseumServer |
| **Key pair** | Create new `my-keypair` |
| **Network** | Default VPC |
| **Security Group** | Create new |
| **IAM role** | MemeMuseumEC2Role |

### Steps

1. **Choose AMI:**
   - Select: **Amazon Linux 2 AMI (HVM), SSD Volume Type**

2. **Choose Instance Type:**
   - Select: **t2.micro** (free tier eligible)
   - Click **"Next"**

3. **Configure Instance Details:**
   - IAM role: **MemeMuseumEC2Role**
   - Click **"Next"**

4. **Add Storage:**
   - Leave default (8 GB)
   - Click **"Next"**

5. **Add Tags:**
   - Key: `Name`
   - Value: `MemeMuseumServer`
   - Click **"Next"**

6. **Configure Security Group:**
   - Create new security group
   - Name: `meme-museum-sg`
   - Add rules:
     - Type: **SSH** | Port: **22** | Source: **My IP**
     - Type: **Custom TCP** | Port: **5000** | Source: **0.0.0.0/0**
   - Click **"Review and Launch"**

7. **Review and Launch:**
   - Click **"Launch"**

8. **Create Key Pair:**
   - Key pair name: `my-keypair`
   - Download: **Download Key Pair**
   - ⚠️ Save this file safely (you'll need it to SSH)

9. **Launch Instances:**
   - Click **"Launch Instances"**
   - Click **"View Instances"**

### Verify EC2
```
✅ Instance name: MemeMuseumServer
✅ State: running
✅ Public IPv4 address: [copy this]
✅ IAM role: MemeMuseumEC2Role
```

---

## STEP 6: Get Your AWS Account ID

### Find Account ID
1. AWS Console → click **Account** dropdown (top right)
2. Click **"Account"**
3. Copy the **Account ID** (12-digit number)

Example: `123456789012`

**Important:** You'll need this for `.env` file!

---

## STEP 7: Get SNS Topic ARNs

### Find Each Topic ARN
1. Go to SNS → **Topics**
2. Click each topic one by one
3. Copy the **Topic ARN** (long string starting with `arn:aws:...`)

You should have:
```
NEW_MEME_UPLOAD = arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-NewMemeUpload
TRENDING_ALERT = arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-TrendingAlert
MODERATION_ALERT = arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-ContentModeration
```

---

## STEP 8: Create .env File

### On Your Local Computer (or EC2 via nano)

Create file: `.env`

```
# AWS Configuration
AWS_DEFAULT_REGION=us-east-1

# S3
S3_BUCKET_NAME=meme-museum-bucket

# DynamoDB
USERS_TABLE=UsersTable
MEMES_TABLE=MemeTable
ACTIVITY_LOG_TABLE=ActivityLogTable

# SNS Topics (replace YOUR_ACCOUNT_ID with your 12-digit number)
NEW_MEME_UPLOAD_SNS_TOPIC=arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-NewMemeUpload
TRENDING_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-TrendingAlert
MODERATION_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:YOUR_ACCOUNT_ID:MemeMuseum-ContentModeration

# Flask
SECRET_KEY=your-super-secret-key-here
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
FLASK_DEBUG=False
```

**Replace `YOUR_ACCOUNT_ID` with your actual 12-digit account ID!**

---

## STEP 9: SSH into EC2

### On Your Local Computer

1. **Move key file to safe location:**
   ```bash
   # Windows PowerShell
   Move-Item -Path "Downloads\my-keypair.pem" -Destination "C:\path\to\safe\place\"
   ```

2. **Connect to EC2:**
   ```bash
   # Get EC2 Public IP from AWS Console
   ssh -i /path/to/my-keypair.pem ec2-user@YOUR_EC2_PUBLIC_IP
   
   # Example:
   ssh -i ~/.ssh/my-keypair.pem ec2-user@54.123.45.67
   ```

3. **First connection:** Type **yes** when asked to trust the host

---

## STEP 10: Install Software on EC2

### Run These Commands (one by one)

```bash
# Update system
sudo yum update -y

# Install Python 3 and Git
sudo yum install python3 git -y

# Verify Python
python3 --version

# Clone code (or upload via SCP)
git clone https://github.com/YOUR_USERNAME/Meme_Museum.git
cd Meme_Museum

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
```

---

## STEP 11: Configure .env on EC2

### Create .env File on EC2

```bash
nano .env
```

**Paste the content (from STEP 8) with YOUR_ACCOUNT_ID replaced:**

```
AWS_DEFAULT_REGION=us-east-1
S3_BUCKET_NAME=meme-museum-bucket
USERS_TABLE=UsersTable
MEMES_TABLE=MemeTable
ACTIVITY_LOG_TABLE=ActivityLogTable
NEW_MEME_UPLOAD_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-NewMemeUpload
TRENDING_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-TrendingAlert
MODERATION_ALERT_SNS_TOPIC=arn:aws:sns:us-east-1:123456789012:MemeMuseum-ContentModeration
SECRET_KEY=change-me-to-something-random
FLASK_RUN_HOST=0.0.0.0
FLASK_RUN_PORT=5000
```

**Save:** Ctrl+X → Y → Enter

---

## STEP 12: Run Application

### On EC2

```bash
# Make sure you're in the right directory
cd ~/Meme_Museum

# Activate virtual environment
source venv/bin/activate

# Run the AWS app
python aws_app.py
```

You should see:
```
============================================================
MEME MUSEUM - AWS PRODUCTION DEPLOYMENT
============================================================
Running on http://0.0.0.0:5000
Region: us-east-1
DynamoDB Tables: UsersTable, MemeTable, ActivityLogTable
S3 Bucket: meme-museum-bucket
============================================================
```

---

## STEP 13: Access Your Application

### In Your Browser

```
http://YOUR_EC2_PUBLIC_IP:5000
```

Example: `http://54.123.45.67:5000`

### Test the App
1. ✅ Register a new account
2. ✅ Check your email for SNS notification
3. ✅ Upload an image
4. ✅ Check AWS S3 Console (image should be there)
5. ✅ Check your email for moderation notification
6. ✅ Like/comment on meme
7. ✅ Delete a meme

---

## Verification Checklist

```
AWS Resources Created:
  ✅ S3 bucket: meme-museum-bucket
  ✅ DynamoDB: UsersTable (email key)
  ✅ DynamoDB: MemeTable (meme_id key)
  ✅ DynamoDB: ActivityLogTable (log_id key)
  ✅ SNS: 3 topics with email subscriptions
  ✅ IAM Role: MemeMuseumEC2Role (5 policies)
  ✅ EC2: t2.micro instance running
  
Configuration:
  ✅ .env file created with correct values
  ✅ Account ID in SNS ARNs
  ✅ Table names match exactly
  ✅ Region: us-east-1 everywhere
  
Application:
  ✅ Code running on EC2
  ✅ Accessible at http://EC2_IP:5000
  ✅ Data saves to DynamoDB
  ✅ Images save to S3
  ✅ Emails received from SNS
```

---

## Troubleshooting

### Can't connect to EC2
```
❌ Error: Connection timeout
✅ Solution: 
  - Verify security group allows SSH (port 22)
  - Verify key file permissions: chmod 400 my-keypair.pem
  - Verify key file path is correct
```

### Application won't start
```
❌ Error: ModuleNotFoundError
✅ Solution: 
  - Verify virtual environment activated: source venv/bin/activate
  - Verify dependencies installed: pip install -r requirements.txt
```

### Tables not found
```
❌ Error: ResourceNotFoundException
✅ Solution:
  - Check table names in .env match AWS console EXACTLY
  - Verify tables show "Active" status in DynamoDB
  - Check region is us-east-1
```

### No email notifications
```
❌ Error: No emails received
✅ Solution:
  - Go to SNS Topics
  - Verify subscription status is "Confirmed" (not "PendingConfirmation")
  - Check email account for AWS notifications
```

---

## Cost Estimate (Free Tier Eligible)

| Resource | Monthly Cost |
|----------|--------------|
| S3 | Free (first 5 GB) |
| DynamoDB | Free (first 25 GB write, 25 GB read) |
| SNS | Free (first 1000 emails) |
| EC2 t2.micro | Free (first 750 hours/month) |
| **Total** | **$0** (if within free tier limits) |

---

## Next Steps

1. ✅ Keep EC2 instance running
2. ✅ Monitor DynamoDB for data growth
3. ✅ Set up CloudWatch alarms
4. ✅ Configure SSL/TLS for production
5. ✅ Set up domain name with Route 53

---

**Setup Complete! 🎉**

Your Meme Museum is now live on AWS!
