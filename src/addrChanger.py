from datetime import datetime
import pandas as pd

from addrChanger_LATtoGPS import GPS_to_address

def putStartData(result):
    result.loc[0, 'type'] = "대형폐기물"
    result.loc[0, 'count'] = 0
    result.loc[0, 'time'] = datetime.strptime("2000-01-01 03:38:35.642636", "%Y-%m-%d %H:%M:%S.%f")
    result.loc[0, 'image'] = '(유)오성알씨.png'
    result.loc[0, 'score'] = 0

    result.loc[len(result) - 1, 'type'] = "대형폐기물"
    result.loc[len(result) - 1, 'count'] = 0
    result.loc[len(result) - 1, 'time'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    result.loc[len(result) - 1, 'image'] = '(유)오성알씨.png'
    result.loc[len(result) - 1, 'score'] = 0

    result['count'] = result['count'].astype(int)
    result['time'] = pd.to_datetime(result['time'], errors = 'coerce')
    return result

def main() :
    input_file_path = f'store/image_model_output.csv'
    output_file_path= f'store/route_input.csv'

    # csv 파일 읽기
    data = pd.read_csv(f"{input_file_path}", encoding='UTF8')
    
    # # 앞뒤에 (주)오성알씨 주소 추가
    empty_row = pd.DataFrame({col: '' for col in data.columns}, index=[0])
    empty_row['Latitude'] = '36.4216090560865'
    empty_row['Longitude'] = '127.423704564947'
    data = pd.concat([empty_row, data], ignore_index=True)
    data = pd.concat([data, empty_row], ignore_index=True)

    # 위경도를 주소로 변환
    address = GPS_to_address(data)
    
    # 결과를 DataFrame에 추가
    data['address'] = address
    data = putStartData(data)

    # 결과를 새 엑셀 파일로 저장
    data.to_csv(f"{output_file_path}",index=False)
    print(f"store/route_input.csv 파일을 저장했습니다.")

if __name__ == "__main__":
    main()