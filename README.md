# 2024 지역리빙랩 프로젝트 - 최적경로 알고리즘

## 라이브러리 환경

이쁘게 어케쓰징

## 아키텍쳐 구조

아기차낭

## 코드 설명

### input_data.py

데이터를 입력받는 코드입니다. 입력받는 데이터 컬럼은 아래와 같습니다.
(폐기물 이미지 경로, 폐기물 종류, 폐기물 개수, 폐기물 위치)

- 입력 프로세스를 시각화 하게 되면 이미지 경로가 아닌 이미지를 입력받도록 코드가 변경되어야 합니다.
- 입력받은 데이터는 database/waste_data.xlsx에 저장됩니다.

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
Vehicle 0의 경로:
0 Load(9) -> 6 Load(11) -> 5 Load(16) -> 4 Load(20) -> 3 Load(24) -> 2 Load(34) -> 1 Load(43) -> 28 Load(46) -> 27 Load(49) -> 26 Load(51) -> 25 Load(57) -> 24 Load(60) -> 23 Load(69) -> 22 Load(72) -> 21 Load(75) -> 20 Load(85) -> 19 Load(95) -> 18 Load(104) -> 17 Load(105) -> 16 Load(108) -> 15 Load(111) -> 14 Load(113) -> 13 Load(114) -> 12 Load(124) -> 11 Load(128) -> 10 Load(134) -> 9 Load(137) -> 8 Load(139) -> 7 Load(148) -> 0 Load(148)
경로 거리: 0m
경로 적재량: 148

모든 경로의 총 거리: 0m
모든 경로의 총 적재량: 148
```

- 참고 블로그 : https://suddiyo.tistory.com/entry/Python-OpenAI-API-Secret-Key-%EA%B4%80%EB%A6%AC
