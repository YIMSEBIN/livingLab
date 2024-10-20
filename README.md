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
openai.api_key = secret_key
```

- 참고 블로그 : https://suddiyo.tistory.com/entry/Python-OpenAI-API-Secret-Key-%EA%B4%80%EB%A6%AC
