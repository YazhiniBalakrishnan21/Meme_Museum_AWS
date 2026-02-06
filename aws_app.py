import os
import re
import uuid
import json
import boto3
import botocore
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv

# Load .env for AWS deployment
load_dotenv()

# ==========================================
# AWS CONFIGURATION
# ==========================================
AWS_REGION = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET_NAME")
USERS_TABLE = os.environ.get("USERS_TABLE", "UsersTable")
MEMES_TABLE = os.environ.get("MEMES_TABLE", "MemeTable")
ACTIVITY_LOG_TABLE = os.environ.get("ACTIVITY_LOG_TABLE", "ActivityLogTable")
PRESIGNED_EXPIRATION = int(os.environ.get("PRESIGNED_EXPIRATION", "3600"))
SECRET_KEY = os.environ.get("SECRET_KEY", "replace-me-in-prod")

# SNS Topic ARNs for notifications
SNS_TOPIC_NEW_UPLOAD = os.environ.get("NEW_MEME_UPLOAD_SNS_TOPIC")
SNS_TOPIC_TRENDING = os.environ.get("TRENDING_ALERT_SNS_TOPIC")
SNS_TOPIC_MODERATION = os.environ.get("MODERATION_ALERT_SNS_TOPIC")

# Validate required config
if not S3_BUCKET:
    raise RuntimeError("S3_BUCKET_NAME environment variable is required")

app = Flask(__name__)
app.secret_key = SECRET_KEY

# ==========================================
# AWS CLIENTS
# ==========================================
session_boto = boto3.Session(region_name=AWS_REGION)
s3_client = session_boto.client("s3")
rekognition_client = session_boto.client("rekognition")
dynamodb_resource = session_boto.resource("dynamodb", region_name=AWS_REGION)
sns_client = session_boto.client("sns", region_name=AWS_REGION)

# DynamoDB Table References
users_table = dynamodb_resource.Table(USERS_TABLE)
memes_table = dynamodb_resource.Table(MEMES_TABLE)
activity_log_table = dynamodb_resource.Table(ACTIVITY_LOG_TABLE)

EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")

# ==========================================
# HELPER FUNCTIONS
# ==========================================
def hash_password(password: str) -> str:
    return pbkdf2_sha256.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pbkdf2_sha256.verify(password, hashed)


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def generate_meme_id() -> str:
    return str(uuid.uuid4())


def presigned_get_url(s3_key: str, expiration: int = PRESIGNED_EXPIRATION) -> str:
    """Generate presigned URL for S3 object retrieval"""
    return s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": S3_BUCKET, "Key": s3_key},
        ExpiresIn=expiration,
    )


def upload_bytes_to_s3(bytes_data: bytes, key: str, content_type: str):
    """Upload image bytes to S3"""
    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=bytes_data,
        ContentType=content_type
    )


def publish_sns(topic_arn: str, subject: str, message: str):
    """Publish notification to SNS topic"""
    if not topic_arn:
        return
    try:
        sns_client.publish(
            TopicArn=topic_arn,
            Subject=subject[:100],
            Message=message
        )
    except Exception as e:
        print(f"SNS publish error: {e}")
        # Do not fail on SNS errors


def log_activity(action: str, user_email: str, meta: dict = None):
    """Log activity to DynamoDB ActivityLogTable"""
    log_id = str(uuid.uuid4())
    item = {
        "log_id": log_id,
        "ts": now_iso(),
        "action": action,
        "user": user_email,
        "meta": json.dumps(meta or {})
    }
    try:
        activity_log_table.put_item(Item=item)
    except botocore.exceptions.ClientError as e:
        print(f"Error logging activity: {e}")


def moderate_image_bytes(image_bytes: bytes, min_confidence: float = 60.0):
    """
    Use AWS Rekognition to moderate image content.
    Returns (approved: bool, reasons: list)
    """
    try:
        resp = rekognition_client.detect_moderation_labels(
            Image={"Bytes": image_bytes},
            MinConfidence=min_confidence
        )
        reasons = []
        for label in resp.get("ModerationLabels", []):
            name = label.get("Name", "")
            confidence = label.get("Confidence", 0)
            # Disallow: explicit nudity, violence, hate symbols, sexual content
            if name.lower() in ["explicit nudity", "violence", "hate symbols", "sexual content"]:
                if confidence >= min_confidence:
                    reasons.append({
                        "label": name,
                        "confidence": float(confidence)
                    })
        approved = len(reasons) == 0
        return approved, reasons
    except Exception as e:
        print(f"Rekognition moderation error: {e}")
        # Default to approve on error
        return True, []


def detect_labels_and_text(image_bytes: bytes):
    """
    Use AWS Rekognition to detect labels and text in image.
    Returns (labels: list, detected_text: str)
    """
    try:
        # Detect labels
        labels_resp = rekognition_client.detect_labels(
            Image={"Bytes": image_bytes},
            MaxLabels=20,
            MinConfidence=50
        )
        labels = [label["Name"] for label in labels_resp.get("Labels", [])]

        # Detect text
        text_resp = rekognition_client.detect_text(
            Image={"Bytes": image_bytes}
        )
        detected_text = " ".join([
            detection["DetectedText"]
            for detection in text_resp.get("TextDetections", [])
            if detection.get("Type") == "LINE"
        ])

        return labels, detected_text
    except Exception as e:
        print(f"Rekognition labels/text error: {e}")
        return [], ""


# ==========================================
# ROUTES
# ==========================================
@app.route('/health')
def health():
    return jsonify({
        "status": "ok",
        "time": now_iso(),
        "environment": "AWS-Production",
        "region": AWS_REGION
    })


@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password", "")

        if not EMAIL_RE.match(email):
            flash("Invalid email format.")
            return redirect(url_for("register"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.")
            return redirect(url_for("register"))

        # Check if user already exists
        try:
            resp = users_table.get_item(Key={"email": email})
            if "Item" in resp:
                flash("User already exists. Please login.")
                return redirect(url_for("login"))
        except botocore.exceptions.ClientError as e:
            flash("Internal error checking user.")
            print(f"DynamoDB error: {e}")
            return redirect(url_for("register"))

        # Create new user
        hashed = hash_password(password)
        try:
            users_table.put_item(Item={
                "email": email,
                "password": hashed,
                "created_at": now_iso(),
                "bio": "",
            })
            log_activity("register", email)

            # Send SNS notification
            subject = f"[Meme Museum] New user registered: {email}"
            message = f"User {email} registered at {now_iso()}"
            publish_sns(SNS_TOPIC_NEW_UPLOAD, subject, message)

            flash("Account created successfully. Please login.")
            return redirect(url_for("login"))
        except botocore.exceptions.ClientError as e:
            flash("Error creating account.")
            print(f"DynamoDB error: {e}")
            return redirect(url_for("register"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password", "")

        try:
            resp = users_table.get_item(Key={"email": email})
            user = resp.get("Item")
            if user and verify_password(password, user.get("password", "")):
                session["user"] = email
                log_activity("login", email)
                return redirect(url_for("dashboard"))
        except botocore.exceptions.ClientError as e:
            print(f"DynamoDB error: {e}")

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    email = session.pop("user", None)
    if email:
        log_activity("logout", email)
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    try:
        # Query memes by user (requires GSI with user as partition key)
        resp = memes_table.query(
            IndexName="user-created_at-index",
            KeyConditionExpression="user = :user",
            ExpressionAttributeValues={":user": user}
        )
        items = resp.get("Items", [])
        # Attach presigned URLs for approved memes
        for item in items:
            if item.get("status") == "approved":
                item["url"] = presigned_get_url(item.get("s3_key", ""))
    except botocore.exceptions.ClientError as e:
        print(f"DynamoDB query error: {e}")
        items = []
        flash("Error loading memes.")

    return render_template("dashboard.html", memes=items)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form.get("title", "")
        description = request.form.get("description", "")
        category = request.form.get("category", "Uncategorized")
        tags = [t.strip() for t in request.form.get("tags", "").split(",") if t.strip()]
        file = request.files.get("image")

        if not file:
            flash("Please provide an image file.")
            return redirect(url_for("upload"))

        image_bytes = file.read()
        # Moderation check
        approved, reasons = moderate_image_bytes(image_bytes, min_confidence=60.0)

        meme_id = generate_meme_id()
        user = session["user"]
        filename = file.filename or f"{meme_id}.jpg"
        s3_key = f"memes/{user}/{meme_id}/{filename}"

        # Upload to S3
        try:
            upload_bytes_to_s3(image_bytes, s3_key, file.content_type or "image/jpeg")
        except Exception as e:
            flash("Error uploading to S3.")
            print(f"S3 upload error: {e}")
            return redirect(url_for("upload"))

        # Detect labels and text
        labels, detected_text = detect_labels_and_text(image_bytes)

        # Create meme record
        item = {
            "meme_id": meme_id,
            "user": user,
            "title": title,
            "description": description,
            "category": category,
            "tags": tags,
            "s3_key": s3_key,
            "labels": labels,
            "detected_text": detected_text,
            "likes": 0,
            "views": 0,
            "downloads": 0,
            "status": "approved" if approved else "rejected",
            "reject_reasons": reasons,
            "created_at": now_iso(),
            "comments": []
        }

        try:
            memes_table.put_item(Item=item)
            log_activity(
                "upload",
                user,
                {
                    "meme_id": meme_id,
                    "status": item["status"],
                    "reasons": reasons,
                    "labels": labels
                }
            )

            # Send SNS notification based on status
            if approved:
                subject = f"[Meme Museum] Meme approved: {meme_id}"
                message = f"Meme '{title}' by {user} was approved.\nMeme ID: {meme_id}"
                publish_sns(SNS_TOPIC_NEW_UPLOAD, subject, message)
                flash("Meme uploaded and approved!")
            else:
                subject = f"[Meme Museum] Meme rejected: {meme_id}"
                reasons_str = "; ".join([f"{r['label']} ({r['confidence']:.1f}%)" for r in reasons])
                message = f"Meme '{title}' by {user} was rejected.\nReasons: {reasons_str}"
                publish_sns(SNS_TOPIC_MODERATION, subject, message)
                flash("Meme was rejected by moderation.")

            return redirect(url_for("dashboard"))
        except botocore.exceptions.ClientError as e:
            flash("Error saving meme.")
            print(f"DynamoDB error: {e}")
            return redirect(url_for("upload"))

    return render_template("upload.html")


@app.route("/view/<meme_id>")
def view_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        resp = memes_table.get_item(Key={"meme_id": meme_id})
        item = resp.get("Item")
        if not item:
            flash("Meme not found.")
            return redirect(url_for("dashboard"))

        # Increment view count
        try:
            memes_table.update_item(
                Key={"meme_id": meme_id},
                UpdateExpression="ADD views :inc",
                ExpressionAttributeValues={":inc": 1}
            )
            item["views"] = item.get("views", 0) + 1
        except botocore.exceptions.ClientError as e:
            print(f"Error updating views: {e}")

        # Generate presigned URL for approved memes
        if item.get("status") == "approved":
            item["url"] = presigned_get_url(item.get("s3_key", ""))

        return render_template("meme.html", meme=item)
    except botocore.exceptions.ClientError as e:
        flash("Error loading meme.")
        print(f"DynamoDB error: {e}")
        return redirect(url_for("dashboard"))


@app.route("/comment/<meme_id>", methods=["POST"])
def comment_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    text = request.form.get("comment", "")
    if not text:
        return redirect(url_for("view_meme", meme_id=meme_id))

    comment = {
        "user": session["user"],
        "text": text,
        "ts": now_iso()
    }

    try:
        memes_table.update_item(
            Key={"meme_id": meme_id},
            UpdateExpression="SET comments = list_append(if_not_exists(comments, :empty_list), :c)",
            ExpressionAttributeValues={
                ":c": [comment],
                ":empty_list": []
            }
        )
        log_activity("comment", session["user"], {"meme_id": meme_id})
    except botocore.exceptions.ClientError as e:
        print(f"Error adding comment: {e}")
        flash("Error adding comment.")

    return redirect(url_for("view_meme", meme_id=meme_id))


@app.route("/delete/<meme_id>", methods=["POST"])
def delete_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    try:
        resp = memes_table.get_item(Key={"meme_id": meme_id})
        item = resp.get("Item")
        if not item:
            flash("Meme not found.")
            return redirect(url_for("dashboard"))

        if item.get("user") != user:
            flash("Not authorized to delete this meme.")
            return redirect(url_for("dashboard"))

        # Delete from S3
        try:
            s3_client.delete_object(Bucket=S3_BUCKET, Key=item.get("s3_key", ""))
        except Exception as e:
            print(f"Error deleting from S3: {e}")

        # Delete from DynamoDB
        memes_table.delete_item(Key={"meme_id": meme_id})
        log_activity("delete", user, {"meme_id": meme_id})
        flash("Meme deleted.")
        return redirect(url_for("dashboard"))
    except botocore.exceptions.ClientError as e:
        flash("Error deleting meme.")
        print(f"DynamoDB error: {e}")
        return redirect(url_for("dashboard"))


@app.route("/like/<meme_id>")
def like_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    try:
        # Try to increment likes (idempotent operation)
        memes_table.update_item(
            Key={"meme_id": meme_id},
            UpdateExpression="ADD likes :inc",
            ExpressionAttributeValues={":inc": 1}
        )
        log_activity("like", user, {"meme_id": meme_id})
    except botocore.exceptions.ClientError as e:
        print(f"Error liking meme: {e}")

    return redirect(url_for("view_meme", meme_id=meme_id))


@app.route("/download/<meme_id>")
def download_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    try:
        resp = memes_table.get_item(Key={"meme_id": meme_id})
        item = resp.get("Item")
        if not item or item.get("status") != "approved":
            flash("Meme not available for download.")
            return redirect(url_for("dashboard"))

        # Increment download count
        try:
            memes_table.update_item(
                Key={"meme_id": meme_id},
                UpdateExpression="ADD downloads :inc",
                ExpressionAttributeValues={":inc": 1}
            )
        except botocore.exceptions.ClientError as e:
            print(f"Error updating downloads: {e}")

        log_activity("download", session["user"], {"meme_id": meme_id})

        # Generate presigned URL and redirect
        url = presigned_get_url(item.get("s3_key", ""), expiration=PRESIGNED_EXPIRATION)
        return redirect(url)
    except botocore.exceptions.ClientError as e:
        flash("Error downloading meme.")
        print(f"DynamoDB error: {e}")
        return redirect(url_for("dashboard"))


# ==========================================
# RUN APP
# ==========================================
if __name__ == "__main__":
        app.run(host="0.0.0.0", port=5000)