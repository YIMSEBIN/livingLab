import glob
import streamlit as st
import os
import pandas as pd
from streamlit import components
from ultralytics import YOLO
import cv2
import numpy as np
from datetime import datetime

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
            with open(os.path.join("data", file.name), "wb") as f:
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
    base_dir = 'E:/livingLab/livingLab-main/demo'
    model_path = os.path.join(base_dir, 'model/best.pt')  # 모델 경로 수정
    output_dir = os.path.join(base_dir, 'results')
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
        detected_name = f"{os.path.splitext(img_name)[0]}_detected{os.path.splitext(img_name)[1]}"
        output_path = os.path.join(output_dir, detected_name)
        cv2.imwrite(output_path, img)
        st.write(f"이미지 저장 완료: {output_path}")
    
    # DataFrame 생성
    if results:
        df = pd.DataFrame(results)
        
        # results 폴더에 CSV 파일 저장
        # Large Waste Items가 없는 데이터
        df_no_large = df[~df['Type'].str.contains('Large Waste Items', na=False)]
        no_large_path = os.path.join(output_dir, 'detection_results_no_large_waste.csv')
        df_no_large.to_csv(no_large_path, index=False, encoding='utf-8-sig')
        st.write(f"Large Waste Items 제외 CSV 저장 완료: {no_large_path}")
        
        # PP bag이 없는 데이터
        df_no_pp = df[~df['Type'].str.contains('PP bag', na=False)]
        no_pp_path = os.path.join(output_dir, 'detection_results_no_pp_bag.csv')
        df_no_pp.to_csv(no_pp_path, index=False, encoding='utf-8-sig')
        st.write(f"PP bag 제외 CSV 저장 완료: {no_pp_path}")
        
        return df
    else:
        st.warning("검출된 결과가 없습니다.")
        return None

def initalize_state():
    if 'images' not in st.session_state:
        st.session_state['images'] = []
    if 'show_map' not in st.session_state:
        st.session_state['show_map'] = False
    if 'page' not in st.session_state:
        st.session_state['page'] = 1
    if 'analysis_results' not in st.session_state:
        st.session_state['analysis_results'] = None

def main():
    st.set_page_config(page_title="리빙랩 데모", layout="wide")
    st.title("😎 폐기물 수거 최적경로 탐색")
    initalize_state()
    
    # data 디렉토리 생성
    os.makedirs("data", exist_ok=True)
    
    if st.session_state['page'] == 1:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 이미지를 업로드하세요")
            uploaded_files = st.file_uploader(
                label="Choose an image file",
                type=['png', 'jpg', 'jpeg'],
                accept_multiple_files=True
            )
            if uploaded_files:
                save_image(uploaded_files)
            
            if st.session_state['show_map']:
                map_html_file = "store/node_map1.html"
                show_map(map_html_file)

            # 이미지 표시
            if st.session_state["images"]:
                st.write("업로드된 이미지:")
                displayed_images = st.session_state["images"]
                cols = st.columns(min(len(displayed_images), 8))
                for index, image_name in enumerate(displayed_images):
                    with cols[index % 8]:
                        st.image(f'data/{image_name}', width=200)
            
        with col2:
            left, right = st.columns([1, 1])
            with left:
                if st.button("이미지 분석하기"):
                    st.session_state['analysis_results'] = analyze_images()
                    st.session_state['show_map'] = True
                    st.rerun()
            with right:
                if st.button("경로 도출하기"):
                    st.session_state['page'] = 2
                    st.rerun()
                    
            st.markdown("## 폐기물 리스트")

            # 분석 결과 표시
            if st.session_state['analysis_results'] is not None:
                df = st.session_state['analysis_results']
                for _, row in df.iterrows():
                    cols = st.columns([1, 2, 2, 1])
                    with cols[0]:
                        detected_image = f'E:/livingLab/livingLab-main/demo/results/{os.path.splitext(row["Image"])[0]}_detected{os.path.splitext(row["Image"])[1]}'
                        if os.path.exists(detected_image):
                            st.image(detected_image, width=70)
                        else:
                            st.write("이미지 없음")
                    with cols[1]:
                        st.write(f'위도: {row["Latitude"]}, 경도: {row["Longitude"]}')
                    with cols[2]:
                        st.write(row['Type'])
                    with cols[3]:
                        st.write(f'{row["Score"]:.3f}')

    elif st.session_state['page'] == 2:
        if st.button("이전 페이지로 돌아가기"):
            st.session_state['page'] = 1
            st.rerun()
            
        col1, col2 = st.columns([2, 1])

        with col1:
            map_html_file = "store/result1_waste_route_map.html"
            show_map(map_html_file)
            
        with col2:
            st.markdown("## 폐기물 리스트")
            if st.session_state['analysis_results'] is not None:
                df = st.session_state['analysis_results']
                for _, row in df.iterrows():
                    cols = st.columns([1, 2, 2, 1])
                    with cols[0]:
                        detected_image = f'E:/livingLab/livingLab-main/demo/results/{os.path.splitext(row["Image"])[0]}_detected{os.path.splitext(row["Image"])[1]}'
                        if os.path.exists(detected_image):
                            st.image(detected_image, width=70)
                        else:
                            st.write("이미지 없음")
                    with cols[1]:
                        st.write(f'위도: {row["Latitude"]}, 경도: {row["Longitude"]}')
                    with cols[2]:
                        st.write(row['Type'])
                    with cols[3]:
                        st.write(f'{row["Score"]:.3f}')

if __name__ == "__main__":
    main()