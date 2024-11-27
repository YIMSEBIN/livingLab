import os
import json
import sys
import requests

def get_secret_key(filename='secrets.json', primary_key='SECRET_KEY_Junhyeong', fallback_key='SECRET_KEY_Sebin'):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    file_path = os.path.join(script_dir, filename)

    try:
        with open(file_path, 'r') as file:
            secrets = json.load(file)

        primary_secret = secrets.get(primary_key)
        fallback_secret = secrets.get(fallback_key)

        # 먼저 primary_secret로 요청
        if primary_secret and test_api_key(primary_secret):
            print('현재 사용중인 API KEY : Junhyeong')
            return primary_secret

        # primary_secret 실패 시 fallback_secret 반환
        if fallback_secret and test_api_key(fallback_secret):
            print('현재 사용중인 API KEY : Sebin')
            return fallback_secret

        print("ERROR: 모든 키가 유효하지 않음.")
        return None

    except FileNotFoundError:
        print(f"ERROR: {filename} 파일을 찾을 수 없음.")
        return None
    except json.JSONDecodeError:
        print(f"ERROR: {filename} 파일은 유효한 JSON 형식이 아님.")
        return None

def test_api_key(api_key):
    """
    주어진 API 키를 테스트하는 함수. 
    여기서는 Kakao REST API에 대해 샘플 요청을 시뮬레이션.
    """
    url = "https://apis-navi.kakaomobility.com/v1/directions?origin=127.11015314141542,37.39472714688412&destination=127.10824367964793,37.401937080111644&priority=RECOMMEND"
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }
    
    try:
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return True  # 유효한 키
        else:
            print(f"키 테스트 실패: 상태 코드 {response.status_code}")
            return False  # 잘못된 키
    except requests.RequestException as e:
        print(f"HTTP 요청 에러: {e}")
        return False
