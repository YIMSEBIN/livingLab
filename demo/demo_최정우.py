import streamlit as st
import pandas as pd
import os
from PIL import Image
import torch
import glob
from ultralytics import YOLO
import cv2

def save_image(uploaded_files):
    if not os.path.exists("./data"):
        os.makedirs("./data")

    for file in uploaded_files:
        with open(f"./data/{file.name}", "wb") as f:
            f.write(file.getbuffer())
        st.success(f"{file.name} 저장 완료")


from ultralytics import YOLO


def analyze_images():
    model_path = 'model/best.pt'
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


def main():
    st.set_page_config(
        page_title="폐기물 리스트",
        layout="wide"
    )

    st.title("폐기물 리스트")

    left_col, right_col = st.columns([1, 1])

    with left_col:
        st.markdown("""
            <div style='border: 1px solid #ccc; height: 400px; display: flex; 
            justify-content: center; align-items: center;'>
                <p>지도를<br>생성해주세요</p>
            </div>
            """, unsafe_allow_html=True)

    with right_col:
        table_placeholder = st.empty()
        if 'df' not in st.session_state:
            st.session_state.df = pd.DataFrame(columns=['이미지', '위치', '종류', '신뢰도', '수거여부'])

        st.session_state.df = st.session_state.df.sort_values('이미지')

        # 데이터프레임에서 '수거여부'에 체크박스를 추가
        def render_checkbox(row):
            checked = st.checkbox('', key=f"checkbox_{row.name}", value=row['수거여부'] == '수거')
            return '수거' if checked else '미수거'

        # '수거여부' 열 업데이트
        st.session_state.df['수거여부'] = st.session_state.df.apply(render_checkbox, axis=1)

        # 업데이트된 데이터프레임 표시
        table_placeholder.dataframe(st.session_state.df, width=600, height=400)

    st.markdown("<br>", unsafe_allow_html=True)
    button_container = st.container()
    with button_container:
        col1, col2 = st.columns(2)
        with col1:
            uploaded_files = st.file_uploader(
                "이미지 업로드",
                type=['png', 'jpg', 'jpeg'],
                accept_multiple_files=True,
                key="file_uploader",
                label_visibility="collapsed"
            )
            if st.button("이미지 업로드하기", use_container_width=True):
                if uploaded_files:
                    save_image(uploaded_files)
                    st.session_state.uploaded = True
                else:
                    st.warning("업로드할 이미지를 선택해주세요")

            if 'uploaded' in st.session_state and st.session_state.uploaded:
                st.write("업로드된 이미지:")
                for file in glob.glob('./data/*'):
                    image = Image.open(file)
                    st.image(image, caption=os.path.basename(file), use_column_width=True)

        with col2:
            if st.button("이미지 분석하기", use_container_width=True):
                with st.spinner('이미지 분석 중...'):
                    new_data = analyze_images()
                    st.session_state.df = pd.concat([st.session_state.df, new_data], ignore_index=True)
                    st.session_state.df = st.session_state.df.sort_values('이미지')  # Sort after adding new data
                    st.session_state.analyzed = True

                    # 테이블 업데이트
                    st.session_state.df['수거여부'] = st.session_state.df.apply(render_checkbox, axis=1)
                    table_placeholder.dataframe(st.session_state.df)

                st.success('이미지 분석이 완료되었습니다.')

                if 'analyzed' in st.session_state and st.session_state.analyzed:
                    st.write("분석 결과 이미지:")
                    for img_path in glob.glob('./results/*'):
                        image = Image.open(img_path)
                        st.image(image, caption=os.path.basename(img_path), use_column_width=True)


if __name__ == "__main__":
    main()

