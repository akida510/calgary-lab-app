import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 데이터 연결 및 로드
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)

    # 필수 컬럼 설정
    required_cols = ['Case #', 'Clinic', 'Doctor', 'Patient', 'Arch', 'Material', 'Price', 'Qty', 'Total', 'Receipt Date', 'Completed Date', 'Shipping Date', 'Due Date', 'Status', 'Notes']
    for col in required_cols:
        if col not in main_df.columns:
            main_df[col] = 0 if col in ['Price', 'Qty', 'Total'] else ""
    
    if not main_df.empty:
        main_df['Shipping Date'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')

except Exception as e:
    st.error(f"데이터 연결 오류: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

# --- [TAB 1: 케이스 등록] ---
with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    # 1️⃣ 기본 정보 구역
    with st.expander("1️⃣ 기본 정보 입력 (필수)", expanded=True):
        c1, c2, c3 = st.columns(3)
        
        with c1:
            case_no = st.text_input("A: Case # *", placeholder="번호 입력", key="case_input")
            patient = st.text_input("D: Patient Name *", placeholder="환자 성함", key="patient_input")

        with c2:
            raw_clinics = ref_df.iloc[:, 1].unique().tolist()
            clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic']])
            clinic_opts = ["선택하세요", "➕ 새 클리닉 직접 입력"] + clean_clinics
            
            selected_clinic_pick = st.selectbox("B: Clinic 선택 *", options=clinic_opts, key="clinic_select")
            
            final_clinic = ""
            if selected_clinic_pick == "➕ 새 클리닉 직접 입력":
                final_clinic = st.text_input("클리닉 이름을 입력하세요", key="clinic_direct")
            else:
                final_clinic = selected_clinic_pick

        with c3:
            doctor_opts = ["선택하세요", "➕ 새 의사 직접 입력"]
            if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
                matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
                doctor_opts += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none']])
            
            selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_opts, key="doctor_select")
            
            final_doctor = ""
            if selected_doctor_pick == "➕ 새 의사 직접 입력":
                final_doctor = st.text_input("의사 이름을 입력하세요", key="doctor_direct")
            else:
                final_doctor = selected_doctor_pick

    # 2️⃣ 작업 상세 및 날짜 연동 구역
    with st.expander("2️⃣ 작업 상세 및 날짜 연동", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True, key="arch_radio")
            selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"], key="mat_select")
            qty = st.number_input("Qty (수량)", min_value=1, value=1, key="qty_input")
        
        with d2:
            is_3d_model = st.checkbox("3D 모델 (접수일/시간 없음)", value=True, key="is_3d_check")
            if not is_3
