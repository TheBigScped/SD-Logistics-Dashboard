from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, session, jsonify
import firebase_admin
from firebase_admin import credentials, auth
from db import get_all_shipments, create_shipment
from mongo_db import log_event, get_all_events, create_event

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


@app.route("/shipments", methods=["GET", "POST"])
def shipments():
    # Require login
    if "user" not in session:
        return redirect("/login")
    
    if request.method == "POST":
        # Handle form submission
        tracking_number = request.form.get("tracking_number")
        status = request.form.get("status")
        origin = request.form.get("origin")
        destination = request.form.get("destination")
        
        try:
            create_shipment(tracking_number, status, origin, destination)
            
            # Log event to MongoDB
            log_event(
                event_type="shipment_created",
                tracking_number=tracking_number,
                status=status,
                user_id=session.get("user"),
                metadata={"origin": origin, "destination": destination}
            )
            
            return redirect("/shipments")
        except Exception as e:
            print(f"Error creating shipment: {e}")
            return "Error creating shipment", 500
    
    # GET request - display all shipments
    try:
        all_shipments = get_all_shipments()
        return render_template("shipments.html", shipments=all_shipments)
    except Exception as e:
        print(f"Error fetching shipments: {e}")
        return "Error loading shipments", 500


@app.route("/api/shipments")
def api_shipments():
    """REST API endpoint returning JSON"""
    try:
        all_shipments = get_all_shipments()
        # Convert datetime objects to strings for JSON serialization
        for shipment in all_shipments:
            if shipment.get('created_at'):
                shipment['created_at'] = shipment['created_at'].isoformat()
        return jsonify(all_shipments), 200
    except Exception as e:
        print(f"Error in API: {e}")
        return jsonify({"error": "Failed to fetch shipments"}), 500


@app.route("/events")
def events():
    # Require login
    if "user" not in session:
        return redirect("/login")
    
    try:
        all_events = get_all_events(limit=50)
        return render_template("events.html", events=all_events)
    except Exception as e:
        print(f"Error fetching events: {e}")
        return "Error loading events", 500


@app.route("/api/events", methods=["GET", "POST"])
def api_events():
    """REST API endpoint for events"""
    if request.method == "GET":
        try:
            all_events = get_all_events(limit=50)
            return jsonify(all_events), 200
        except Exception as e:
            print(f"Error in events API: {e}")
            return jsonify({"error": "Failed to fetch events"}), 500
    
    elif request.method == "POST":
        # Require login for POST
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.get_json(silent=True) or {}
        event_type = data.get("type")
        
        if not event_type:
            return jsonify({"error": "Missing 'type' field"}), 400
        
        try:
            event_id = create_event(
                event_type=event_type,
                user_id=session.get("user"),
                **{k: v for k, v in data.items() if k != 'type'}
            )
            return jsonify({"id": event_id, "status": "created"}), 201
        except Exception as e:
            print(f"Error creating event: {e}")
            return jsonify({"error": "Failed to create event"}), 500


if __name__ == "__main__":
    app.run(debug=True)