import pandas as pd
import folium
from folium import plugins
import math
import requests
import re


class WasteRouteVisualizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.colors = {
            'start': '#27ae60',
            'end': '#c0392b',
            'normal': '#2980b9',
            'route': '#3498db',
        }

    def calculate_adjusted_point(self, center, radius, next_point):
        """
        중심(center), 반지름(radius), 다음 지점(next_point)을 기준으로 원 둘레 위의 특정 점 계산.
        """
        center = (float(center[0]), float(center[1]))
        next_point = (float(next_point[0]), float(next_point[1]))

        # 중심과 다음 지점 간의 각도 계산
        bearing = math.atan2(
            next_point[1] - center[1],
            next_point[0] - center[0]
        )
        
        # 중심에서 반지름 거리만큼 떨어진 지점 계산
        adjusted_point = (
            center[0] + (radius / 111320) * math.cos(bearing),
            center[1] + (radius / (111320 * math.cos(math.radians(center[0])))) * math.sin(bearing)
        )
        return adjusted_point

    def get_route(self, start_coord, end_coord):
        """
        카카오 모빌리티 API를 사용하여 경로 데이터 가져오기.
        """
        url = "https://apis-navi.kakaomobility.com/v1/directions"
        headers = {
            "Authorization": f"KakaoAK {self.api_key}",
            "Content-Type": "application/json"
        }
        params = {
            "origin": f"{start_coord[1]},{start_coord[0]}",
            "destination": f"{end_coord[1]},{end_coord[0]}",
            "priority": "RECOMMEND"
        }
        
        response = requests.get(url, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"경로 요청 실패: {response.status_code}, {response.text}")
            return None

    def visualize(self, input_data, index):
        """
        주소 데이터 기반 시각화
        """
        m = folium.Map(location=[36.3504, 127.3845], zoom_start=13)  # 대전 중심 좌표

        for i in range(len(input_data) - 1):
            current = input_data[i]
            next_point = input_data[i + 1]

            radius = float(current['범위(m)'])
            center_coords = (current['위도'], current['경도'])

            # 조정된 둘레의 지점 계산
            adjusted_coords = self.calculate_adjusted_point(center_coords, radius, (next_point['위도'], next_point['경도']))

            # 원 중심 및 조정된 지점 추가
            folium.Circle(
                location=center_coords,
                radius=radius,
                color=self.colors['normal'],
                fill=True,
                fill_opacity=0.4
            ).add_to(m)

            folium.Marker(
                location=adjusted_coords,
                tooltip=f"조정된 지점: {i + 1}",
                icon=folium.Icon(color='blue')
            ).add_to(m)

            # 경로 생성
            route_data = self.get_route(adjusted_coords, (next_point['위도'], next_point['경도']))
            if route_data and 'routes' in route_data:
                coordinates = []
                for section in route_data['routes'][0].get('sections', []):  # 'sections' 키 체크
                    for road in section.get('roads', []):  # 'roads' 키 체크
                        vertices = road.get('vertexes', [])
                        for j in range(0, len(vertices), 2):
                            coordinates.append((vertices[j+1], vertices[j]))

                if coordinates:
                    folium.PolyLine(
                        coordinates,
                        color=self.colors['route'],
                        weight=3,
                        opacity=0.8,
                        tooltip=f"경로 {i + 1} → {i + 2}"
                    ).add_to(m)
            else:
                # 기본 경로: 두 지점을 직선으로 연결
                print(f"경로 데이터가 없어서 기본 경로를 사용합니다: {adjusted_coords} → {(next_point['위도'], next_point['경도'])}")
                folium.PolyLine(
                    [adjusted_coords, (next_point['위도'], next_point['경도'])],
                    color=self.colors['route'],
                    weight=3,
                    opacity=0.8,
                    tooltip=f"기본 경로 {i + 1} → {i + 2}"
                ).add_to(m)

        # 지도 저장
        m.save(f"store/GPS_map{index}.html")
        print(f"지도 생성 완료: store/GPS_map{index}.html")


def get_coordinates_from_kakao(address, api_key):
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            coords = result['documents'][0]['address']
            return float(coords['y']), float(coords['x'])  # 위도, 경도
    return None, None

def process_address_list(address_list, api_key):
    result = []
    for address in address_list:
        match = re.search(r'\((\d+)m 범위\)', address)  # 반지름 추출
        if match:
            range_m = int(match.group(1))
            base_address = re.sub(r'\(\d+m 범위\)', '', address).strip()
            lat, lng = get_coordinates_from_kakao(base_address, api_key)
            if lat is not None and lng is not None:
                result.append({"위도": lat, "경도": lng, "범위(m)": range_m})
    return result


# 메인 실행
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

# 카카오 API 키
kakao_api_key = "993e67e5f9d2bc70937c00a2eb9964f5"

for i in range(1, 9):
    # 주소 리스트
    data = pd.read_csv(f'store/GPS_address{i}.csv')
    
    # '차량위치' 컬럼의 데이터 추출
    address_list = list(data['차량위치'])

    # 데이터 처리
    processed_data = process_address_list(address_list, kakao_api_key)

    visualizer = WasteRouteVisualizer(kakao_api_key)
    visualizer.visualize(processed_data, i)
