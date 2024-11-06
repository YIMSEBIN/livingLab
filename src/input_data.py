import pandas as pd
from pathlib import Path

def input_data() :
    # 엑셀 파일 경로 설정
    db_excel = Path('store/inputData.csv')

    # 엑셀 파일이 존재하는지 확인하고, 없으면 새로운 DataFrame을 생성
    if db_excel.exists():
        df = pd.read_csv(db_excel, encoding='cp949')
    else:
        df = pd.DataFrame(columns=['image', 'address', 'trashType', 'count', 'date'])

    # 입력 데이터 받기
    image_path = input("이미지 경로 : ")
    location = input("폐기물의 위치 : ")
    waste_type = input("폐기물 종류(쉼표로 구분해주세요.) : ")
    quantity = input("폐기물 개수(쉼표로 구분해주세요.) : ")
    date = input("폐기물 배출 날짜 : ")

    # 입력 받은 데이터를 DataFrame에 추가
    new_data = pd.DataFrame({'image': [image_path],
                                'address': [location], 
                                'trashType': [waste_type], 
                                'count': [quantity],
                                'date': [date]})
    df = pd.concat([df, new_data], ignore_index=True)

    # 데이터를 엑셀 파일에 저장
    df.to_excel(db_excel, index=False)

    print("데이터 저장 완료")