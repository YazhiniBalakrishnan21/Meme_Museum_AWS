from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
import requests
from io import BytesIO

app = Flask(__name__)
app.secret_key = "secret123"

# -----------------------------
# In-memory storage (for local dev)
# -----------------------------
users = {}   # { email: password }
memes = []   # list of memes
chats = {}   # private messages


# -----------------------------
# Helper for chat key
# -----------------------------
def chat_key(u1, u2):
    a, b = sorted([u1.lower(), u2.lower()])
    return f"{a}|{b}"


# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    if "user" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# -----------------------------
# ABOUT
# -----------------------------
@app.route("/about")
def about():
    return render_template("about.html")


# -----------------------------
# REGISTER
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]

        if email in users:
            flash("User already exists. Please login.")
            return redirect(url_for("login"))

        users[email] = password
        flash("Account created successfully. Please login.")
        return redirect(url_for("login"))

    return render_template("register.html")


# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].lower()
        password = request.form["password"]

        if email in users and users[email] == password:
            session["user"] = email
            return redirect(url_for("dashboard"))

        flash("Invalid email or password.")
        return redirect(url_for("login"))

    return render_template("login.html")


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", memes=memes)


# -----------------------------
# UPLOAD MEME
# -----------------------------
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        image = request.form["image"]

        memes.append({
            "title": title,
            "image": image,
            "likes": 0,
            "comments": [],
            "saved_by": set()
        })

        flash("Meme uploaded successfully!")
        return redirect(url_for("dashboard"))

    return render_template("upload.html")


# -----------------------------
# LIKE MEME
# -----------------------------
@app.route("/like/<int:index>")
def like(index):
    if "user" not in session:
        return redirect(url_for("login"))

    if 0 <= index < len(memes):
        memes[index]["likes"] += 1

    return redirect(url_for("dashboard"))


# -----------------------------
# SAVE / UNSAVE MEME
# -----------------------------
@app.route("/save/<int:index>", methods=["POST"])
def save(index):
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    meme = memes[index]

    if user in meme["saved_by"]:
        meme["saved_by"].remove(user)
    else:
        meme["saved_by"].add(user)

    return redirect(url_for("dashboard"))


# -----------------------------
# SAVED MEMES
# -----------------------------
@app.route("/saved")
def saved():
    if "user" not in session:
        return redirect(url_for("login"))

    user = session["user"]
    saved_memes = [m for m in memes if user in m["saved_by"]]
    return render_template("saved.html", memes=saved_memes)


# -----------------------------
# DELETE MEME
# -----------------------------
@app.route("/delete/<int:index>", methods=["POST"])
def delete(index):
    if "user" not in session:
        return redirect(url_for("login"))

    if 0 <= index < len(memes):
        memes.pop(index)

    return redirect(url_for("dashboard"))


# -----------------------------
# COMMENTS
# -----------------------------
@app.route("/comment/<int:meme_index>", methods=["POST"])
def comment(meme_index):
    if "user" not in session:
        return redirect(url_for("login"))

    text = request.form["comment"]
    memes[meme_index]["comments"].append({
        "user": session["user"],
        "text": text
    })

    return redirect(url_for("dashboard"))


@app.route("/delete-comment/<int:meme_index>/<int:comment_index>", methods=["POST"])
def delete_comment(meme_index, comment_index):
    if "user" not in session:
        return redirect(url_for("login"))

    comment = memes[meme_index]["comments"][comment_index]

    if comment["user"] == session["user"]:
        memes[meme_index]["comments"].pop(comment_index)

    return redirect(url_for("dashboard"))


# -----------------------------
# DOWNLOAD MEME
# -----------------------------
@app.route("/download/<int:index>")
def download(index):
    if "user" not in session:
        return redirect(url_for("login"))

    image_url = memes[index]["image"]
    response = requests.get(image_url)

    return send_file(
        BytesIO(response.content),
        as_attachment=True,
        download_name="meme.jpg"
    )


# -----------------------------
# MESSAGES (FRIENDS LIST)
# -----------------------------
@app.route("/messages")
def messages():
    if "user" not in session:
        return redirect(url_for("login"))

    me = session["user"]
    friends = [u for u in users if u != me]

    return render_template("messages.html", friends=friends)


# -----------------------------
# CHAT PAGE
# -----------------------------
@app.route("/chat/<friend>")
def chat(friend):
    if "user" not in session:
        return redirect(url_for("login"))

    key = chat_key(session["user"], friend)
    thread = chats.get(key, [])

    return render_template("chat.html", friend=friend, thread=thread)


# -----------------------------
# SEND MESSAGE
# -----------------------------
@app.route("/send/<friend>", methods=["POST"])
def send(friend):
    if "user" not in session:
        return redirect(url_for("login"))

    text = request.form["text"]
    key = chat_key(session["user"], friend)

    chats.setdefault(key, [])
    chats[key].append({
        "sender": session["user"],
        "text": text
    })

    return redirect(url_for("chat", friend=friend))


# -----------------------------
# RUN APP
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
