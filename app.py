import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 구글 시트 연결
# (Secrets에 설정된 connections.gsheets 정보를 자동으로 사용합니다)
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 함수 ---
@st.cache_data(ttl=60)
def get_all_data():
    try:
        # 메인 시트와 Reference 시트 로드
        main_df = conn.read()
        ref_df = conn.read(worksheet="Reference")
        return main_df, ref_df
    except Exception as e:
        st.error(f"데이터 연결 오류: {e}")
        return pd.DataFrame(), pd.DataFrame()

df, ref_df = get_all_data()

# --- 화면 구성 ---
st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with tab1:
    st.subheader("새 케이스 등록")
    if not ref_df.empty:
        # 참조 데이터 추출
        clinics = sorted(ref_df.iloc[:, 1].dropna().unique().tolist())
        arch_list = ref_df.iloc[:, 3].dropna().unique().tolist()
        mat_list = ref_df.iloc[:, 4].dropna().unique().tolist()
        
        with st.form(key="data_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                case_no = st.text_input("Case #")
                clinic = st.selectbox("Clinic", options=["Select"] + clinics)
                
                # 닥터 필터링
                if clinic != "Select":
                    docs = ref_df[(ref_df.iloc[:, 1] == clinic) | (ref_df.iloc[:, 1].isna()) | (ref_df.iloc[:, 1] == "")].iloc[:, 2].dropna().tolist()
                else:
                    docs = []
                doctor = st.selectbox("Doctor", options=docs)
                patient = st.text_input("Patient")
            
            with c2:
                date_g = st.date_input("Date Completed", datetime.now())
                arch = st.radio("Arch", options=arch_list, horizontal=True)
                material = st.selectbox("Material", options=mat_list)
            
            note = st.text_area("Notes")
            
            if st.form_submit_button("✅ 구글 시트에 저장"):
                if clinic == "Select" or not patient:
                    st.warning("Clinic과 Patient Name은 필수입니다.")
                else:
                    # 새로운 행 데이터 생성 (시트의 열 순서에 맞춰서)
                    new_data = pd.DataFrame([{
                        "Case #": case_no,
                        "Clinic": clinic,
                        "Doctor": doctor,
                        "Patient": patient,
                        "Date": date_g.strftime("%Y-%m-%d"),
                        "Arch": arch,
                        "Material": material,
                        "Notes": note
                    }])
                    
                    # 기존 데이터에 추가 후 시트 업데이트
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    conn.update(data=updated_df)
                    
                    st.success("🎉 구글 시트에 성공적으로 저장되었습니다!")
                    st.cache_data.clear() # 데이터 새로고침
    else:
        st.info("시트 정보를 불러오는 중입니다...")

# 정산/검색 탭은 기존과 동일 (생략)
