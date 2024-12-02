##  ! 터미널에 "streamlit run app.py" 라고 입력하면 실행됨 

import glob
import time
import numpy as np
import streamlit as st
import os
import pandas as pd
from datetime import datetime
from streamlit import components
from ultralytics import YOLO
import cv2

from src.address_changer.addrChanger import image_to_route_changer
from src.main import make_route
from src.visualize.visualize_nodes import visualize_nodemap
from src.visualize.visualize_routes import visualize_routemap

# 카테고리 매핑 정의
category_mapping = {
    # Large Waste Items
    'arcade machine': 'Large Waste Items',
    'Audio': 'Large Waste Items',
    'Computer': 'Large Waste Items',
    'fax machine': 'Large Waste Items',
    'Main unit': 'Large Waste Items',
    'Monitor': 'Large Waste Items',
    'Printer': 'Large Waste Items',
    'sewing machine': 'Large Waste Items',
    'Speaker': 'Large Waste Items',
    'typewriter': 'Large Waste Items',
    'Vacuum cleaner': 'Large Waste Items',
    'Video player': 'Large Waste Items',
    'Bathtub': 'Large Waste Items',
    'Sink': 'Large Waste Items',
    'Kitchen sink': 'Large Waste Items',
    'Toilet bowl': 'Large Waste Items',
    'Bed': 'Large Waste Items',
    'Bookcase': 'Large Waste Items',
    'Bookstand': 'Large Waste Items',
    'Cabinet': 'Large Waste Items',
    'chair': 'Large Waste Items',
    'Cupboard': 'Large Waste Items',
    'Desk': 'Large Waste Items',
    'Dining table': 'Large Waste Items',
    'Display cabinet': 'Large Waste Items',
    'Display stand': 'Large Waste Items',
    'Drawer unit': 'Large Waste Items',
    'Shoe rack': 'Large Waste Items',
    'Small cabinet': 'Large Waste Items',
    'Sofa': 'Large Waste Items',
    'Table': 'Large Waste Items',
    'TV stand': 'Large Waste Items',
    'Vanity table': 'Large Waste Items',
    'Wardrobe': 'Large Waste Items',
    'Air conditioner': 'Large Waste Items',
    'Air purifier': 'Large Waste Items',
    'dish dryer': 'Large Waste Items',
    'Electric rice cooker': 'Large Waste Items',
    'Fan': 'Large Waste Items',
    'Gas oven range': 'Large Waste Items',
    'Heater': 'Large Waste Items',
    'Humidifier': 'Large Waste Items',
    'Microwave': 'Large Waste Items',
    'refrigerator': 'Large Waste Items',
    'Spin dryer': 'Large Waste Items',
    'TV': 'Large Waste Items',
    'Washing machine': 'Large Waste Items',
    'Aquarium': 'Large Waste Items',
    'Bamboo mat': 'Large Waste Items',
    'Bedding items': 'Large Waste Items',
    'bicycle': 'Large Waste Items',
    'Carpet': 'Large Waste Items',
    'Clothes drying rack': 'Large Waste Items',
    'Coat rack': 'Large Waste Items',
    'Door panel': 'Large Waste Items',
    'Earthenware jar': 'Large Waste Items',
    'Floor covering': 'Large Waste Items',
    'Frame': 'Large Waste Items',
    'lumber': 'Large Waste Items',
    'Mannequin': 'Large Waste Items',
    'Mat': 'Large Waste Items',
    'Piano': 'Large Waste Items',
    'Rice storage container': 'Large Waste Items',
    'Signboard': 'Large Waste Items',
    'Stroller': 'Large Waste Items',
    'Wall clock': 'Large Waste Items',
    'Water tank': 'Large Waste Items',
    'audio cabinet': 'Large Waste Items',
    'suitcase': 'Large Waste Items',
    
    # 기타 카테고리
    'PP bag': 'PP bag',
    'General waste bag': 'General Waste',
    'waste pile': 'General Waste',
    'CleanNet': 'CleanNet',
    'General Waste': 'General Waste'
}

def calculate_iou(box1, box2):
    """Calculate Intersection over Union between two boxes"""
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i < x1_i or y2_i < y1_i:
        return 0.0
    
    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0

def non_max_suppression(boxes, scores, classes, iou_threshold=0.5):
    """Apply Non-Maximum Suppression to remove overlapping detections"""
    if len(boxes) == 0:
        return [], [], []
        
    selected_indices = []
    indices = np.argsort(scores)[::-1]
    
    while len(indices) > 0:
        current_idx = indices[0]
        selected_indices.append(current_idx)
        
        if len(indices) == 1:
            break
            
        ious = [calculate_iou(boxes[current_idx], boxes[idx]) for idx in indices[1:]]
        indices = indices[1:][np.array(ious) < iou_threshold]
    
    return [boxes[i] for i in selected_indices], [scores[i] for i in selected_indices], [classes[i] for i in selected_indices]

def get_bbox_color(class_name, confidence):
    """Get bounding box color based on class and confidence threshold"""
    mapped_class = category_mapping.get(class_name, class_name)
    
    if mapped_class == 'Large Waste Items':
        return (0, 255, 0) if confidence > 0.4 else (0, 0, 255)
    elif mapped_class == 'PP bag':
        return (0, 255, 0) if confidence > 0.5 else (0, 0, 255)
    else:
        return (255, 255, 255)

def parse_location_from_filename(filename):
    parts = filename.split('-')
    if len(parts) >= 5:
        lat = float(f"{parts[1]}.{parts[2]}")
        lon = float(f"{parts[3]}.{parts[4].split('_')[0]}")
        return lat, lon
    return None, None

def parse_time_from_filename(filename):
    time_str = filename[:12]
    try:
        return datetime.strptime(time_str, '%Y%m%d%H%M').strftime('%Y-%m-%d %H:%M:%S')
    except:
        return None

def save_image(uploaded_files):
    for file in uploaded_files:
        if file.name not in st.session_state.images:
            st.session_state["images"].append(file.name)
            with open(f"./data/{file.name}", "wb") as f:
                f.write(file.getbuffer())

def show_map(html_file):
    """HTML 파일을 스트림릿에서 불러와 표시합니다."""
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            html_content = f.read()
            components.v1.html(html_content, height=600, scrolling=True)
    else:
        st.error("지도 파일을 찾을 수 없습니다.")

def analyze_images():
    # base_dir = 'E:/livingLab/livingLab-main/demo'
    # model_path = os.path.join(base_dir, 'model/best.pt')  # 모델 경로 수정
    model_path = 'model/best.pt'
    # output_dir = os.path.join(base_dir, 'results')
    output_dir = 'results'
    os.makedirs(output_dir, exist_ok=True)
    
    # 모델 파일 존재 여부 확인
    if not os.path.exists(model_path):
        st.error(f"모델 파일을 찾을 수 없습니다: {model_path}")
        return None
        
    model = YOLO(model_path)
    results = []
    process_times = []
    
    # st.session_state에 있는 업로드된 이미지만 처리
    for img_name in st.session_state.images:
        img_path = os.path.join("data", img_name)
        if not os.path.exists(img_path):
            st.error(f"이미지 파일을 찾을 수 없습니다: {img_path}")
            continue
        
        # 이미지 로드 및 추론
        prediction = model.predict(source=img_path, save=False)[0]
        img = cv2.imread(img_path)
        if img is None:
            st.error(f"이미지를 불러올 수 없습니다: {img_path}")
            continue
        
        process_times.append({
            'preprocess': prediction.speed['preprocess'],
            'inference': prediction.speed['inference'],
            'postprocess': prediction.speed['postprocess']
        })
        
        boxes = []
        scores = []
        class_names = []
        
        for pred in prediction.boxes.data:
            x1, y1, x2, y2, conf, cls = pred
            boxes.append([x1.item(), y1.item(), x2.item(), y2.item()])
            scores.append(conf.item())
            class_names.append(model.names[int(cls.item())])
        
        filtered_boxes, filtered_scores, filtered_classes = non_max_suppression(
            boxes, scores, class_names, iou_threshold=0.5
        )
        
        lat, lon = parse_location_from_filename(img_name)
        time = parse_time_from_filename(img_name)
        
        for cls, conf, box in zip(filtered_classes, filtered_scores, filtered_boxes):
            mapped_class = category_mapping.get(cls, cls)
            
            # 바운딩 박스 그리기
            x1, y1, x2, y2 = map(int, box)
            color = get_bbox_color(cls, conf)
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f'{cls} {conf:.2f}'
            cv2.putText(img, label, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            results.append({
                'Latitude': lat,
                'Longitude': lon,
                'Time': time,
                'Type': mapped_class,
                'Score': round(conf, 3),
                'Image': img_name
            })
        
        # 결과 이미지 저장
        # detected_name = f"{os.path.splitext(img_name)[0]}_detected{os.path.splitext(img_name)[1]}"
        detected_name = f"{os.path.splitext(img_name)[0]}{os.path.splitext(img_name)[1]}"
        output_path = os.path.join(output_dir, detected_name)
        cv2.imwrite(output_path, img)
        print(f"이미지 저장 완료: {output_path}")
    
    # DataFrame 생성
    if results:
        df = pd.DataFrame(results)
        
        # results 폴더에 CSV 파일 저장
        # Large Waste Items가 없는 데이터
        df_no_large = df[~df['Type'].str.contains('Large Waste Items', na=False)]
        no_large_path = os.path.join(output_dir, 'detection_results_no_large_waste.csv')
        df_no_large.to_csv(no_large_path, index=False, encoding='utf-8-sig')
        print(f"Large Waste Items 제외 CSV 저장 완료: {no_large_path}")
        
        # PP bag이 없는 데이터
        df_no_pp = df[~df['Type'].str.contains('PP bag', na=False)]
        no_pp_path = os.path.join(output_dir, 'detection_results_no_pp_bag.csv')
        df_no_pp.to_csv(no_pp_path, index=False, encoding='utf-8-sig')
        print(f"PP bag 제외 CSV 저장 완료: {no_pp_path}")
        
        return df
    else:
        st.warning("검출된 결과가 없습니다.")
        return None


def initalize_state() : 
    if 'page' not in st.session_state:
        st.session_state['page'] = 1
    if 'images' not in st.session_state:
        st.session_state['images'] = []
    if 'route_input_path' not in st.session_state:
        st.session_state['route_input_path'] = 'store/route_input.csv'
    if 'type_choice' not in st.session_state:
        st.session_state['type_choice'] = None
    if 'show_nodemap' not in st.session_state :
        st.session_state['show_nodemap'] = False
    if 'nodemap_path' not in st.session_state :
        st.session_state['nodemap_path'] = 'store/empty_map.html'

def make_route_map() :
    make_route()
    type = "Large Waste Items" if st.session_state['type_choice']=='대형폐기물' else "PP bag"
    visualize_routemap(type)

def initalize_checkbox_state() :
    if 'pp_selection_status' not in st.session_state:
        data = pd.read_csv('store/route_input_pp.csv')
        st.session_state['pp_selection_status'] = [True] * len(data)
    if 'large_selection_status' not in st.session_state:
        data = pd.read_csv('store/route_input_large.csv')
        st.session_state['large_selection_status'] = [True] * len(data)

# 폐기물 종류 state에 따라 최적경로 input path를 변경하는 유틸함수.
def change_type_state(type_choice) :
    st.session_state['type_choice'] = type_choice
    
    if type_choice == '대형폐기물':
        st.session_state['route_input_path'] = 'store/route_input_large.csv'
        st.session_state['nodemap_path'] = 'store/node_map_large.html'
    elif type_choice == 'pp마대':
        st.session_state['route_input_path'] = 'store/route_input_pp.csv'
        st.session_state['nodemap_path'] = 'store/node_map_pp.html'
    else:
        st.session_state['route_input_path'] = 'store/route_input.csv'
        st.session_state['nodemap_path'] = 'store/empty_map.html'
    st.rerun()


def main():
    st.set_page_config(page_title="리빙랩 데모", layout="wide")
    st.title("😎 페기물 수거 최적경로 탐색")
    initalize_state()

    ##############
    ### PAGE 1 ###
    ##############
    if st.session_state['page'] == 1:

        ## 오른쪽 버튼 Layout ##
        col1, col2 = st.columns([1, 1])

        with col2:
            cols = st.columns([3, 1, 1, 1])

            with cols[1]:
                if st.button("이미지 분석하기"):
                    analyze_images()
                    image_to_route_changer()
                    visualize_nodemap()
                    time.sleep(1)
                    initalize_checkbox_state()
                    st.session_state['show_nodemap'] = True
                    st.rerun()

            with cols[2]:
                if st.button("경로 도출하기"):
                    route_input_path = st.session_state['route_input_path']
                    type_choice = st.session_state['type_choice']
                    route_input_df = pd.read_csv(route_input_path)
                    if type_choice == '대형폐기물':
                        selected_df = route_input_df[st.session_state['large_selection_status']]
                    elif type_choice == 'pp마대':
                        selected_df = route_input_df[st.session_state['pp_selection_status']]
                        
                    selected_df.to_csv('store/route_input_after_demo.csv', index=False)
                    make_route_map()
                    st.session_state['page'] = 2
                    st.rerun()

            with cols[3]: 
                type = ['대형폐기물', 'pp마대']
                current_choice = st.selectbox('폐기물 종류', type, label_visibility="collapsed")
                previous_choice = st.session_state['type_choice']

                if current_choice != previous_choice:
                    change_type_state(current_choice)


        ## 지도 / 리스트 Layout ##
        col1, col2 = st.columns([1, 1])

        with col1:
            
            ## 지도 Section
            map_html_file = 'store/empty_map.html'
            if st.session_state['show_nodemap']:
                map_html_file = st.session_state['nodemap_path']
            show_map(map_html_file)

            ## 이미지 업로드 Section
            uploaded_files = st.file_uploader(label="Choose an image file", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
            if uploaded_files:
                save_image(uploaded_files)

            ## 이미지 미리보기 Section
            if st.session_state["images"]:
                st.write("업로드된 이미지:")
                displayed_images = st.session_state["images"]
                cols = st.columns(min(len(displayed_images), 8))  # 최대 8열로 표시
                for index, image_name in enumerate(displayed_images):
                    with cols[index % 8]:
                        st.image(f'data/{image_name}', width=200)
            
        with col2:
            st.markdown("### ✅ 폐기물 리스트")
            st.markdown('<hr style="margin-top: 0rem; margin-bottom: 0rem;"/>', unsafe_allow_html=True)

            if st.session_state['show_nodemap']:
                trash_data = pd.read_csv(st.session_state['route_input_path'])

                ## 폐기물 리스트 헤더 Section
                cols = st.columns([1, 30, 1, 25, 1, 15, 1, 15, 1])
                with cols[1]:
                    st.markdown('<p style="margin: 0;"><strong>이미지</strong></p>', unsafe_allow_html=True)
                with cols[3]:
                    st.markdown('<p style="margin: 0;"><strong>주소</strong></p>', unsafe_allow_html=True)
                with cols[5]:
                    st.markdown('<p style="margin: 0;"><strong>폐기물 종류</strong></p>', unsafe_allow_html=True)
                with cols[7]:
                    st.markdown('<p style="margin: 0;"><strong>수거여부</strong></p>', unsafe_allow_html=True)
                st.markdown('<hr style="margin-top: 0rem;"/>', unsafe_allow_html=True)

                ## 폐기물 리스트 바디 Section
                for i, row in trash_data.iterrows():
                    # 1번, 끝번 데이터는 (유)오성알씨.
                    if i == 0 :
                        continue
                    
                    # 리스트 (이미지, 주소, 폐기물 종류, 수거여부)
                    cols = st.columns([1, 30, 1, 25, 1, 15, 1, 15, 1])
                    with cols[1]:
                        st.image(f'results/{row["image"]}', width=1000)
                    with cols[3]:
                        st.write(f'{row["address"]}')
                    with cols[5]:
                        st.markdown(f'<div style="display: flex; align-items: center; height: 100%;">{row["type"]}</div>', unsafe_allow_html=True)
                    with cols[7]:
                        checkbox_label = f"Select {row['type']} at {row['address']}"
                        if st.session_state['type_choice'] == '대형폐기물' :
                            checkbox_value =  st.session_state['large_selection_status']
                        elif st.session_state['type_choice'] == 'pp마대' :
                            checkbox_value =  st.session_state['pp_selection_status']
                        is_selected = st.checkbox(checkbox_label, key=i, value=checkbox_value[i], label_visibility="collapsed")
                        if is_selected != checkbox_value[i] :
                            checkbox_value[i] = is_selected

                    # 각 데이터 아래 선
                    st.markdown('<hr style="margin-top: 0.5rem;"/>', unsafe_allow_html=True)

            else : 
                st.write("이미지를 먼저 분석해주세요.")


    ##############
    ### PAGE 2 ###
    ##############
    elif st.session_state['page'] == 2:
        if st.button("이전 페이지로 돌아가기"):
            st.session_state['page'] = 1
            st.rerun()

        col1, col2 = st.columns([2, 1])

        data = pd.read_csv('store/result.csv')
        df = data[:-2]

        with col1:
            map_html_file = 'store/result_map.html'
            show_map(map_html_file)

        with col2:
            st.markdown("## 폐기물 수거 경로")

            # 테이블 데이터 준비
            table_data = df[['수거순서', '이미지', '위치', '폐기물종류', '쓰레기확인시간']].copy()

            table_data['쓰레기확인시간'] = pd.to_datetime(table_data['쓰레기확인시간']).dt.strftime('%Y-%m-%d %H:%M:%S')
            table_data = table_data[['수거순서', '이미지', '위치', '폐기물종류', '쓰레기확인시간']]

            # 테이블 표시 (인덱스 숨김)
            st.dataframe(table_data, hide_index=True)


if __name__ == "__main__":
    main()
