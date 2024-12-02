from datetime import datetime
import pandas as pd

from src.address_changer.addrChanger_LATtoGPS import GPS_to_address

def putStartData(result, type):
    result.loc[0, 'type'] = type
    result.loc[0, 'count'] = 0
    result.loc[0, 'time'] = datetime.strptime("2000-01-01 03:38:35.642636", "%Y-%m-%d %H:%M:%S.%f")
    result.loc[0, 'image'] = '(유)오성알씨.png'
    result.loc[0, 'score'] = 0

    result['count'] = result['count'].astype(int)
    result['time'] = pd.to_datetime(result['time'], errors = 'coerce')
    return result


def group_and_count(data):
    grouped_data = data.groupby('Image').agg(count=('Image', 'size'), 
                                             Latitude=('Latitude', 'first'),
                                             Longitude=('Longitude', 'first'),
                                             Time=('Time', 'first'),
                                             Type=('Type', 'first'),
                                             Score=('Score', 'mean')).reset_index()
    return grouped_data


def image_to_route_changer() :
    input_path_large = 'results/detection_results_no_pp_bag.csv'
    input_path_pp = 'results/detection_results_no_large_waste.csv'
    output_path_large = 'store/route_input_large.csv'
    output_path_pp = 'store/route_input_pp.csv'

    # csv 파일 읽기
    data = pd.read_csv(f"{input_path_large}", encoding='UTF8')
    data = group_and_count(data)
    data.rename(columns={'Time': 'time', 'Type': 'type', 'Score': 'score', 'Image': 'image'}, inplace=True)

    # # 앞뒤에 (주)오성알씨 주소 추가
    empty_row = pd.DataFrame({col: '' for col in data.columns}, index=[0])
    empty_row['Latitude'] = '36.4216090560865'
    empty_row['Longitude'] = '127.423704564947'
    data = pd.concat([empty_row, data], ignore_index=True)

    # 위경도를 주소로 변환
    address = GPS_to_address(data)
    
    # 결과를 DataFrame에 추가
    data['address'] = address
    data = putStartData(data, "Large Waste Items")

    # 필터링: 'type'이 'Large Waste Items'인 행만 남김
    data = data[data['type'] == 'Large Waste Items']

    # 결과를 새 엑셀 파일로 저장
    data.to_csv(f"{output_path_large}",index=False, encoding='utf-8-sig')
    print(f"store/{output_path_large}.csv 파일을 저장했습니다.")

    
    # csv 파일 읽기
    data = pd.read_csv(f"{input_path_pp}", encoding='UTF8')
    data = group_and_count(data)
    data.rename(columns={'Time': 'time', 'Type': 'type', 'Score': 'score', 'Image': 'image'}, inplace=True)
    
    # # 앞뒤에 (주)오성알씨 주소 추가
    empty_row = pd.DataFrame({col: '' for col in data.columns}, index=[0])
    empty_row['Latitude'] = '36.4216090560865'
    empty_row['Longitude'] = '127.423704564947'
    data = pd.concat([empty_row, data], ignore_index=True)

    # 위경도를 주소로 변환
    address = GPS_to_address(data)
    
    # 결과를 DataFrame에 추가
    data['address'] = address
    data = putStartData(data, "PP bag")

    # 필터링: 'type'이 'PP bag'인 행만 남김
    data = data[data['type'] == 'PP bag']

    # 결과를 새 엑셀 파일로 저장
    data.to_csv(f"{output_path_pp}",index=False, encoding='utf-8-sig')
    print(f"store/{output_path_pp}.csv 파일을 저장했습니다.")
