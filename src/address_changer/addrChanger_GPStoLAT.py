import os
import pandas as pd
import re
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

def addrChanger_GPStoLAT() :
    gps_directory = "docs/GPS/"
    output_directory = "docs/LatLon/"

    # 출력 디렉토리 생성 (없을 경우)
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    # 모든 xlsx 파일 처리
    for file in os.listdir(gps_directory):
        if file.endswith('.xlsx'):
            print(f"Start {file}")
            process_file(file, gps_directory, output_directory)
            print(f"Processed {file}")


# 주소에서 "(00m 범위)" 부분 제거하는 함수
def delete_paren(address) :
    # 정규 표현식을 사용하여 괄호와 그 내용을 제거
    cleaned_address = re.sub(r'\(\d+m 범위\)', '', address).strip()
    return cleaned_address

# 주소 중복제거
def clean_address(addresses):
    addresses = addresses.apply(delete_paren)
    unique_addresses = []
    previous_address = None
    
    for current_address in addresses:
        if current_address != previous_address:
            unique_addresses.append(current_address)
        previous_address = current_address
    unique_addresses = pd.Series(unique_addresses)
    return unique_addresses

# Geopy를 사용하여 주소를 위도와 경도로 변환하는 함수
def geocode_address(address_list):
    geolocator = Nominatim(user_agent="South Korea")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
    lat_lon = []
    for address in address_list:
        location = geocode(address)
        if location :
            lat_lon.append((location.latitude, location.longitude))
        else:
            lat_lon.append((None, None))
    return lat_lon

def process_file(file_path, gps_directory, output_directory):
    # 엑셀 파일 읽기
    data = pd.read_excel(f"{gps_directory}{file_path}", engine='openpyxl', header = 3)

    # '차량위치' 열에서 주소 읽기 (주소 형식 확인 필요)
    addresses = clean_address(data['차량위치'])
    # 주소를 위도와 경도로 변환
    coordinates = geocode_address(addresses)

    # 결과를 DataFrame에 추가
    result = pd.DataFrame()
    result['address'] = addresses
    result['Latitude'], result['Longitude'] = zip(*coordinates)

    # 결과를 새 엑셀 파일로 저장
    result.to_excel(f"{output_directory}{file_path}",index=False)
