import pandas as pd
import folium
from folium import plugins
import branca
import requests
from src.secret_key.secrets_manager import get_secret_key

class WasteRouteVisualizer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.colors = {
            'start': '#27ae60',      # 시작점 - 초록색
            'end': '#c0392b',        # 종료점 - 빨간색
            'normal': '#2980b9',     # 중간지점 - 파란색
            'route': '#3498db',      # 경로선 - 밝은 파란색
            'highlight': '#f39c12'   # 강조색 - 주황색
        }
        
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
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            print(f"경로 데이터 요청 실패: {e}")
        return None

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
                {' '.join(waste_summary)}
                <tr class="total-row">
                    <td>총 폐기물</td>
                    <td class="text-right">{total_count}개</td>
                </tr>
            </table>
        </div>
        """

    def create_legend(self, colormap):
        """지도 범례 생성"""
        legend_html = colormap.to_step(index=[1, 2, 3, 4, 5, 6])._repr_html_()
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
            <div><span style="color: {self.colors['end']};">●</span> 시작 및 종료 지점</div>
            <div><span style="color: {self.colors['normal']};">●</span> 수거 지점</div>
            <div><span style="color: {self.colors['route']};">━━</span> 이동 경로</div>
            <div style="margin-top: 5px; border-top: 1px solid #ddd; padding-top: 5px;">
                <div style="font-weight: bold; margin-bottom: 3px;">폐기물 존재 확률</div>
                {legend_html}
            </div>
        </div>
        """


    def visualize(self, input_csv, output_html):
        """폐기물 수거 경로 시각화 생성"""
        # 데이터 로드 및 전처리
        df = pd.read_csv(input_csv).iloc[:-2]
        df[['수거순서', '쓰레기확인시간', '위도', '경도']] = df[['수거순서', '쓰레기확인시간', '위도', '경도']].ffill()
        df['쓰레기확인시간'] = pd.to_datetime(df['쓰레기확인시간'])
        df['수거순서'] = df['수거순서'].astype(int)
        df = df.sort_values(by=['수거순서', '쓰레기확인시간'])

        # 컬러맵 생성
        colormap, total_waste = self.create_colormap(df)

        # 지도 초기화
        center_lat = df['위도'].astype(float).mean()
        center_lng = df['경도'].astype(float).mean()
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=13,
            tiles='cartodbpositron'
        )

        # 마커 및 경로 추가
        total_points = df['수거순서'].nunique()
        unique_points = df.drop_duplicates('수거순서')

        for idx, (order, group) in enumerate(df.groupby('수거순서')):
            point_type = "시작 지점" if order == 1 else "종료 지점" if order == total_points else "수거 지점"
            color = (self.colors['start'] if order == 1 
                    else self.colors['end'] if order == total_points 
                    else self.colors['normal'])
            # print(colormap.rgb_hex_str(1))
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
            ).add_to(m)

            # 경로 추가
            if idx < len(unique_points) - 1:
                start = (first_row['위도'], first_row['경도'])
                next_point = unique_points.iloc[idx + 1]
                end = (next_point['위도'], next_point['경도'])
                
                route_data = self.get_route(start, end)
                if route_data and 'routes' in route_data:
                    try:
                        coordinates = []
                        for section in route_data['routes'][0]['sections']:
                            for road in section['roads']:
                                vertices = road['vertexes']
                                for i in range(0, len(vertices), 2):
                                    coordinates.append((vertices[i+1], vertices[i]))
                        
                        folium.PolyLine(
                            coordinates,
                            color=self.colors['route'],
                            weight=3,
                            opacity=0.8,
                            tooltip=f"구간 {order} → {order + 1}"
                        ).add_to(m)
                    except Exception as e:
                        print(route_data)
                        print(f"경로 처리 중 오류 발생: {e}")
                        print("출발지와 도착지가 5m 이내인 경우는 경로 표시가 없어도 괜찮은 수준임.")

        # 범례 추가
        m.get_root().html.add_child(folium.Element(self.create_legend(colormap)))
        
        # 지도 저장
        m.save(output_html)
        print(f"지도 생성 완료: {output_html}")

def visualize_routemap() :
    API_KEY = get_secret_key()

    input_csv_path = f"store/result.csv"
    output_html_path = f"store/result_waste_route_map.html"

    visualizer = WasteRouteVisualizer(API_KEY)
    visualizer.visualize(input_csv_path, output_html_path)