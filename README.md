# 데이터 기반 생활폐기물의 효율적 수거를 위한 최적경로 도출 - 최적경로 알고리즘 코드
- 2024 지역리빙랩 지원사업 프로젝트
- 충남대학교 컴퓨터융합학부 스마트데이터랩
- 프로젝트 기간 :  2024.06 ~ 2024.11

### 최적경로 팀원 구성
| 이관희 | 유준형 | 임세빈 |
| --- | --- | --- |
| SDLab 석사과정 | 경영학부 | 컴퓨터융합학부 |

## 사용 라이브러리 환경
```
pip install pandas
pip install ortools
pip install pathlib
pip install folium
pip install geopy
```

## 아키텍쳐 구조
```
├── README.md
├── .gitignore
├── docs
│    ├── GPS
│    ├── LatLon
│    ├── address.xlsx
│    ├── CleanNetAddress.xlsx
│    └── TrashCost.xlsx
├── src
│    ├── address_changer
│    ├── visualize
│    ├── CVRP.py
│    ├── input_data.py
│    ├── main.py
│    ├── secrets_manager.py
│    └── select_oldest_waste.py
└── store
     ├── address.csv
     ├── distance_matrix.csv
     └── inputData.csv
```

## 상세 설명

### input_data.py

데이터를 입력받는 코드입니다. 입력받는 데이터 컬럼은 아래와 같습니다.

| 폐기물 이미지 경로 | 위치 | 종류 | 개수 | 배출 날짜 |
| --- | --- | --- | --- | --- |
| image | address | trashType | count | date |

- 입력받은 데이터는 store/inputData.xlsx에 저장됩니다.

### select_oldest_waste.py

입력데이터(inputData.csv)에서 배출날짜가 가장 오래된 순으로 상위 n개를 추출합니다.

- FILE_PATH : 입력데이터(inputData.csv) 경로
- top_N : 데이터 추출 개수

### CVRP.py

CVRP 문제를 해결합니다.

- create_data_model : CVRP 문제를 위한 데이터 모델 생성
- create_distance_matrix : 데이터 모델에 사용되는 거리 행렬 생성
- 구글 OR-tools에서 제공하는 CVRP(용량형 차량경로문제) 해결 코드를 참고함.

### address_changer

도로명주소와 위경도 간 주소 변환 코드입니다.

- addrChanger_GPStoLAT.py : 도로명수조를 위경도로 변환.
- addrChanger_LATtoGPS.py : 위경도를 도로명주소로 변환.

### main.py

최적경로 도출을 진행합니다.

- create_data_model에 적절한 파라미터를 제공하여 진행함.
  - DISTANCE_MATRIX_FILE: 거리 행렬을 저장하는 엑셀 파일 경로
  - locations : 폐기물 주소 정보(위경도 dictionary)
  - API_KEY : 거리행렬 생성을 위한 카카오맵 API 키
  - demands : 각 폐기물의 용량(쓰레기 유형에 배정된 cost * 개수) 리스트.
  - vehicle : 폐기물 수거 차량(용량, 수)

## 참고사항

### API KEY 사용방법

1. src/secrets.json 파일 생성

```json
{
  "SECRET_KEY": "your_api_key"
}
```

2. src/secrets_manager.py 내부 함수를 호출해서 API KEY 사용

```python
from secrets_manager import get_secret_key

secret_key = get_secret_key()
```

### 결과 형태 예시

```
Objective: 27081
Vehicle 0의 경로:
 0 Load(13) ->  1 Load(15) ->  3 Load(20) ->  5 Load(22) ->  4 Load(26) ->  2 Load(29) ->  0 Load(29)                                                                        ->  0 Load(29)        
경로 거리: 27081m
경로 적재량: 29

모든 경로의 총 거리: 27081m
모든 경로의 총 적재량: 29
```

- 참고 블로그 : https://suddiyo.tistory.com/entry/Python-OpenAI-API-Secret-Key-%EA%B4%80%EB%A6%AC
