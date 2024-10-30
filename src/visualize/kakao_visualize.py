import pandas as pd
import requests
import folium

from secrets_manager import get_secret_key

# 카카오 API 키 설정 (발급받은 API 키를 입력하세요)
API_KEY = get_secret_key()

# 시점과 종점, 경유지의 위도와 경도 설정 : 오성알씨
start = (36.420924, 127.423353)
end = (36.420924, 127.423353)

# 엑셀 파일 읽기
file_path = '운행기록_88다1348_20240902.xlsx'
address = pd.read_excel(f"docs/LatLon/{file_path}", engine='openpyxl')
waypoints = [(lat, lon) for lat, lon in zip(address['Latitude'], address['Longitude'])]
# waypoints = [
#     (36.315569, 127.346243),     # 경유지 1
#     (36.310511, 127.347090),     # 경유지 2
#     (36.312989, 127.350407),     # 경유지 3
# ]

# 카카오 경로 탐색 API 요청 URL
url = "https://apis-navi.kakaomobility.com/v1/directions"

# 경로 탐색 API 요청
params = {
    'origin': f"{start[1]},{start[0]}",  # 시점 (경도, 위도)
    'destination': f"{end[1]},{end[0]}",  # 종점 (경도, 위도)
    'waypoints': '|'.join([f"{wp[1]},{wp[0]}" for wp in waypoints]),  # 경유지 (경도, 위도)
    'priority': 'RECOMMEND'  # 최적 경로
}
headers = {
    "Authorization": f"KakaoAK {API_KEY}"
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

# folium 지도 초기화 (시작점을 중심으로)
m = folium.Map(location=start, zoom_start=14)

# 시점, 경유지, 종점에 마커 추가
folium.Marker(location=start, popup="Start", icon=folium.Icon(color="green")).add_to(m)
folium.Marker(location=end, popup="End", icon=folium.Icon(color="red")).add_to(m)
for idx, waypoint in enumerate(waypoints, start=1):
    folium.Marker(location=waypoint, popup=f"Waypoint {idx}", icon=folium.Icon(color="blue")).add_to(m)

# 경로 그리기
if data.get('routes'):
    for route in data['routes']:
        for section in route['sections']:
            for road in section['roads']:
                # 경로 좌표 가져오기
                polyline = road['vertexes']
                # 좌표 리스트를 folium에 추가
                coordinates = [(polyline[i+1], polyline[i]) for i in range(0, len(polyline), 2)]
                folium.PolyLine(coordinates, color="blue", weight=5, opacity=0.7).add_to(m)

# 지도를 HTML 파일로 저장
m.save('vehicle_route_kakao.html')

# 결과 출력
print("지도가 'vehicle_route_kakao.html' 파일로 저장되었습니다. 파일을 열어 경로를 확인하세요.")
