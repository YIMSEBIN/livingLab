##  ! 터미널에 "streamlit run app.py" 라고 입력하면 실행됨 

import glob
import streamlit as st
import os
import pandas as pd
from streamlit import components
from ultralytics import YOLO
import cv2

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
    model_path = 'model/best.pt'
    # 모델 파일 존재 여부 확인
    if not os.path.exists(model_path):
        return None
    model = YOLO(model_path)

    image_files = glob.glob('./data/*')
    results = []

    for img_path in image_files:
        # 이미지 로드 및 추론
        prediction = model(img_path)

        # 원본 이미지 로드
        img = cv2.imread(img_path)

        for pred in prediction[0].boxes.data:
            x1, y1, x2, y2, conf, cls = pred
            results.append({
                '이미지': os.path.basename(img_path),
                '위치': f'({x1:.2f}, {y1:.2f}, {x2:.2f}, {y2:.2f})',
                '종류': model.names[int(cls)],
                '신뢰도': f'{conf:.2f}',
                '수거여부': '미수거'
            })

            # 바운딩 박스 그리기
            cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            label = f"{model.names[int(cls)]}: {conf:.2f}"
            cv2.putText(img, label, (int(x1), int(y1) - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 결과 이미지 저장
        cv2.imwrite(f"./results/{os.path.basename(img_path)}", img)

    return pd.DataFrame(results)

def initalize_state() : 
    if 'images' not in st.session_state:
        st.session_state['images'] = []
    if 'show_map' not in st.session_state :
        st.session_state['show_map'] = False
    if 'page' not in st.session_state:
        st.session_state['page'] = 1  # 첫 번째 페이지로 초기화

data = [
    [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Plastic_bottles_ready_for_recycling.jpg/640px-Plastic_bottles_ready_for_recycling.jpg",
        "대전 유성구 궁동99",
        "PP마대",
        False
    ],
    [
        "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Litter_in_Budapest.jpg/640px-Litter_in_Budapest.jpg",
        "대전 유성구 궁동99",
        "대형폐기물, PP마대",
        True
    ],
]

def main():
    st.set_page_config(page_title="리빙랩 데모", layout="wide")
    st.title("😎 페기물 수거 최적경로 탐색")
    initalize_state()
    
    if st.session_state['page'] == 1:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### 이미지를 업로드하세요")
            uploaded_files = st.file_uploader(label="Choose an image file", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
            if uploaded_files:
                save_image(uploaded_files)
            
            if st.session_state['show_map']:
                map_html_file = "store/node_map1.html"  # 예시 파일 이름
                show_map(map_html_file)

            # 이미지 표시
            if st.session_state["images"]:
                st.write("업로드된 이미지:")
                displayed_images = st.session_state["images"]
                cols = st.columns(min(len(displayed_images), 8))  # 최대 3열로 표시
                for index, image_name in enumerate(displayed_images):
                    with cols[index % 8]:
                        st.image(f'data/{image_name}', width=200)
            
        with col2:
            left, right = st.columns([1, 1])  # 비율을 조정하여 버튼 위치 변경 가능
            with left:
                if st.button("이미지 분석하기"):
                    # analyze_images()
                    st.session_state['show_map'] = True
                    st.rerun()
            with right:
                if st.button("경로 도출하기"):
                    st.session_state['page'] = 2
                    st.rerun()
                    
            st.markdown("## 폐기물 리스트")

            # CSV 파일 읽기
            if st.session_state['show_map']:

                data = pd.read_csv('store/route_input.csv')
            
                for i, row in data.iterrows():
                    cols = st.columns([1, 2, 2, 1])
                    with cols[0]:
                        st.image(f'data/{row['image']}', width=70)  # 이미지 URL 혹은 경로
                    with cols[1]:
                        st.write(row['address'])
                    with cols[2]:
                        st.write(row['type'])
                    with cols[3]:
                        st.write(row['score'])

    elif st.session_state['page'] == 2:
        if st.button("이전 페이지로 돌아가기"):
            st.session_state['page'] = 1
            st.rerun()
            
        col1, col2 = st.columns([2, 1])

        with col1:
            map_html_file = "store/result1_waste_route_map.html"  # 예시 파일 이름
            show_map(map_html_file)
            
        with col2:
            st.markdown("## 폐기물 리스트")
            # CSV 파일 읽기
            if os.path.exists('route_input.csv'):
                data = pd.read_csv('route_input.csv')
            
                for i, row in data.iterrows():
                    cols = st.columns([1, 2, 2, 1])
                    with cols[0]:
                        st.image(row['image'], width=70)  # 이미지 URL 혹은 경로
                    with cols[1]:
                        st.write(row['address'])
                    with cols[2]:
                        st.write(row['type'])
                    with cols[3]:
                        st.write(row['score'])


if __name__ == "__main__":
    main()
