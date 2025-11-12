import os
import requests
from typing import List, Dict, Optional


class GeocodingSearch:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_MAPS_API_KEY')
        if not self.api_key:
            raise ValueError(
                "API key not provided. Set GOOGLE_MAPS_API_KEY environment variable "
                "or pass api_key parameter"
            )
        self.base_url = "https://maps.googleapis.com/maps/api/geocode/json"

    def search_address(self, keyword: str) -> List[Dict]:
        params = {
            'address': keyword,
            'key': self.api_key
        }
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            if data['status'] == 'OK':
                results = {}
                for result in data['results']:
                    location = result['geometry']['location']
                    results[result['formatted_address']] = (location['lat'], location['lng'])
                return results
            elif data['status'] == 'ZERO_RESULTS':
                print(f"No results found for: {keyword}")
                return {}
            else:
                print(f"Geocoding API error: {data['status']}")
                if 'error_message' in data:
                    print(f"Error message: {data['error_message']}")
                return {}
        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return {}
