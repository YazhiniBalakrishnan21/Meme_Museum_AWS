import os
import re
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from passlib.hash import pbkdf2_sha256
from dotenv import load_dotenv

# Load .env for local/dev
load_dotenv()

# Local development - uses Python dictionaries for data storage
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "local-dev-secret-key")

EMAIL_RE = re.compile(r"[^@]+@[^@]+\.[^@]+")

# ==========================================
# IN-MEMORY DATA STORAGE (Local Development)
# ==========================================
users_db = {}  # {email: {password, created_at, bio}}
memes_db = {}  # {meme_id: {meme_id, user, title, description, category, tags, labels, detected_text, likes, views, downloads, status, created_at}}
likes_db = {}  # {meme_id_user: {meme_id, user, created_at}}
activity_log_db = []  # [{id, ts, action, user, meta}]
meme_images = {}  # {meme_id: image_bytes}


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


def log_activity(action: str, user_email: str, meta: dict = None):
    item = {
        "id": str(uuid.uuid4()),
        "ts": now_iso(),
        "action": action,
        "user": user_email,
        "meta": json.dumps(meta or {})
    }
    activity_log_db.append(item)


def moderate_image_bytes(image_bytes: bytes, min_confidence: float = 60.0):
    """
    Local development: Simple moderation - accept all images
    In production (AWS), this uses Rekognition
    """
    # For local dev, always approve
    return True, []


def detect_labels_and_text(image_bytes: bytes):
    """
    Local development: Return empty labels and text
    In production (AWS), this uses Rekognition
    """
    return [], ""


def get_image_for_meme(meme_id: str):
    """Retrieve stored image bytes from memory"""
    return meme_images.get(meme_id)


def store_image_for_meme(meme_id: str, image_bytes: bytes):
    """Store image bytes in memory"""
    meme_images[meme_id] = image_bytes


    # Send important notifications
    try:
        if action == "register":
            subject = f"[Meme Museum] New user registered: {user_email}"
            message = f"User {user_email} registered at {item['ts']}\nMeta: {meta or {}}"
        elif action == "upload":
            status = (meta or {}).get("status")
            meme_id = (meta or {}).get("meme_id")
            if status and status.lower() == "rejected":
                subject = f"[Meme Museum] Meme rejected: {meme_id}"
                message = f"Meme {meme_id} uploaded by {user_email} was rejected. Reasons: {meta.get('reasons') if meta else 'N/A'}"
            elif status and status.lower() == "approved":
                subject = f"[Meme Museum] Meme approved: {meme_id}"
                message = f"Meme {meme_id} uploaded by {user_email} was approved."
    except Exception:
        pass


def moderate_image_bytes(image_bytes: bytes, min_confidence: float = 60.0):
    # Local dev: always approve
    reasons = []
    approved = True
    return approved, reasons


def detect_labels_and_text(image_bytes: bytes):
    # Local dev: return empty
    labels = []
    detected_text = ""
    return labels, detected_text
# ==========================================
# ROUTES
# ==========================================
@app.route('/health')
def health():
    return jsonify({"status": "ok", "time": now_iso(), "environment": "local-development"})


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

        # Check duplicate
        if email in users_db:
            flash("User already exists. Please login.")
            return redirect(url_for("login"))

        hashed = hash_password(password)
        users_db[email] = {
            "email": email,
            "password": hashed,
            "created_at": now_iso(),
            "bio": "",
        }
        log_activity("register", email)
        flash("Account created successfully. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").lower()
        password = request.form.get("password", "")

        user = users_db.get(email)
        if user and verify_password(password, user.get("password", "")):
            session["user"] = email
            log_activity("login", email)
            return redirect(url_for("dashboard"))

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
    # Get user's memes from local storage
    user_memes = [meme for meme in memes_db.values() if meme["user"] == user]
    return render_template("dashboard.html", memes=user_memes)


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
        # Moderation
        approved, reasons = moderate_image_bytes(image_bytes, min_confidence=60.0)

        meme_id = generate_meme_id()
        user = session["user"]

        # Store image in memory
        store_image_for_meme(meme_id, image_bytes)

        labels, detected_text = detect_labels_and_text(image_bytes)

        item = {
            "meme_id": meme_id,
            "user": user,
            "title": title,
            "description": description,
            "category": category,
            "tags": tags,
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
        memes_db[meme_id] = item
        log_activity("upload", user, {"meme_id": meme_id, "status": item["status"], "reasons": reasons, "labels": labels})

        if not approved:
            flash("Meme was rejected by moderation.")
        else:
            flash("Meme uploaded and approved!")

        return redirect(url_for("dashboard"))

    return render_template("upload.html")


@app.route("/view/<meme_id>")
def view_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    item = memes_db.get(meme_id)
    if not item:
        flash("Meme not found.")
        return redirect(url_for("dashboard"))

    # Increment view count
    item["views"] = item.get("views", 0) + 1

    return render_template("meme.html", meme=item)


@app.route("/comment/<meme_id>", methods=["POST"])
def comment_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    text = request.form.get("comment", "")
    if not text:
        return redirect(url_for("view_meme", meme_id=meme_id))

    item = memes_db.get(meme_id)
    if not item:
        flash("Meme not found.")
        return redirect(url_for("dashboard"))

    comment = {"user": session["user"], "text": text, "ts": now_iso()}
    if "comments" not in item:
        item["comments"] = []
    item["comments"].append(comment)

    log_activity("comment", session["user"], {"meme_id": meme_id})
    return redirect(url_for("view_meme", meme_id=meme_id))


@app.route("/delete/<meme_id>", methods=["POST"])
def delete_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    item = memes_db.get(meme_id)
    if not item:
        flash("Meme not found.")
        return redirect(url_for("dashboard"))

    if item.get("user") != user:
        flash("Not authorized to delete this meme.")
        return redirect(url_for("dashboard"))

    # Delete from memory
    del memes_db[meme_id]
    if meme_id in meme_images:
        del meme_images[meme_id]

    log_activity("delete", user, {"meme_id": meme_id})
    flash("Meme deleted.")
    return redirect(url_for("dashboard"))


@app.route("/like/<meme_id>")
def like_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    like_key = f"{meme_id}_{user}"

    # Check if already liked
    if like_key not in likes_db:
        likes_db[like_key] = {
            "meme_id": meme_id,
            "user": user,
            "created_at": now_iso()
        }
        # Increment likes count
        if meme_id in memes_db:
            memes_db[meme_id]["likes"] = memes_db[meme_id].get("likes", 0) + 1
        log_activity("like", user, {"meme_id": meme_id})

    return redirect(url_for("view_meme", meme_id=meme_id))


@app.route("/download/<meme_id>")
def download_meme(meme_id):
    if "user" not in session:
        return redirect(url_for("login"))

    item = memes_db.get(meme_id)
    if not item or item.get("status") != "approved":
        flash("Meme not available for download.")
        return redirect(url_for("dashboard"))

    # Increment download count
    item["downloads"] = item.get("downloads", 0) + 1
    log_activity("download", session["user"], {"meme_id": meme_id})

    # In local dev, redirect back to view (real implementation would generate file)
    flash("Download tracked! (Local dev - file download not implemented)")
    return redirect(url_for("view_meme", meme_id=meme_id))

# ==========================================
# RUN APP
# ==========================================
if __name__ == "__main__":
    debug = os.environ.get("FLASK_DEBUG", "False").lower() in ("1", "true", "yes")
    host = os.environ.get("FLASK_RUN_HOST", "0.0.0.0")
    port = int(os.environ.get("FLASK_RUN_PORT", "5000"))
    print("\n" + "="*50)
    print("MEME MUSEUM - LOCAL DEVELOPMENT")
    print("="*50)
    print(f"Running on http://{host}:{port}")
    print("Using in-memory dictionary storage (NOT AWS)")
    print("="*50 + "\n")
    app.run(host=host, port=port, debug=debug)
