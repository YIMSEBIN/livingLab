from datetime import datetime, timedelta
import random
import pandas as pd
import re
import requests

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
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK 993e67e5f9d2bc70937c00a2eb9964f5"}
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


def putRandomData(result):

    # 0번째와 -1번째 행을 고정값으로 설정
    result.loc[0, 'type'] = "대형폐기물"
    result.loc[0, 'count'] = 0
    result.loc[0, 'time'] = datetime.strptime("2000-01-01 03:38:35.642636", "%Y-%m-%d %H:%M:%S.%f")

    result.loc[len(result) - 1, 'type'] = "대형폐기물"
    result.loc[len(result) - 1, 'count'] = 0
    result.loc[len(result) - 1, 'time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

    # 1번째부터 len(result) - 2번째까지 랜덤 값 채우기
    for i in range(1, len(result) - 1):
        result.loc[i, 'type'] = random.choice(["대형폐기물", "pp마대"])
        result.loc[i, 'count'] = random.randint(1, 10)
        result.loc[i, 'time'] = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d %H:%M:%S.%f")

    result['count'] = result['count'].astype(int)
    result['time'] = pd.to_datetime(result['time'], errors = 'coerce')
    return result

def addrChangerToLAT(input_file_path, output_file_path):
    # csv 파일 읽기
    data = pd.read_csv(f"{input_file_path}", encoding='UTF8')

    # '차량위치' 열에서 주소 읽기 (주소 형식 확인 필요)
    addresses = clean_address(data['address'])
    
    # 앞뒤에 (주)오성알씨 주소 추가
    addresses = pd.concat([pd.Series(['대전 대덕구 상서당3길 16']), addresses], ignore_index=True)
    addresses = pd.concat([addresses, pd.Series(['대전 대덕구 상서당3길 16'])], ignore_index=True)

    # 주소를 위도와 경도로 변환
    coordinates = geocode_address(addresses)

    # 결과를 DataFrame에 추가
    result = pd.DataFrame()
    result['address'] = addresses
    result['Latitude'], result['Longitude'] = zip(*coordinates)

    result = putRandomData(result)

    # 결과를 새 엑셀 파일로 저장
    result.to_csv(f"{output_file_path}",index=False)

for i in range(1, 9) :
    addrChangerToLAT(f'store/input{i}.csv',f'store/output{i}.csv',)
    print(f"store/output{i}.csv 파일을 저장했습니다.")
