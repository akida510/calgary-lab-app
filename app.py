import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 앱 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 구글 시트 연결
SHEET_URL = "https://docs.google.com/spreadsheets/d/1t8Nt3jEZliThpKNwgUBXBxnVPJXoUzwQ1lGIAnoqhxk/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 및 정제 함수 ---
@st.cache_data(ttl=60)
def load_data():
    try:
        raw_df = conn.read(spreadsheet=SHEET_URL)
        if raw_df is None or raw_df.empty:
            return pd.DataFrame()
        
        # G열(인덱스 6) 복사본 생성 및 날짜 변환
        # 변환 불가능한 값은 NaT(빈 날짜)로 만듭니다.
        raw_df['date_cleaned'] = pd.to_datetime(raw_df.iloc[:, 6], errors='coerce')
        return raw_df
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        return pd.DataFrame()

df = load_data()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with tab1:
    st.subheader("새 케이스 추가")
    with st.form(key="input_form_v3", clear_on_submit=True):
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
            st.warning("현재는 조회 모드입니다. 저장 기능은 API 설정 후 활성화됩니다.")

with tab2:
    st.subheader(f"📊 {datetime.now().month}월 수당 리포트")
    
    if not df.empty and 'date_cleaned' in df.columns:
        # 날짜가 성공적으로 변환된 데이터만 사용
        valid_df = df.dropna(subset=['date_cleaned']).copy()
        
        curr_month = datetime.now().month
        curr_year = datetime.now().year
        
        # 월/년 필터링 (에러 방지를 위해 .dt 접근 전 데이터 확인)
        this_month_df = valid_df[
            (valid_df['date_cleaned'].dt.month == curr_month) & 
            (valid_df['date_cleaned'].dt.year == curr_year)
        ]
        
        count = len(this_month_df)
        extra = max(0, count - 320)
        gross = extra * 30
        
        c1, c2, c3 = st.columns(3)
        c1.metric("이번 달 완료", f"{count}개")
        c2.metric("오버 수량", f"{extra}개")
        c3.metric("세전 수당", f"${gross:,.0f}")
        
        st.progress(min(count / 320, 1.0))
        # 주요 컬럼만 표시 (A, C, E, G열)
        st.dataframe(this_month_df.iloc[:, [0, 2, 4, 6]], use_container_width=True)
    else:
        st.info("정산할 데이터가 없거나 G열의 날짜 형식을 확인해야 합니다.")

with tab3:
    st.subheader("🔍 환자 검색")
    search = st.text_input("환자 이름 입력")
    if search and not df.empty:
        # E열(인덱스 4)에서 검색
        res = df[df.iloc[:, 4].astype(str).str.contains(search, na=False, case=False)]
        st.dataframe(res.iloc[:, [0, 2, 4, 6]])
        
