from datetime import datetime, timedelta
import random
import pandas as pd
import re
import requests
from secret_key.secrets_manager import get_secret_key

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

# 카카오 API를 사용하여 주소를 위도와 경도로 변환하는 함수
def geocode_address(address_list):
    API_KEY = get_secret_key()
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {API_KEY}"}
    lat_lon = []
    
    for address in address_list:
        params = {"query": address}
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            result = response.json()
            if result['documents']:
                location = result['documents'][0]
                lat_lon.append((float(location['y']), float(location['x'])))
            else:
                lat_lon.append((None, None))  # 주소를 찾을 수 없는 경우
        else:
            lat_lon.append((None, None))  # 요청 실패 시
    return lat_lon

def putStartData(result):
    result.loc[0, 'type'] = "대형폐기물"
    result.loc[0, 'count'] = 0
    result.loc[0, 'time'] = datetime.strptime("2000-01-01 03:38:35.642636", "%Y-%m-%d %H:%M:%S.%f")
    result.loc[0, 'image'] = ''
    result.loc[0, 'score'] = 0

    result.loc[len(result) - 1, 'type'] = "대형폐기물"
    result.loc[len(result) - 1, 'count'] = 0
    result.loc[len(result) - 1, 'time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    result.loc[len(result) - 1, 'image'] = ''
    result.loc[len(result) - 1, 'score'] = 0

    result['count'] = result['count'].astype(int)
    result['time'] = pd.to_datetime(result['time'], errors = 'coerce')
    return result

def addrChangerToLAT(input_file_path, output_file_path):

    # csv 파일 읽기
    data = pd.read_csv(f"{input_file_path}", encoding='UTF8')

    # '차량위치' 열에서 주소 읽기 (주소 형식 확인 필요)
    data['address'] = clean_address(data['address'])
    
    # # 앞뒤에 (주)오성알씨 주소 추가
    empty_row = pd.DataFrame({col: '' for col in data.columns}, index=[0])
    empty_row['address'] = '대전 대덕구 상서당3길 16'
    data = pd.concat([empty_row, data], ignore_index=True)
    data = pd.concat([data, empty_row], ignore_index=True)

    # 주소를 위도와 경도로 변환
    coordinates = geocode_address(data['address'])

    # 결과를 DataFrame에 추가
    result = data
    result['address'] = data['address']
    result['Latitude'], result['Longitude'] = zip(*coordinates)

    result = putStartData(result)

    # 결과를 새 엑셀 파일로 저장
    result.to_csv(f"{output_file_path}",index=False, encoding='utf-8-sig')

for i in range(1, 9) :
    addrChangerToLAT(f'store/image_model_output{i}.csv',f'store/route_input{i}.csv',)
    print(f"store/route_input{i}.csv 파일을 저장했습니다.")
