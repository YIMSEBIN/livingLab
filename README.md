# 과제 개요

2024 리빙랩 과제 최적경로 알고리즘

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

- 참고 블로그 : https://suddiyo.tistory.com/entry/Python-OpenAI-API-Secret-Key-%EA%B4%80%EB%A6%AC

### input_data.py

데이터를 입력받는 코드입니다. 입력받는 데이터 컬럼은 아래와 같습니다.
(폐기물 이미지 경로, 폐기물 종류, 폐기물 개수, 폐기물 위치)

- 입력 프로세스를 시각화 하게 되면 이미지 경로가 아닌 이미지를 입력받도록 코드가 변경되어야 합니다.
- 입력받은 데이터는 database/waste_data.xlsx에 저장됩니다.
