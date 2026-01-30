from flask import Flask, render_template

app = Flask(__name__, template_folder="app/templates")

@app.route("/")
def dashboard():
    return render_template("dashboard.html")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("base.html"), 404

if __name__ == "__main__":
    app.run(debug=True)
