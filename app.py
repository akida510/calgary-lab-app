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
        main_df = conn.read(spreadsheet=SHEET_URL)
        ref_df = conn.read(spreadsheet=SHEET_URL, worksheet="Reference")
        
        # 메인 시트 G열(7번째 열) 날짜 정제
        if not main_df.empty:
            main_df.iloc[:, 6] = pd.to_datetime(main_df.iloc[:, 6], errors='coerce')
        
        return main_df, ref_df
    except Exception as e:
        st.error(f"데이터 로드 오류: {e}")
        return pd.DataFrame(), pd.DataFrame()

df, ref_df = get_all_data()

# --- 화면 구성 ---
st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # 참조시트 열 번호 정의
        # B=1(Clinic), C=2(Doctor), D=3(Arch - 상/하악), E=4(Material - 재질)
        clinics = sorted(ref_df.iloc[:, 1].dropna().unique().tolist())
        arch_list = ref_df.iloc[:, 3].dropna().unique().tolist()
        mat_list = ref_df.iloc[:, 4].dropna().unique().tolist()
        
        with st.form(key="final_entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case # (케이스 번호)")
                selected_clinic = st.selectbox("C: Clinic (클리닉)", options=["Select Clinic"] + clinics)
                
                # 닥터 필터링 (해당 클리닉 닥터 + 소속 없는 닥터)
                if selected_clinic != "Select Clinic":
                    filtered_docs = ref_df[
                        (ref_df.iloc[:, 1] == selected_clinic) | 
                        (ref_df.iloc[:, 1].isna()) | (ref_df.iloc[:, 1] == "")
                    ].iloc[:, 2].dropna().unique().tolist()
                else:
                    filtered_docs = ["Select Clinic First"]
                
                selected_doctor = st.selectbox("D: Doctor (닥터)", options=filtered_docs)
                patient = st.text_input("E: Patient Name (환자이름)")

            with col2:
                date_g = st.date_input("G: Date Completed (완료일)", datetime.now())
                selected_arch = st.radio("J: Arch (상/하악)", options=arch_list if arch_list else ["Upper", "Lower"], horizontal=True)
                selected_material = st.selectbox("K: Material (재질)", options=mat_list if mat_list else ["Thermo", "Dual", "Soft"])
            
            note = st.text_area("L: Notes (특이사항 / 리메이크 사유)")
            
            if st.form_submit_button("✅ 확인 및 저장", use_container_width=True):
                if selected_clinic == "Select Clinic" or not patient:
                    st.warning("Clinic과 Patient Name은 필수입니다.")
                else:
                    st.success(f"데이터 준비 완료: {patient} ({selected_clinic})")
                    st.info("실제 시트 기록 기능 연결을 위해 다음 단계를 진행해 주세요.")
    else:
        st.error("Reference 시트를 불러올 수 없습니다.")

# --- 정산 및 검색 탭 (생략 - 이전과 동일) ---
# (중략 - Tab2, Tab3 로직은 이전과 동일하게 유지됨)
