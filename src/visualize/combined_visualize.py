import pandas as pd
import folium
from folium import plugins
import branca
import requests
import re
from secrets_manager import get_secret_key


class CombinedRouteVisualizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.colors = {
            'route1': '#3498db',  # 파란색
            'route2': '#e74c3c',   # 빨간색
            'start': '#27ae60',      # 시작점 - 초록색
            'end': '#c0392b',        # 종료점 - 빨간색
            'normal': '#2980b9',     # 중간지점 - 파란색
            'route': '#3498db',      # 경로선 - 밝은 파란색
            'highlight': '#f39c12'   # 강조색 - 주황색
        }

    
    def create_popup_content(self, order, group, total_waste, point_type="수거 지점"):
        """상세 정보를 포함한 팝업 컨텐츠 생성"""
        waste_summary = []
        total_count = 0

        for _, row in group.iterrows():
            if pd.notna(row['폐기물종류']) and pd.notna(row['폐기물개수']):
                count = int(row['폐기물개수'])
                waste_summary.append(
                    f"<tr><td>{row['폐기물종류']}</td><td class='text-right'>{count}개</td></tr>"
                )
                total_count += count

        # '쓰레기확인시간'이 datetime으로 변환된 것을 전제
        time_str = "-"
        if pd.notna(group.iloc[0]['쓰레기확인시간']):
            time_str = group.iloc[0]['쓰레기확인시간'].strftime('%Y-%m-%d %H:%M')

        return f"""
        <div class="popup-content">
            <style>
                .popup-content {{
                    font-family: 'Malgun Gothic', sans-serif;
                    padding: 10px;
                    min-width: 200px;
                }}
                .popup-header {{
                    font-size: 16px;
                    font-weight: bold;
                    margin-bottom: 10px;
                    color: {self.colors['highlight']};
                }}
                .info-table {{
                    width: 100%;
                    border-collapse: collapse;
                }}
                .info-table td {{
                    padding: 3px 0;
                }}
                .text-right {{
                    text-align: right;
                }}
                .total-row {{
                    border-top: 2px solid #ddd;
                    font-weight: bold;
                }}
            </style>
            <div class="popup-header">{point_type} #{order}</div>
            <table class="info-table">
                <tr>
                    <td colspan="2">🕒 {time_str}</td>
                </tr>
                {''.join(waste_summary)}
                <tr class="total-row">
                    <td>총 폐기물</td>
                    <td class="text-right">{total_count}개</td>
                </tr>
            </table>
        </div>
        """


    def create_legend(self, colormap):
        """지도 범례 생성"""
        legend_html = colormap.to_step(index=[1, 2, 3, 4, 5])._repr_html_()
        return f"""
        <div style="position: fixed; 
                    bottom: 50px; right: 50px; 
                    background: white;
                    padding: 10px;
                    border-radius: 5px;
                    box-shadow: 0 0 15px rgba(0,0,0,0.2);
                    font-family: 'Malgun Gothic', sans-serif;
                    z-index: 1000;">
            <div style="font-weight: bold; margin-bottom: 5px;">수거 경로 안내</div>
            <div><span style="color: {self.colors['start']};">●</span> 시작 지점</div>
            <div><span style="color: {self.colors['normal']};">●</span> 수거 지점</div>
            <div><span style="color: {self.colors['end']};">●</span> 종료 지점</div>
            <div><span style="color: {self.colors['route']};">━━</span> 이동 경로</div>
            <div style="margin-top: 5px; border-top: 1px solid #ddd; padding-top: 5px;">
                <div style="font-weight: bold; margin-bottom: 3px;">총 폐기물 수량</div>
                {legend_html}
            </div>
        </div>
        """

        
    def create_colormap(self, df):
        """폐기물 개수에 따른 컬러맵 생성"""
        total_waste = df.groupby('수거순서')['폐기물개수'].sum()
        colormap = branca.colormap.LinearColormap(
            colors=['#f1c40f', '#e67e22', '#e74c3c'],
            vmin=total_waste.min(),
            vmax=total_waste.max()
        )
        return colormap, total_waste

    def get_route(self, start_coord, end_coord):
        """카카오 모빌리티 API를 사용하여 경로 데이터 가져오기"""
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

    def visualize_combined_routes(self, route1_data, route2_data, output_html, marker_data):
        """두 경로를 하나의 지도에 시각화"""
        # 지도 초기화
        m = folium.Map(location=[36.3504, 127.3845], zoom_start=13, tiles='cartodbpositron')

        # 첫 번째 경로 (파란색)
        self.add_route_to_map(route1_data, m, 'route1')

        # 두 번째 경로 (빨간색)
        self.add_route_to_map(route2_data, m, 'route2')
        
        # 컬러맵 생성
        colormap, total_waste = self.create_colormap(marker_data)
        self.add_marker(m, marker_data, total_waste)
        
        # 범례 추가
        m.get_root().html.add_child(folium.Element(self.create_legend(colormap)))
        # 지도 저장
        m.save(output_html)
        print(f"지도 생성 완료: {output_html}")

    def add_route_to_map(self, route_data, map_obj, color_key):
        """경로 데이터를 지도에 추가"""
        for i in range(len(route_data) - 1):
            current = route_data[i]
            next_point = route_data[i + 1]

            start_coords = (current['위도'], current['경도'])
            end_coords = (next_point['위도'], next_point['경도'])

            route_response = self.get_route(start_coords, end_coords)
            if route_response and 'routes' in route_response:
                coordinates = []
                for section in route_response['routes'][0].get('sections', []):
                    for road in section.get('roads', []):
                        vertices = road.get('vertexes', [])
                        for j in range(0, len(vertices), 2):
                            coordinates.append((vertices[j + 1], vertices[j]))
                folium.PolyLine(
                    coordinates,
                    color=self.colors[color_key],
                    weight=3,
                    opacity=0.8,
                    tooltip=f"경로 {i + 1} → {i + 2}"
                ).add_to(map_obj)
            else:
                print(f"경로 데이터가 없어 기본 경로를 사용합니다: {start_coords} → {end_coords}")
                folium.PolyLine(
                    [start_coords, end_coords],
                    color=self.colors[color_key],
                    weight=3,
                    opacity=0.8,
                    tooltip=f"기본 경로 {i + 1} → {i + 2}"
                ).add_to(map_obj)
            
    def add_marker(self, map, marker_data, total_waste) :

        total_points = marker_data['수거순서'].nunique()

        for idx, (order, group) in enumerate(marker_data.groupby('수거순서')):
            point_type = "시작 지점" if order == 1 else "종료 지점" if order == total_points else "수거 지점"
            color = (self.colors['start'] if order == 1 
                    else self.colors['end'] if order == total_points 
                    else self.colors['normal'])
            
            first_row = group.iloc[0]
            
            # 마커 추가
            folium.Marker(
                [float(first_row['위도']), float(first_row['경도'])],
                icon=plugins.BeautifyIcon(
                    icon='circle' if order in [1, total_points] else 'arrow-down',
                    icon_shape='circle',
                    border_width=3,
                    number=str(order),
                    background_color=color if order in [1, total_points] else 'white',
                    border_color=color,
                    text_color='white' if order in [1, total_points] else color,
                    inner_icon_style=f"color:{'white' if order in [1, total_points] else color};"
                ),
                popup=folium.Popup(
                    self.create_popup_content(order, group, total_waste[order], point_type),
                    max_width=300
                ),
                tooltip=f"{point_type} #{order}"
            ).add_to(map)


def load_gps_address_data(file_path, api_key):
    """GPS 주소 데이터를 로드"""
    data = pd.read_csv(file_path)
    address_list = list(data['차량위치'])
    processed_data = []

    for address in address_list:
        match = re.search(r'\((\d+)m 범위\)', address)
        if match:
            range_m = int(match.group(1))
            base_address = re.sub(r'\(\d+m 범위\)', '', address).strip()
            lat, lng = get_coordinates_from_kakao(base_address, api_key)
            if lat is not None and lng is not None:
                processed_data.append({"위도": lat, "경도": lng, "범위(m)": range_m})

    return processed_data



def load_result_data(file_path):
    """폐기물 수거 경로 데이터를 로드"""
    df = pd.read_csv(file_path).iloc[:-2]

    # 데이터 타입 변환: '쓰레기확인시간'을 datetime 형식으로 변환
    if '쓰레기확인시간' in df.columns:
        df['쓰레기확인시간'] = pd.to_datetime(df['쓰레기확인시간'], errors='coerce')

    # 결측값 처리
    df[['수거순서', '위도', '경도']] = df[['수거순서', '위도', '경도']].ffill()
    df['수거순서'] = df['수거순서'].astype(int)
    df = df.sort_values(by=['수거순서'])
    
    route_data = df.drop_duplicates('수거순서')[['위도', '경도']].to_dict('records')
    return route_data, df



def get_coordinates_from_kakao(address, api_key):
    """카카오 API를 사용하여 주소의 위도/경도 가져오기"""
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {"query": address}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        result = response.json()
        if result['documents']:
            coords = result['documents'][0]['address']
            return float(coords['y']), float(coords['x'])
    return None, None

# 메인 실행
API_KEY = get_secret_key()

# 첫 번째 경로 데이터 로드
route1_data = load_gps_address_data('store/GPS_address1.csv', API_KEY)

# 두 번째 경로 데이터 로드
route2_data, marker_data = load_result_data('store/result1.csv')

# 경로 시각화
visualizer = CombinedRouteVisualizer(API_KEY)
visualizer.visualize_combined_routes(route1_data, route2_data, 'store/combined_routes_map.html', marker_data)
