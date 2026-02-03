Smart Logistics Dashboard
A cloud-based logistics management application for tracking shipments across SQL and NoSQL databases.
Technology Stack

Backend: Python, Flask
Databases: Neon PostgreSQL, MongoDB Atlas
Cloud Platform: Google App Engine
Authentication: Firebase (Google OAuth + Email/Password)
Serverless: Google Cloud Functions (Geocoding, Distance Matrix)

Deployment
Live Application: https://sd-logistics-486104.nw.r.appspot.com
Local Setup

Install dependencies:

bashpip install -r requirements.txt

Configure environment variables in .env:

MONGODB_URI=your_mongodb_connection_string
GOOGLE_MAPS_API_KEY=your_api_key

Add Firebase credentials (firebase-key.json)
Run locally:

bashpython main.py
Testing
Run unit tests:
bashpytest test_app.py -v
Features

Full CRUD operations on shipments (PostgreSQL)
Event logging with MongoDB
Firebase authentication with email whitelist
Google Cloud Functions integration
RESTful API with rate limiting
Input validation and security controls

Project Structure

main.py - Flask application and routes
db.py - PostgreSQL database operations
mongo_db.py - MongoDB operations
test_app.py - Unit tests (20 tests)
app/templates/ - HTML templates
cloud_functions/ - Geocoding Cloud Function
cloud_function_distance/ - Distance calculation Cloud Function