import functions_framework
import requests
import os

@functions_framework.http
def distance_eta(request):
    """
    Cloud Function to calculate distance and ETA between two cities using Google Distance Matrix API.
    Accepts: ?origin=CityName&destination=CityName
    Returns: JSON with origin, destination, distance_km, duration_minutes
    """
    # Enable CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        return ('', 204, headers)
    
    headers = {'Access-Control-Allow-Origin': '*'}
    
    # Get origin and destination from query parameters
    origin = request.args.get('origin')
    destination = request.args.get('destination')
    
    if not origin or not destination:
        return ({'error': 'Missing origin or destination parameter'}, 400, headers)
    
    # Get API key from environment variable
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return ({'error': 'API key not configured'}, 500, headers)
    
    # Call Google Distance Matrix API
    try:
        url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={origin}&destinations={destination}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK' and len(data['rows']) > 0:
            element = data['rows'][0]['elements'][0]
            
            if element['status'] == 'OK':
                # Extract distance and duration
                distance_meters = element['distance']['value']
                distance_km = round(distance_meters / 1000, 2)
                
                duration_seconds = element['duration']['value']
                duration_minutes = round(duration_seconds / 60, 2)
                
                result = {
                    'origin': origin,
                    'destination': destination,
                    'distance_km': distance_km,
                    'distance_text': element['distance']['text'],
                    'duration_minutes': duration_minutes,
                    'duration_text': element['duration']['text']
                }
                return (result, 200, headers)
            else:
                return ({'error': f"Could not calculate distance: {element['status']}"}, 404, headers)
        else:
            return ({'error': f"API error: {data['status']}"}, 404, headers)
    
    except Exception as e:
        return ({'error': str(e)}, 500, headers)