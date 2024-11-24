import pandas as pd

# 폐기물 클래스 정의
class Waste:
    def __init__(self, disposal_time, waste_type, quantity, location):
        self.disposal_time = disposal_time  # 폐기 시간
        self.waste_type = waste_type        # 폐기물 종류
        self.quantity = quantity            # 폐기물 개수
        self.location = location            # 폐기물 위치

def select_data(FILE_PATH, top_N) :
    locations_df = pd.read_csv(FILE_PATH, encoding='UTF8')

    # 'date' 열을 datetime 형식으로 변환
    locations_df['time'] = pd.to_datetime(locations_df['time'])

    # '쓰레기 배출 시간' 기준으로 오름차순 정렬
    locations_df = locations_df.sort_values(by='time')

    return locations_df.head(top_N)