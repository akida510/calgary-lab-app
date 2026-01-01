import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 구글 시트 연결
SHEET_URL = "https://docs.google.com/spreadsheets/d/1t8Nt3jEZliThpKNwgUBXBxnVPJXoUzwQ1lGIAnoqhxk/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 함수 ---
@st.cache_data(ttl=60)
def get_all_data():
    try:
        # 메인 데이터 로드 (첫 번째 시트)
        main_df = conn.read(spreadsheet=SHEET_URL)
        # 참조시트 로드
        ref_df = conn.read(spreadsheet=SHEET_URL, worksheet="참조시트")
        
        # 메인 데이터 날짜 정제
        main_df['date_cleaned'] = pd.to_datetime(main_df.iloc[:, 6], errors='coerce')
        return main_df, ref_df
    except Exception as e:
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame()

df, ref_df = get_all_data()

# --- 화면 구성 ---
st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # 참조시트 기반 데이터 추출
        # B열: 클리닉명
        clinics = sorted(ref_df['클리닉명'].dropna().unique().tolist())
        # D열: 상악/하악 옵션
        arch_options = ref_df['작업치'].dropna().unique().tolist() if '작업치' in ref_df.columns else ["Upper", "Lower"]
        # E열: 재질 옵션
        material_options = ref_df['재질'].dropna().unique().tolist() if '재질' in ref_df.columns else ["Thermo", "Dual", "Soft"]
        
        with st.form(key="case_input_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: 케이스 번호 (Case #)")
                
                # 클리닉 선택 (자동완성 기능 포함)
                selected_clinic = st.selectbox("C: 클리닉 선택", options=["선택하세요"] + clinics)
                
                # --- 의사 필터링 로직 (종속 드롭다운) ---
                if selected_clinic != "선택하세요":
                    # 1. 해당 클리닉 소속 의사 + 2. 클리닉명이 비어있는(공통) 의사
                    filtered_docs = ref_df[
                        (ref_df['클리닉명'] == selected_clinic) | 
                        (ref_df['클리닉명'].isna()) | 
                        (ref_df['클리닉명'] == "")
                    ]['닥터명'].dropna().unique().tolist()
                else:
                    filtered_docs = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("D: 닥터 선택", options=filtered_docs)
                patient = st.text_input("E: 환자 이름")

            with col2:
                date_g = st.date_input("G: 작업 완료일", datetime.now())
                selected_arch = st.radio("J: 상악/하악", options=arch_options, horizontal=True)
                selected_material = st.selectbox("K: 재질", options=material_options)
            
            # F열: 참고사항/리메이크 사유
            note = st.text_area("L: 특이사항 및 리메이크 사유 (F열 참조)")
            
            submit_button = st.form_submit_button("✅ 구글 시트에 저장하기", use_container_width=True)
            
            if submit_button:
                if selected_clinic == "선택하세요" or not patient:
                    st.error("클리닉명과 환자 이름은 필수 입력 항목입니다.")
                else:
                    # 여기에 실제 저장 로직이 들어갑니다.
                    st.success(f"{patient}님 케이스({selected_clinic})가 성공적으로 기록되었습니다! (조회 모드)")
    else:
        st.warning("참조시트를 불러올 수 없습니다. 시트의 탭 이름과 컬럼 제목을 확인해 주세요.")

# --- 정산 및 검색 탭은 이전과 동일하게 유지 ---
with tab2:
    st.subheader(f"📊 {datetime.now().month}월 실적 리포트")
    if not df.empty:
        valid_df = df.dropna(subset=['date_cleaned']).copy()
        curr_month, curr_year = datetime.now().month, datetime.now().year
        this_month_df = valid_df[(valid_df['date_cleaned'].dt.month == curr_month) & (valid_df['date_cleaned'].dt.year == curr_year)]
        
        count = len(this_month_df)
        extra = max(0, count - 320)
        c1, c2, c3 = st.columns(3)
        c1.metric("완료 수량", f"{count}개")
        c2.metric("오버 수량", f"{extra}개")
        c3.metric("예상 수당", f"${extra * 30:,.0f}")
        st.dataframe(this_month_df.iloc[:, [0, 2, 4, 6]], use_container_width=True)

with tab3:
    st.subheader("🔍 환자 검색")
    search = st.text_input("환자 이름을 입력하세요")
    if search and not df.empty:
        res = df[df.iloc[:, 4].astype(str).str.contains(search, na=False, case=False)]
        st.dataframe(res.iloc[:, [0, 2, 4, 6]], use_container_width=True)
