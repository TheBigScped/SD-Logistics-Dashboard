# SD-Logistics-Dashboard

# Smart Logistics Dashboard

A cloud-based logistics management system built with Flask and Google App Engine.

## Features (planned)
- Shipment management
- Driver assignment
- Event tracking
- Alerts and SLA monitoring
- Firebase authentication
- SQL + NoSQL databases
- Cloud Functions and APIs

## How to run locally
```bash
pip install -r requirements.txt
python main.py

## Deployment
This application is designed to run on Google App Engine (Python runtime).

Deployment steps:
1. Install Google Cloud SDK
2. Authenticate with `gcloud auth login`
3. Set project with `gcloud config set project <project-id>`
4. Deploy using:
   ```bash
   gcloud app deploy