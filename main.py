from flask import Flask, render_template, request, redirect, session
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__, template_folder="app/templates")
app.secret_key = "dev-secret"

# Fix for session persistence - use Lax but ensure session commits
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize Firebase Admin
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)


@app.route("/")
def dashboard():
    if "user" not in session:
        return redirect("/login")
    return render_template("dashboard.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        print("POST /login hit")

        data = request.get_json(silent=True) or {}
        print("POST /login data:", data)

        token = data.get("token")
        if not token:
            print("No token received")
            return {"error": "Missing token"}, 400

        try:
            decoded = auth.verify_id_token(token, check_revoked=False)
            session["user"] = decoded["uid"]
            session.modified = True  # Explicitly mark session as modified
            print("Session set to:", session["user"])
            return {"ok": True}, 200
        except Exception as e:
            print("Token verification failed:", e)
            return {"error": "Invalid token"}, 401

    # If already logged in, skip login page
    if "user" in session:
        return redirect("/")

    return render_template("login.html")


@app.route("/whoami")
def whoami():
    return {"user": session.get("user")}, 200


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/status")
def status():
    return render_template("status.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)