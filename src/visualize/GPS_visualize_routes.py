import pandas as pd
import folium
from folium import plugins
import math
import requests
import re

from secret_key.secrets_manager import get_secret_key


class WasteRouteVisualizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.colors = {
            'start': '#27ae60',  # 시작점 - 초록색
            'end': '#c0392b',    # 종료점 - 빨간색
            'normal': '#2980b9', # 중간지점 - 파란색
            'route': '#3498db',  # 경로선 - 밝은 파란색
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

    def add_markers_from_csv(self, map_obj, marker_data):
        """
        store/result1.csv 데이터를 기반으로 마커 추가
        """
        for idx, (order, group) in enumerate(marker_data.groupby('수거순서')):
            point_type = "시작 지점" if order == 1 else "종료 지점" if idx == len(marker_data['수거순서'].unique()) - 1 else "수거 지점"
            color = (self.colors['start'] if order == 1
                     else self.colors['end'] if point_type == "종료 지점"
                     else self.colors['normal'])

            first_row = group.iloc[0]

            # 마커 추가
            folium.Marker(
                location=[float(first_row['위도']), float(first_row['경도'])],
                icon=plugins.BeautifyIcon(
                    icon='circle' if point_type in ["시작 지점", "종료 지점"] else 'arrow-down',
                    icon_shape='circle',
                    border_width=3,
                    number=str(order),
                    background_color=color,
                    border_color=color
                ),
                popup=f"{point_type} #{order}",
                tooltip=f"{point_type} #{order}"
            ).add_to(map_obj)

    def visualize(self, input_data, marker_data, index):
        """
        주소 데이터 기반 시각화
        """
        m = folium.Map(location=[36.3504, 127.3845], zoom_start=13, tiles='cartodbpositron')  # 대전 중심 좌표

        for i in range(len(input_data) - 1):
            current = input_data[i]
            next_point = input_data[i + 1]

            radius = float(current['범위(m)'])
            center_coords = (current['위도'], current['경도'])

            # 조정된 둘레의 지점 계산
            adjusted_coords = self.calculate_adjusted_point(center_coords, radius, (next_point['위도'], next_point['경도']))

            # 경로 생성
            route_data = self.get_route(adjusted_coords, (next_point['위도'], next_point['경도']))
            if route_data and 'routes' in route_data:
                coordinates = []
                for section in route_data['routes'][0].get('sections', []):
                    for road in section.get('roads', []):
                        vertices = road.get('vertexes', [])
                        for j in range(0, len(vertices), 2):
                            coordinates.append((vertices[j + 1], vertices[j]))

                if coordinates:
                    folium.PolyLine(
                        coordinates,
                        color=self.colors['route'],
                        weight=3,
                        opacity=0.8,
                        tooltip=f"경로 {i + 1} → {i + 2}"
                    ).add_to(m)
            else:
                print(f"경로 데이터가 없어 기본 경로를 사용합니다: {adjusted_coords} → {(next_point['위도'], next_point['경도'])}")
                folium.PolyLine(
                    [adjusted_coords, (next_point['위도'], next_point['경도'])],
                    color=self.colors['route'],
                    weight=3,
                    opacity=0.8,
                    tooltip=f"기본 경로 {i + 1} → {i + 2}"
                ).add_to(m)

        # store/result1.csv 데이터를 기반으로 마커 추가
        self.add_markers_from_csv(m, marker_data)

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


def load_marker_data(file_path):
    """store/result1.csv 데이터를 로드"""
    df = pd.read_csv(file_path).iloc[:-2]
    df['수거순서'] = df['수거순서'].astype(int)
    return df


# 메인 실행
API_KEY = get_secret_key()

# 첫 번째 경로 데이터 로드
for i in range(1, 9):
    # 주소 리스트
    data = pd.read_csv(f'store/GPS_address{i}.csv')
    address_list = list(data['차량위치'])
    processed_data = process_address_list(address_list, API_KEY)

    # 마커 데이터 로드
    marker_data = load_marker_data('store/result1.csv')

    # 지도 시각화
    visualizer = WasteRouteVisualizer(API_KEY)
    visualizer.visualize(processed_data, marker_data, i)
