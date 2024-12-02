import sys
import pandas as pd
import folium
from folium import plugins
import requests
from src.secret_key.secrets_manager import get_secret_key

class WasteRouteVisualizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.colors = {
            'normal': '#2980b9',     # 중간지점 - 파란색
            'highlight': '#f39c12'   # 강조색 - 주황색
        }

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
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"경로 데이터 요청 실패: {e}")
        return None

    def create_popup_content(self, idx, row, point_type="수거 지점"):
        """상세 정보를 포함한 팝업 컨텐츠 생성"""
        waste_summary = []
        total_count = 0
        
        if pd.notna(row['type']) and pd.notna(row['count']):
            count = int(row['count'])
            waste_summary.append(
                f"<tr><td>{row['type']}</td><td class='text-right'>{count}개</td></tr>"
            )
            total_count += count

        time_str = row['time'].strftime('%Y-%m-%d %H:%M')
        
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
            <div class="popup-header">{point_type} #{idx}</div>
            <table class="info-table">
                <tr>
                    <td colspan="2">🕒 {time_str}</td>
                </tr>
                {' '.join(waste_summary)}
                <tr class="total-row">
                    <td>총 폐기물</td>
                    <td class="text-right">{total_count}개</td>
                </tr>
            </table>
        </div>
        """

    def visualize(self, input_csv, output_html):
        """폐기물 수거 경로 시각화 생성"""
        # 데이터 로드 및 전처리
        df = pd.read_csv(input_csv)
        df[['time', 'Latitude', 'Longitude']] = df[['time', 'Latitude', 'Longitude']].ffill()
        df['time'] = pd.to_datetime(df['time'])

        # 지도 초기화
        center_lat = df['Latitude'].astype(float).mean()
        center_lng = df['Longitude'].astype(float).mean()
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=13,
            tiles='cartodbpositron'
        )

        for idx, data in df.iterrows():
            point_type = "수거 지점"
            
            # 마커 추가
            marker = folium.Marker(
                [float(data['Latitude']), float(data['Longitude'])],
                icon=plugins.BeautifyIcon(
                    icon='circle', icon_shape='circle', border_width=3,
                    number=str(idx), background_color='white',
                    border_color='#2980b9', text_color='#2980b9',
                ),
                popup=folium.Popup(
                    self.create_popup_content(idx, data, point_type),
                    max_width=300
                ),
                tooltip=f"{point_type} #{idx}"
            )
            marker.add_to(m)

        # 지도 저장
        m.save(output_html)
        print(f"지도 생성 완료: {output_html}")

def visualize_nodemap() :
    API_KEY = get_secret_key()

    input_path_large = 'store/route_input_large.csv'
    input_path_pp = 'store/route_input_pp.csv'
    output_path_large = 'store/node_map_large.html'
    output_path_pp = 'store/node_map_pp.html'

    visualizer = WasteRouteVisualizer(API_KEY)
    visualizer.visualize(input_path_large, output_path_large)
    visualizer.visualize(input_path_pp, output_path_pp)
