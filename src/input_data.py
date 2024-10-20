import pandas as pd
from pathlib import Path

def input_data() :
    # 엑셀 파일 경로 설정
    db_excel = Path('database/waste_data.xlsx')

    # 엑셀 파일이 존재하는지 확인하고, 없으면 새로운 DataFrame을 생성
    if db_excel.exists():
        df = pd.read_excel(db_excel)
    else:
        df = pd.DataFrame(columns=['이미지', '종류', '개수', '위치'])

    # 입력 데이터 받기
    image_path = input("이미지 경로 : ")
    waste_type = input("폐기물 종류 : ")
    quantity = int(input("폐기물 개수 : "))
    location = input("폐기물의 위치 : ")

    # 입력 받은 데이터를 DataFrame에 추가
    new_data = pd.DataFrame({'이미지': [image_path], 
                                '종류': [waste_type], 
                                '개수': [quantity], 
                                '위치': [location]})
    df = pd.concat([df, new_data], ignore_index=True)

    # 데이터를 엑셀 파일에 저장
    df.to_excel(db_excel, index=False)

    print("데이터 저장 완료")


input_data()