import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 구글 시트 연결
SHEET_URL = "https://docs.google.com/spreadsheets/d/1t8Nt3jEZliThpKNwgUBXBxnVPJXoUzwQ1lGIAnoqhxk/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 함수 (참조시트 포함) ---
@st.cache_data(ttl=60)
def get_all_data():
    # 메인 데이터와 참조시트를 각각 로드
    main_df = conn.read(spreadsheet=SHEET_URL)
    # worksheet 이름이 '참조시트'인 것을 가져옵니다.
    ref_df = conn.read(spreadsheet=SHEET_URL, worksheet="참조시트")
    
    # 메인 데이터 날짜 정제
    main_df['date_cleaned'] = pd.to_datetime(main_df.iloc[:, 6], errors='coerce')
    return main_df, ref_df

df, ref_df = get_all_data()

# --- 입력 폼 로직 ---
tab1, tab2, tab3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with tab1:
    st.subheader("새 케이스 추가")
    
    # 1. 참조시트에서 데이터 추출 (컬럼명은 시트에 맞게 수정 가능)
    # 클리닉명 리스트 (중복 제거)
    clinics = sorted(ref_df['클리닉명'].dropna().unique().tolist())
    
    with st.form(key="smart_input_form"):
        col1, col2 = st.columns(2)
        with col1:
            case_no = st.text_input("A: 케이스 번호")
            
            # 클리닉 선택 (검색 기능 포함)
            selected_clinic = st.selectbox("C: 클리닉 선택", options=["선택하세요"] + clinics)
            
            # 2. 닥터 필터링 로직
            if selected_clinic != "선택하세요":
                # 해당 클리닉 의사 + 소속 없는 의사
                relevant_docs = ref_df[
                    (ref_df['클리닉명'] == selected_clinic) | 
                    (ref_df['클리닉명'].isna()) | 
                    (ref_df['클리닉명'] == "")
                ]['의사명'].dropna().unique().tolist()
            else:
                relevant_docs = []

            selected_doctor = st.selectbox("D: 닥터 선택", options=relevant_docs)
            patient = st.text_input("E: 환자 이름")
            
        with col2:
            date_g = st.date_input("G: 작업 완료일", datetime.now())
            # 참조시트에 재질 리스트가 있다면 그것도 불러올 수 있습니다.
            materials = ref_df['재질'].dropna().unique().tolist() if '재질' in ref_df.columns else ["Thermo", "Dual", "Soft"]
            material = st.selectbox("K: 재질", options=materials)
            arch = st.radio("J: 상/하악", ["Upper", "Lower"], horizontal=True)
        
        note = st.text_area("L: 특이사항")
        
        if st.form_submit_button("✅ 저장하기"):
            # 구글 시트에 업데이트 하는 부분은 사장님이 준비되시면 추가하겠습니다!
            st.success(f"{selected_clinic} / {selected_doctor} / {patient} 저장 완료(시뮬레이션)")
