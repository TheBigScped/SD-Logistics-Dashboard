import functions_framework
import requests
import os

@functions_framework.http
def geocode_city(request):
    """
    Cloud Function to geocode a city name using Google Maps API.
    Accepts: ?city=CityName
    Returns: JSON with city, lat, lng
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
    
    # Get city from query parameter
    city = request.args.get('city')
    if not city:
        return ({'error': 'Missing city parameter'}, 400, headers)
    
    # Get API key from environment variable
    api_key = os.environ.get('GOOGLE_MAPS_API_KEY')
    if not api_key:
        return ({'error': 'API key not configured'}, 500, headers)
    
    # Call Google Maps Geocoding API
    try:
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={city}&key={api_key}"
        response = requests.get(url)
        data = response.json()
        
        if data['status'] == 'OK' and len(data['results']) > 0:
            location = data['results'][0]['geometry']['location']
            result = {
                'city': city,
                'lat': location['lat'],
                'lng': location['lng'],
                'formatted_address': data['results'][0]['formatted_address']
            }
            return (result, 200, headers)
        else:
            return ({'error': f"Could not geocode city: {city}"}, 404, headers)
    
    except Exception as e:
        return ({'error': str(e)}, 500, headers)