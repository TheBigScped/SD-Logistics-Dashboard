from dotenv import load_dotenv
load_dotenv()

from flask import Flask, render_template, request, redirect, session, jsonify
import firebase_admin
from firebase_admin import credentials, auth
from db import get_all_shipments, create_shipment, generate_tracking_number, update_shipment, delete_shipment, get_shipment_by_id
from mongo_db import log_event, get_all_events, create_event

app = Flask(__name__, template_folder="app/templates")
app.secret_key = "dev-secret"

# Fix for session persistence - use Lax but ensure session commits
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_HTTPONLY'] = True

# Initialize Firebase Admin
cred = credentials.Certificate("firebase-key.json")
firebase_admin.initialize_app(cred)


def validate_shipment_data(status, origin, destination):
    """Validate shipment data"""
    errors = []
    if not status or not status.strip():
        errors.append("Status is required")
    if not origin or not origin.strip():
        errors.append("Origin is required")
    if not destination or not destination.strip():
        errors.append("Destination is required")
    return errors


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
        status = request.form.get("status", "").strip()
        origin = request.form.get("origin", "").strip()
        destination = request.form.get("destination", "").strip()
        
        # Validate input
        errors = validate_shipment_data(status, origin, destination)
        if errors:
            return f"Validation errors: {', '.join(errors)}", 400
        
        # Auto-generate tracking number
        tracking_number = generate_tracking_number()
        
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


@app.route("/api/shipments", methods=["GET", "POST"])
@app.route("/api/shipments/<int:shipment_id>", methods=["GET", "PUT", "DELETE"])
def api_shipments_full(shipment_id=None):
    """REST API endpoint for shipments with full CRUD"""
    
    # GET single shipment
    if request.method == "GET" and shipment_id:
        try:
            shipment = get_shipment_by_id(shipment_id)
            if shipment:
                if shipment.get('created_at'):
                    shipment['created_at'] = shipment['created_at'].isoformat()
                return jsonify(shipment), 200
            else:
                return jsonify({"error": "Shipment not found"}), 404
        except Exception as e:
            print(f"Error fetching shipment: {e}")
            return jsonify({"error": "Failed to fetch shipment"}), 500
    
    # GET all shipments
    if request.method == "GET":
        try:
            all_shipments = get_all_shipments()
            for shipment in all_shipments:
                if shipment.get('created_at'):
                    shipment['created_at'] = shipment['created_at'].isoformat()
            return jsonify(all_shipments), 200
        except Exception as e:
            print(f"Error in API: {e}")
            return jsonify({"error": "Failed to fetch shipments"}), 500
    
    # POST - create new shipment
    if request.method == "POST":
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.get_json(silent=True) or {}
        status = data.get("status", "").strip()
        origin = data.get("origin", "").strip()
        destination = data.get("destination", "").strip()
        
        # Validate
        errors = validate_shipment_data(status, origin, destination)
        if errors:
            return jsonify({"error": ", ".join(errors)}), 400
        
        try:
            tracking_number = generate_tracking_number()
            shipment_id = create_shipment(tracking_number, status, origin, destination)
            
            # Log event
            log_event(
                event_type="shipment_created",
                tracking_number=tracking_number,
                status=status,
                user_id=session.get("user"),
                metadata={"origin": origin, "destination": destination}
            )
            
            return jsonify({"id": shipment_id, "tracking_number": tracking_number, "status": "created"}), 201
        except Exception as e:
            print(f"Error creating shipment: {e}")
            return jsonify({"error": "Failed to create shipment"}), 500
    
    # PUT - update shipment
    if request.method == "PUT" and shipment_id:
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        data = request.get_json(silent=True) or {}
        status = data.get("status", "").strip()
        origin = data.get("origin", "").strip()
        destination = data.get("destination", "").strip()
        
        # Validate
        errors = validate_shipment_data(status, origin, destination)
        if errors:
            return jsonify({"error": ", ".join(errors)}), 400
        
        try:
            success = update_shipment(shipment_id, status, origin, destination)
            if success:
                # Get shipment for event logging
                shipment = get_shipment_by_id(shipment_id)
                if shipment:
                    log_event(
                        event_type="shipment_updated",
                        tracking_number=shipment["tracking_number"],
                        status=status,
                        user_id=session.get("user"),
                        metadata={"origin": origin, "destination": destination}
                    )
                return jsonify({"id": shipment_id, "status": "updated"}), 200
            else:
                return jsonify({"error": "Shipment not found"}), 404
        except Exception as e:
            print(f"Error updating shipment: {e}")
            return jsonify({"error": "Failed to update shipment"}), 500
    
    # DELETE shipment
    if request.method == "DELETE" and shipment_id:
        if "user" not in session:
            return jsonify({"error": "Unauthorized"}), 401
        
        try:
            # Get shipment before deleting
            shipment = get_shipment_by_id(shipment_id)
            
            success = delete_shipment(shipment_id)
            if success:
                if shipment:
                    log_event(
                        event_type="shipment_deleted",
                        tracking_number=shipment["tracking_number"],
                        status=shipment["status"],
                        user_id=session.get("user"),
                        metadata={"origin": shipment["origin"], "destination": shipment["destination"]}
                    )
                return jsonify({"id": shipment_id, "status": "deleted"}), 200
            else:
                return jsonify({"error": "Shipment not found"}), 404
        except Exception as e:
            print(f"Error deleting shipment: {e}")
            return jsonify({"error": "Failed to delete shipment"}), 500


@app.route("/shipments/<int:shipment_id>/update", methods=["POST"])
def update_shipment_route(shipment_id):
    # Require login
    if "user" not in session:
        return redirect("/login")
    
    status = request.form.get("status", "").strip()
    origin = request.form.get("origin", "").strip()
    destination = request.form.get("destination", "").strip()
    
    # Validate input
    errors = validate_shipment_data(status, origin, destination)
    if errors:
        return f"Validation errors: {', '.join(errors)}", 400
    
    try:
        success = update_shipment(shipment_id, status, origin, destination)
        if success:
            # Get shipment details for event logging
            shipment = get_shipment_by_id(shipment_id)
            if shipment:
                # Log event to MongoDB
                log_event(
                    event_type="shipment_updated",
                    tracking_number=shipment["tracking_number"],
                    status=status,
                    user_id=session.get("user"),
                    metadata={"origin": origin, "destination": destination}
                )
            return redirect("/shipments")
        else:
            return "Shipment not found", 404
    except Exception as e:
        print(f"Error updating shipment: {e}")
        return "Error updating shipment", 500


@app.route("/shipments/<int:shipment_id>/delete", methods=["POST"])
def delete_shipment_route(shipment_id):
    # Require login
    if "user" not in session:
        return redirect("/login")
    
    try:
        # Get shipment details before deleting for event logging
        shipment = get_shipment_by_id(shipment_id)
        
        success = delete_shipment(shipment_id)
        if success:
            # Log event to MongoDB
            if shipment:
                log_event(
                    event_type="shipment_deleted",
                    tracking_number=shipment["tracking_number"],
                    status=shipment["status"],
                    user_id=session.get("user"),
                    metadata={"origin": shipment["origin"], "destination": shipment["destination"]}
                )
            return redirect("/shipments")
        else:
            return "Shipment not found", 404
    except Exception as e:
        print(f"Error deleting shipment: {e}")
        return "Error deleting shipment", 500


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