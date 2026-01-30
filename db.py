import os
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime

def get_db_connection():
    """Get database connection using DATABASE_URL environment variable."""
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL environment variable is not set")
    # Neon generally requires SSL
    conn = psycopg2.connect(
        db_url,
        sslmode="require",
        cursor_factory=RealDictCursor
    )
    return conn

def generate_tracking_number():
    """Generate a unique tracking number based on timestamp"""
    # Format: TRK-YYYYMMDD-HHMMSS (e.g., TRK-20260130-143022)
    return f"TRK-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

def get_all_shipments():
    """Fetch all shipments from database."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM shipments ORDER BY created_at DESC")
            return cur.fetchall()
    finally:
        conn.close()

def get_shipment_by_id(shipment_id):
    """Fetch a single shipment by ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM shipments WHERE id = %s", (shipment_id,))
            return cur.fetchone()
    finally:
        conn.close()

def create_shipment(tracking_number, status, origin, destination):
    """Create a new shipment."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO shipments (tracking_number, status, origin, destination)
                VALUES (%s, %s, %s, %s)
                RETURNING id
                """,
                (tracking_number, status, origin, destination)
            )
            shipment_id = cur.fetchone()["id"]
            conn.commit()
            return shipment_id
    finally:
        conn.close()

def update_shipment(shipment_id, status, origin, destination):
    """Update an existing shipment."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE shipments
                SET status = %s, origin = %s, destination = %s
                WHERE id = %s
                RETURNING id
                """,
                (status, origin, destination, shipment_id)
            )
            result = cur.fetchone()
            conn.commit()
            return result is not None
    finally:
        conn.close()

def delete_shipment(shipment_id):
    """Delete a shipment by ID."""
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM shipments WHERE id = %s RETURNING id", (shipment_id,))
            result = cur.fetchone()
            conn.commit()
            return result is not None
    finally:
        conn.close()