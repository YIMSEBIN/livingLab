# 데이터를 더 추가하여 20개 이상 처리하도록 수정
import pandas as pd

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

    # 결과를 파일로 저장 (선택 사항)
    top_locations.to_csv(f"store/input{i}.csv", index=False, encoding='utf-8-sig')
    print(f"\n결과가 'input{i}.csv' 파일로 저장되었습니다.")
