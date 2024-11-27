##  ! 터미널에 "streamlit run app.py" 라고 입력하면 실행됨 

import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np

def save_image(uploaded_files):  # 사용자가 업로드한 이미지를 "./data/"에 저장
    for file in uploaded_files:
        if file.name not in st.session_state.images:
            st.session_state["images"].append(file.name)
            with open(f"./data/{file.name}", "wb") as f:
                f.write(file.getbuffer())
            
                
def main():
    # 페이지 기본 설정
    st.set_page_config(
        page_title="이미지 분석 데모",
        layout="wide"
    )

    # 제목과 설명
    st.title("페기물 리스트")
    
    # 두 개의 컬럼으로 나누기
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # 왼쪽 이미지 업로드 영역
        st.markdown("### 지도를 생성해주세요")
        
        uploaded_files = st.file_uploader("이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if uploaded_files:
            save_image(uploaded_files)
        
        st.write("업로드된 이미지:")
        st.write(st.session_state["images"])
        
        
    with col2:
        # 오른쪽 분석 결과 테이블
        st.markdown("## 폐기물 리스트")
        columns = ["이미지", "위치", "종류", "수거여부"]
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

        # 폐기물 리스트 데이터 표
        for i, row in enumerate(data):
            cols = st.columns([1, 2, 2, 1])
            with cols[0]:
                st.image(row[0], width=70)  # 실제 이미지 URL 사용
            with cols[1]:
                st.write(row[1])
            with cols[2]:
                st.write(row[2])
            with cols[3]:
                st.checkbox("수거 여부", value=row[3], key=f"checkbox_{i}")
                
    
    # 하단 버튼들
    col3, col4 = st.columns(2)
    
    with col3:
        if st.button("이미지 업로드하기", key="upload"):
            st.write("이미지 업로드 기능")
            
    with col4:
        if st.button("이미지 분석하기", key="analyze"):
            st.write("이미지 분석 기능")

if __name__ == "__main__":
    main()