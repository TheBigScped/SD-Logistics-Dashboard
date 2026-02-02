import functions_framework
import requests
import os
import time
from functools import lru_cache

# Get API key from environment
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')

@lru_cache(maxsize=100)
def get_cached_geocode(city):
    """
    Get geocoding data with caching to reduce API calls
    """
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # Make request with timeout
            response = requests.get(
                'https://maps.googleapis.com/maps/api/geocode/json',
                params={
                    'address': city,
                    'key': GOOGLE_MAPS_API_KEY
                },
                timeout=5  # 5 second timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if geocoding was successful
                if data.get('status') == 'OK' and data.get('results'):
                    result = data['results'][0]
                    location = result['geometry']['location']
                    
                    # Return cleaned, structured data
                    return {
                        'success': True,
                        'city': city,
                        'latitude': location['lat'],
                        'longitude': location['lng'],
                        'formatted_address': result.get('formatted_address', city),
                        'place_id': result.get('place_id', ''),
                        'cached': False
                    }
                elif data.get('status') == 'ZERO_RESULTS':
                    return {
                        'success': False,
                        'error': f'No results found for city: {city}'
                    }
                else:
                    # API returned error status
                    error_msg = data.get('error_message', data.get('status', 'Unknown error'))
                    if attempt < max_retries - 1:
                        # Exponential backoff: 1s, 2s, 4s
                        time.sleep(retry_delay * (2 ** attempt))
                        continue
                    return {
                        'success': False,
                        'error': f'Geocoding API error: {error_msg}'
                    }
            else:
                # HTTP error
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
def geocode_city(request):
    """
    HTTP Cloud Function to geocode a city name
    Enhanced with validation, retry logic, caching, and error handling
    """
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

    # Input validation
    city = request.args.get('city')
    
    if not city:
        return (
            {'success': False, 'error': 'Missing required parameter: city'},
            400,
            headers
        )
    
    # Validate city name length
    city = city.strip()
    if len(city) < 2:
        return (
            {'success': False, 'error': 'City name too short (minimum 2 characters)'},
            400,
            headers
        )
    
    if len(city) > 100:
        return (
            {'success': False, 'error': 'City name too long (maximum 100 characters)'},
            400,
            headers
        )
    
    # Check for invalid characters
    invalid_chars = ['<', '>', ';', '"', "'", '\\', '`']
    if any(char in city for char in invalid_chars):
        return (
            {'success': False, 'error': 'City name contains invalid characters'},
            400,
            headers
        )
    
    # Get geocoding data (with caching and retry logic)
    result = get_cached_geocode(city)
    
    # Mark if result was from cache
    if result.get('success') and city in get_cached_geocode.cache_info()._asdict():
        result['cached'] = True
    
    # Return appropriate status code
    status_code = 200 if result.get('success') else 400
    
    return (result, status_code, headers)