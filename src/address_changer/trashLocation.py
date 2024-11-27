from datetime import datetime, timedelta
import random
import pandas as pd

def putRandomData(result):
    for i in range(0, len(result)):
        result.loc[i, 'Latitude'] = ''
        result.loc[i, 'Longitude'] = ''
        result.loc[i, 'type'] = random.choice(["대형폐기물", "pp마대"])
        result.loc[i, 'count'] = random.randint(1, 10)
        result.loc[i, 'time'] = (datetime.now() - timedelta(days=random.randint(0, 365))).strftime("%Y-%m-%d %H:%M:%S.%f")
        result.loc[i, 'image'] = ''
        result.loc[i, 'score'] = random.uniform(0, 1)

    result['count'] = result['count'].astype(int)
    result['time'] = pd.to_datetime(result['time'], errors = 'coerce')
    return result

input_file_path = [
'운행기록_88다1348_20240902',
'운행기록_88다1348_20240905',
'운행기록_88다1348_20240909',
'운행기록_88다1348_20240912',
'운행기록_88다1348_20240919',
'운행기록_88다1348_20240923',
'운행기록_88다1348_20240926',
'운행기록_88다1348_20240930'
]

for i in range(1, 9) :
    # Excel 파일 로드
    df = pd.read_excel(f'docs/GPS/{input_file_path[i-1]}.xlsx', header=3)
    # '차량위치' 컬럼의 데이터 추출
    df = pd.DataFrame(df['차량위치'], columns=['차량위치'])
    
    # 주소와 범위를 분리하여 데이터프레임으로 변환
    df[['address', 'range']] = df['차량위치'].str.extract(r"^(.*)\((\d+m 범위)\)$")

    # 연속된 중복 주소 제거 (shift를 활용)
    df['is_duplicate'] = df['address'].eq(df['address'].shift())
    df = df[~df['is_duplicate']].drop(columns=['is_duplicate']).reset_index(drop=True)

    df.to_csv(f"store/GPS_address{i}.csv", index=False, encoding='utf-8-sig')

    # 방문 횟수 집계
    location_counts = df['address'].value_counts().reset_index()
    location_counts.columns = ['address', 'visit_count']

    # 방문 횟수를 기준으로 상위 20개 추출
    top_locations = location_counts.head(20)['address']

    # 랜덤 데이터 추가
    result = pd.DataFrame(top_locations, columns=['address'])
    result = putRandomData(result)

    # 결과를 파일로 저장
    result.to_csv(f"store/image_model_output{i}.csv", index=False, encoding='utf-8-sig')
    print(f"\n결과가 'image_model_output{i}.csv' 파일로 저장되었습니다.")
