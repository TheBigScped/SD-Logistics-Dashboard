import os
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId

def get_mongo_connection():
    """Get MongoDB connection using MONGODB_URI environment variable"""
    mongo_uri = os.environ.get('MONGODB_URI')
    if not mongo_uri:
        raise RuntimeError("MONGODB_URI environment variable is not set")
    
    # Configure SSL/TLS settings for App Engine compatibility
    client = MongoClient(
        mongo_uri,
        tls=True,
        tlsAllowInvalidCertificates=True,  # Allow self-signed certs for App Engine
        connect=False,  # Lazy connection
        serverSelectionTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    db = client.get_database()  # Gets the database specified in the URI
    return db

def log_event(event_type, tracking_number=None, status=None, user_id=None, metadata=None):
    """Log an event to MongoDB events collection"""
    db = get_mongo_connection()
    events_collection = db['events']
    
    event = {
        'type': event_type,
        'timestamp': datetime.utcnow(),
        'user_id': user_id,
        'tracking_number': tracking_number,
        'status': status,
        'metadata': metadata or {}
    }
    
    result = events_collection.insert_one(event)
    return str(result.inserted_id)

def get_all_events(limit=50):
    """Fetch the most recent events from MongoDB"""
    db = get_mongo_connection()
    events_collection = db['events']
    
    # Get events sorted by timestamp (newest first), limited to 50
    events = list(events_collection.find().sort('timestamp', -1).limit(limit))
    
    # Convert ObjectId to string for JSON serialization
    for event in events:
        event['_id'] = str(event['_id'])
        # Convert datetime to ISO format string
        if isinstance(event.get('timestamp'), datetime):
            event['timestamp'] = event['timestamp'].isoformat()
    
    return events

def create_event(event_type, timestamp=None, **kwargs):
    """Create a custom event (for API POST)"""
    db = get_mongo_connection()
    events_collection = db['events']
    
    event = {
        'type': event_type,
        'timestamp': timestamp or datetime.utcnow(),
        **kwargs
    }
    
    result = events_collection.insert_one(event)
    return str(result.inserted_id)