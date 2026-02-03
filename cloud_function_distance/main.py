import functions_framework
import requests
import os
import time
from functools import lru_cache

# Get API key from environment
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

@lru_cache(maxsize=100)
def get_cached_distance(origin, destination):
    """Get distance and duration with caching"""
    max_retries = 3
    retry_delay = 1
    
    for attempt in range(max_retries):
        try:
            response = requests.get(
                'https://maps.googleapis.com/maps/api/distancematrix/json',
                params={
                    'origins': origin,
                    'destinations': destination,
                    'key': GOOGLE_MAPS_API_KEY
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'OK':
                    rows = data.get('rows', [])
                    if rows and rows[0].get('elements'):
                        element = rows[0]['elements'][0]
                        
                        if element.get('status') == 'OK':
                            distance = element.get('distance', {})
                            duration = element.get('duration', {})
                            
                            distance_km = distance.get('value', 0) / 1000
                            duration_minutes = duration.get('value', 0) / 60
                            
                            return {
                                'success': True,
                                'origin': origin,
                                'destination': destination,
                                'distance_text': distance.get('text', 'N/A'),
                                'distance_km': round(distance_km, 2),
                                'distance_miles': round(distance_km * 0.621371, 2),
                                'duration_text': duration.get('text', 'N/A'),
                                'duration_minutes': round(duration_minutes, 0),
                                'duration_hours': round(duration_minutes / 60, 1),
                                'cached': False
                            }
                        elif element.get('status') == 'ZERO_RESULTS':
                            return {
                                'success': False,
                                'error': f'No route found between {origin} and {destination}'
                            }
                        else:
                            # Route calculation failed
                            error_status = element.get('status', 'Unknown error')
                            if attempt < max_retries - 1:
                                time.sleep(retry_delay * (2 ** attempt))
                                continue
                            return {
                                'success': False,
                                'error': f'Route calculation failed: {error_status}'
                            }
                else:
                    error_msg = data.get('error_message', data.get('status', 'Unknown error'))
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return {
                        'success': False,
                        'error': f'Distance Matrix API error: {error_msg}'
                    }
            else:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                    continue
                return {
                    'success': False,
                    'error': f'HTTP error: {response.status_code}'
                }
                
        except requests.Timeout:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            return {
                'success': False,
                'error': 'Request timeout after retries'
            }
        except requests.RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay * (2 ** attempt))
                continue
            return {
                'success': False,
                'error': f'Request failed: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}'
            }
    
    return {
        'success': False,
        'error': 'Failed after maximum retries'
    }


@functions_framework.http
def distance_eta(request):
    """Calculate distance and ETA between two locations"""
    # Enable CORS
    if request.method == 'OPTIONS':
        headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Max-Age': '3600'
        }
        return ('', 204, headers)

    headers = {
        'Access-Control-Allow-Origin': '*'
    }

    origin = request.args.get('origin')
    destination = request.args.get('destination')
    
    if not origin or not destination:
        return (
            {
                'success': False,
                'error': 'Missing required parameters: origin and destination'
            },
            400,
            headers
        )
    
    origin = origin.strip()
    destination = destination.strip()
    
    if len(origin) < 2 or len(destination) < 2:
        return (
            {
                'success': False,
                'error': 'Origin and destination must be at least 2 characters'
            },
            400,
            headers
        )
    
    if len(origin) > 100 or len(destination) > 100:
        return (
            {
                'success': False,
                'error': 'Origin and destination must be less than 100 characters'
            },
            400,
            headers
        )
    
    invalid_chars = ['<', '>', ';', '"', "'", '\\', '`']
    if any(char in origin for char in invalid_chars) or any(char in destination for char in invalid_chars):
        return (
            {'success': False, 'error': 'Location names contain invalid characters'},
            400,
            headers
        )
    
    result = get_cached_distance(origin, destination)
    
    cache_key = (origin, destination)
    if result.get('success') and cache_key in [
        tuple(k) if isinstance(k, tuple) else k 
        for k in get_cached_distance.cache_info()._asdict()
    ]:
        result['cached'] = True
    
    status_code = 200 if result.get('success') else 400
    
    return (result, status_code, headers)