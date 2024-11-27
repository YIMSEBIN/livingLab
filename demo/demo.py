import streamlit as st

# 페이지 제목
st.title("폐기물 경로 생성 페이지")

# 좌측: 생성된 지도
st.subheader("생성된 지도")
st.write("(폐기물 위치가 핀으로 찍혀있음)")
st.empty()  # 지도를 삽입할 자리

# 우측: 폐기물 리스트
st.subheader("폐기물 리스트")
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

# 버튼: 경로 만들기
if st.button("경로 만들기"):
    st.write("경로를 생성합니다...")

# 아래: 이미지 업로드 및 분석
st.subheader("이미지 업로드 및 분석")
uploaded_file = st.file_uploader("이미지 업로드하기", type=["jpg", "png", "jpeg"])

if uploaded_file is not None:
    st.image(uploaded_file, caption="업로드된 이미지", use_column_width=True)

if st.button("이미지 분석하기"):
    st.write("이미지를 분석합니다...")
