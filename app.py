import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 앱 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 구글 시트 연결
SHEET_URL = "https://docs.google.com/spreadsheets/d/1t8Nt3jEZliThpKNwgUBXBxnVPJXoUzwQ1lGIAnoqhxk/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 함수 ---
@st.cache_data(ttl=60)
def load_data():
    # 시트 읽기
    raw_df = conn.read(spreadsheet=SHEET_URL)
    
    # 데이터가 아예 없는 경우 방지
    if raw_df.empty:
        return raw_df

    # G열(인덱스 6) 날짜 강제 변환
    # 날짜가 아니면 NaT(Not a Time)로 표시하고 에러 없이 진행
    raw_df.iloc[:, 6] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce')
    
    return raw_df

# --- 실행부 ---
df = load_data()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with tab1:
    st.subheader("새 케이스 추가")
    with st.form(key="input_form_v2", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            case_no = st.text_input("A: 케이스 번호")
            clinic = st.text_input("C: 클리닉 이름")
            patient = st.text_input("E: 환자 이름")
        with col2:
            date_g = st.date_input("G: 작업 완료일", datetime.now())
            material = st.selectbox("K: 재질", ["Thermo", "Dual", "Soft", "Other"])
            arch = st.radio("J: 상/하악", ["Upper", "Lower"], horizontal=True)
        
        note = st.text_area("L: 특이사항")
        
        if st.form_submit_button("✅ 저장하기", use_container_width=True):
            st.info("데이터를 저장하려면 시트 업데이트 로직이 필요합니다. 현재는 입력 테스트 모드입니다.")

with tab2:
    st.subheader(f"📊 {datetime.now().month}월 수당 리포트")
    
    if not df.empty:
        # G열 날짜가 유효한 것만 필터링 (에러 방지 핵심)
        valid_date_df = df.dropna(subset=[df.columns[6]])
        
        # 이번 달 데이터 필터링
        curr_month = datetime.now().month
        curr_year = datetime.now().year
        
        this_month_df = valid_date_df[
            (valid_date_df.iloc[:, 6].dt.month == curr_month) & 
            (valid_date_df.iloc[:, 6].dt.year == curr_year)
        ]
        
        count = len(this_month_df)
        extra = max(0, count - 320)
        gross = extra * 30
        
        c1, c2, c3 = st.columns(3)
        c1.metric("이번 달 완료", f"{count}개")
        c2.metric("오버 수량", f"{extra}개")
        c3.metric("세전 수당", f"${gross:,.0f}")
        
        st.progress(min(count / 320, 1.0))
        st.dataframe(this_month_df.iloc[:, [0, 2, 4, 6]], use_container_width=True)
    else:
        st.write("데이터가 없습니다.")

with tab3:
    st.subheader("🔍 환자 검색")
    search = st.text_input("환자 이름 입력")
    if search and not df.empty:
        # E열(인덱스 4)에서 이름 검색
        res = df[df.iloc[:, 4].astype(str).str.contains(search, na=False, case=False)]
        st.dataframe(res.iloc[:, [0, 2, 4, 6]])
        
