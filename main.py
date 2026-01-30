from flask import Flask, render_template, request, redirect, session
import firebase_admin
from firebase_admin import credentials, auth

app = Flask(__name__, template_folder="app/templates")
app.secret_key = "dev-secret"

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
        token = request.json["token"]
        decoded = auth.verify_id_token(token)
        session["user"] = decoded["uid"]
        return "", 200
    return render_template("login.html")

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
