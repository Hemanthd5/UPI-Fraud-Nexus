"""
Geolocation module for automatic location detection
Supports both IP-based geolocation and browser-based geolocation
"""

import requests
import logging
from functools import lru_cache

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def get_location_from_ip(ip_address):
    """
    Get location (city, state, country) from IP address using free IP geolocation API
    Falls back to multiple services if one fails
    
    Args:
        ip_address (str): IP address to geolocate
        
    Returns:
        dict: Contains 'city', 'state', 'country', 'latitude', 'longitude'
    """
    
    # Default location if all services fail
    default_location = {
        'city': 'Unknown',
        'state': 'Unknown',
        'country': 'Unknown',
        'latitude': None,
        'longitude': None,
        'source': 'default'
    }
    
    # Skip private/localhost IPs
    if ip_address.startswith(('127.', '192.168.', '10.', '172.')) or ip_address == 'localhost':
        return {
            'city': 'Local Network',
            'state': 'Local',
            'country': 'Local',
            'latitude': None,
            'longitude': None,
            'source': 'local'
        }
    
    # Try multiple IP geolocation services
    services = [
        {
            'url': f'https://ipapi.co/{ip_address}/json/',
            'parser': parse_ipapi_response,
            'timeout': 3
        },
        {
            'url': f'https://ip-api.com/json/{ip_address}?fields=city,regionName,country,lat,lon,status',
            'parser': parse_ip_api_response,
            'timeout': 3
        },
        {
            'url': f'https://ipwho.is/{ip_address}',
            'parser': parse_ipwho_response,
            'timeout': 3
        }
    ]
    
    for service in services:
        try:
            response = requests.get(service['url'], timeout=service['timeout'])
            if response.status_code == 200:
                location = service['parser'](response.json())
                if location['city'] != 'Unknown':
                    location['source'] = 'ip_api'
                    logging.info(f"Successfully determined location from IP: {location['city']}")
                    return location
        except requests.exceptions.Timeout:
            logging.warning(f"Timeout fetching location from {service['url']}")
            continue
        except requests.exceptions.ConnectionError:
            logging.warning(f"Connection error fetching location from {service['url']}")
            continue
        except Exception as e:
            logging.warning(f"Error fetching location from {service['url']}: {e}")
            continue
    
    logging.warning(f"Could not determine location from IP: {ip_address}")
    return default_location


def parse_ipapi_response(data):
    """Parse response from ipapi.co"""
    return {
        'city': data.get('city', 'Unknown'),
        'state': data.get('region', 'Unknown'),
        'country': data.get('country_name', 'Unknown'),
        'latitude': data.get('latitude'),
        'longitude': data.get('longitude'),
        'source': 'ipapi'
    }


def parse_ip_api_response(data):
    """Parse response from ip-api.com"""
    if data.get('status') == 'success':
        return {
            'city': data.get('city', 'Unknown'),
            'state': data.get('regionName', 'Unknown'),
            'country': data.get('country', 'Unknown'),
            'latitude': data.get('lat'),
            'longitude': data.get('lon'),
            'source': 'ip_api'
        }
    return {'city': 'Unknown', 'state': 'Unknown', 'country': 'Unknown', 'latitude': None, 'longitude': None}


def parse_ipwho_response(data):
    """Parse response from ipwho.is"""
    if data.get('success'):
        return {
            'city': data.get('city', 'Unknown'),
            'state': data.get('region', 'Unknown'),
            'country': data.get('country', 'Unknown'),
            'latitude': data.get('latitude'),
            'longitude': data.get('longitude'),
            'source': 'ipwho'
        }
    return {'city': 'Unknown', 'state': 'Unknown', 'country': 'Unknown', 'latitude': None, 'longitude': None}


def get_location_from_coordinates(latitude, longitude):
    """
    Get city and state from latitude/longitude using reverse geocoding (Nominatim)
    
    Args:
        latitude (float): Latitude coordinate
        longitude (float): Longitude coordinate
        
    Returns:
        dict: Contains 'city', 'state', 'country'
    """
    
    default_location = {
        'city': 'Unknown',
        'state': 'Unknown',
        'country': 'Unknown',
        'source': 'default'
    }
    
    if not latitude or not longitude:
        return default_location
    
    try:
        # Using OpenStreetMap's Nominatim service (free, no API key required)
        url = f'https://nominatim.openstreetmap.org/reverse'
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json'
        }
        headers = {'User-Agent': 'UPI-Fraud-Detection/1.0'}
        
        response = requests.get(url, params=params, headers=headers, timeout=3)
        
        if response.status_code == 200:
            data = response.json()
            address = data.get('address', {})
            
            # Extract location components
            city = address.get('city') or address.get('town') or address.get('village') or 'Unknown'
            state = address.get('state') or 'Unknown'
            country = address.get('country') or 'Unknown'
            
            logging.info(f"Reverse geocoding successful: {city}, {state}")
            return {
                'city': city,
                'state': state,
                'country': country,
                'source': 'reverse_geocoding'
            }
    except requests.exceptions.Timeout:
        logging.warning(f"Timeout in reverse geocoding for coordinates: {latitude}, {longitude}")
    except requests.exceptions.ConnectionError:
        logging.warning(f"Connection error in reverse geocoding")
    except Exception as e:
        logging.warning(f"Error in reverse geocoding: {e}")
    
    return default_location


def get_location_from_browser_data(latitude, longitude):
    """
    Wrapper for getting location from browser's geolocation data
    
    Args:
        latitude (float): Browser-provided latitude
        longitude (float): Browser-provided longitude
        
    Returns:
        dict: Location details
    """
    return get_location_from_coordinates(latitude, longitude)


def get_best_location(ip_address=None, latitude=None, longitude=None):
    """
    Determine best location from available sources (priority: browser coords > IP)
    
    Args:
        ip_address (str): IP address
        latitude (float): Browser latitude
        longitude (float): Browser longitude
        
    Returns:
        dict: Best available location
    """
    
    # Priority 1: Use browser coordinates if available
    if latitude and longitude:
        location = get_location_from_coordinates(latitude, longitude)
        if location['city'] != 'Unknown':
            return location
    
    # Priority 2: Fall back to IP-based geolocation
    if ip_address:
        return get_location_from_ip(ip_address)
    
    # Default: return a reasonable default for local dev
    return {
        'city': 'Mumbai',  # Default to Mumbai for India-based UPI system
        'state': 'Maharashtra',
        'country': 'India',
        'source': 'default'
    }
