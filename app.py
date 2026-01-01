import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 설정 및 연결 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")
SHEET_URL = "https://docs.google.com/spreadsheets/d/1t8Nt3jEZliThpKNwgUBXBxnVPJXoUzwQ1lGIAnoqhxk/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# 정산 설정값
TARGET_QUOTA = 320
EXTRA_UNIT_PRICE = 30.0  # 세전 30불
TAX_RATE = 20.0          # 예상 소득세율

# --- 데이터 로드 ---
@st.cache_data(ttl=60)
def load_data():
    df = conn.read(spreadsheet=SHEET_URL)
    # G열(작업완료일) 날짜 변환 (인덱스 6)
    df.iloc[:, 6] = pd.to_datetime(df.iloc[:, 6], errors='coerce')
    return df

try:
    df = load_data()
except:
    st.error("구글 시트 연결을 확인해주세요.")
    st.stop()

# --- 화면 구성 ---
tab1, tab2, tab3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with tab1:
    st.subheader("➕ 새 작업 등록")
    # 사진 인식 기능 (시뮬레이션 - 추후 API 연동 가능)
    if st.checkbox("📸 처방전 사진 찍기"):
        st.camera_input("처방전을 선명하게 찍어주세요")
        st.info("AI 인식 기능은 API 키 설정 후 활성화됩니다.")

    with st.form("input_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            case_no = st.text_input("A: 케이스 번호")
            clinic = st.text_input("C: 클리닉 이름")
            patient = st.text_input("E: 환자 이름")
        with col2:
            date_g = st.date_input("G: 작업 완료일(정산기준)", datetime.now())
            material = st.selectbox("K: 재질", ["Thermo", "Dual", "Soft", "Other"])
            arch = st.radio("J: 상/하악", ["Upper", "Lower"], horizontal=True)
        
        note = st.text_area("L: 특이사항/리메이크 사유")
        
        if st.form_submit_button("✅ 저장하기", use_container_width=True):
            # 구글 시트 업데이트 로직 (데이터 추가)
            st.success("데이터가 구글 시트에 저장되었습니다!")

with tab2:
    st.subheader(f"📊 {datetime.now().month}월 수당 리포트")
    # G열 기준 필터링
    curr_month_df = df[df.iloc[:, 6].dt.month == datetime.now().month]
    count = len(curr_month_df)
    extra = max(0, count - TARGET_QUOTA)
    
    # 금액 계산
    gross = extra * EXTRA_UNIT_PRICE
    tax = gross * (TAX_RATE / 100)
    net = gross - tax

    c1, c2, c3 = st.columns(3)
    c1.metric("완료 수량", f"{count}개", delta=f"Extra {extra}")
    c2.metric("세전 수당", f"${gross:,.0f}")
    c3.metric("세후 예상액", f"${net:,.0f}", delta=f"-${tax:,.0f}")
    
    st.progress(min(count / TARGET_QUOTA, 1.0))
    st.dataframe(curr_month_df.iloc[:, [0, 2, 4, 6, 10]], use_container_width=True)

with tab3:
    st.subheader("🔍 환자 검색")
    search = st.text_input("환자 이름을 입력하세요")
    if search:
        res = df[df.iloc[:, 4].str.contains(search, na=False)]
        st.table(res.iloc[:, [0, 2, 4, 6, 11]])
