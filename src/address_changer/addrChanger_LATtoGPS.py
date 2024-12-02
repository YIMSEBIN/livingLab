import pandas as pd
import requests

from src.secret_key.secrets_manager import get_secret_key

def GPS_to_address(data):
    coordinates = data.apply(lambda row: (row['Latitude'], row['Longitude']), axis=1).tolist()
    print("추출된 좌표 리스트:", coordinates)

    def geocode_address(lat, lon, api_key):
        base_url = "https://dapi.kakao.com/v2/local/geo/coord2address.json"
        headers = {"Authorization": f"KakaoAK {api_key}"}
        params = {"x": lon, "y": lat}
        response = requests.get(base_url, headers=headers, params=params)
        response_json = response.json()
        if response_json['documents']:
            address_info = response_json['documents'][0]['address']
            return address_info['address_name']
        else:
            print(f"Geocoding failed for coordinates ({lat}, {lon})")
            return None

    API_KEY = get_secret_key()

    # 각 좌표를 주소로 변환
    addresses = [geocode_address(lat, lon, API_KEY) for lat, lon in coordinates if lat is not None and lon is not None]

    return addresses
