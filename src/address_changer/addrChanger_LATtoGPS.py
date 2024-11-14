import pandas as pd
import requests

def addrChanger_LATtoGPS() :
    # 엑셀 파일 경로
    file_path = './CleanNetAddress.xlsx'

    # 엑셀 파일에서 데이터 읽기
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        print("엑셀 파일 읽기 성공")
    except Exception as e:
        print(f"엑셀 파일 읽기 실패: {e}")


    # 엑셀 파일의 열 이름 확인
    print("엑셀 파일의 열 이름:", df.columns)

    # # 데이터 확인 (앞부분 5개 행 출력)
    # print("엑셀 파일의 데이터 (앞부분 5개 행):")
    # print(df.head())

    # 주소 리스트 추출 (열 이름을 정확히 확인 후 수정하세요)
    addresses = df['Address'].tolist()  # 'Address' 열 이름을 실제 엑셀 파일의 주소 열 이름으로 수정
    print("추출된 주소 리스트:", addresses)

    def geocode_address(address, api_key):
        base_url = "https://dapi.kakao.com/v2/local/search/address.json"
        headers = {"Authorization": f"KakaoAK {api_key}"}
        params = {"query": address}
        response = requests.get(base_url, headers=headers, params=params)
        response_json = response.json()
        if response_json['documents']:
            location = response_json['documents'][0]['address']
            return (address, location['y'], location['x'])  # 위도, 경도
        else:
            print(f"Geocoding failed for address {address}")
            return (address, None, None)

    api_key = 'cac3864be84e85e6bc9f0497ec5ad86d'  # 여기에 실제 API 키를 입력하세요

    # 각 주소를 지리적 좌표로 변환
    coordinates = [geocode_address(address, api_key) for address in addresses if address is not None]

    print("지리적 좌표:", coordinates)
    print(len(coordinates))

    coord_df = pd.DataFrame(coordinates)
    coord_df.columns=['address', 'latitude', 'longitude']
    
    with pd.ExcelWriter(file_path, mode='a', engine='openpyxl') as writer:
        coord_df.to_excel(writer, index=False, startcol=0, startrow=0)