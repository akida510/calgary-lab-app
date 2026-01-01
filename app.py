import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 제목 변경
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="centered")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 보안 키 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드 (Reference 시트에서 정보 추출)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 제목 없이 전체를 읽어와서 공백 제거
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)
except Exception as e:
    st.error(f"데이터 연결 실패: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("A: Case #", key="case_input")
        
        # B열(Index 1)에서 클리닉 목록 추출
        raw_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', 'header']])
        
        selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics, key="clinic_select")
        
        # C열(Index 2)에서 닥터 매칭
        doctor_options = ["클리닉을 먼저 선택하세요"]
        if selected_clinic != "선택하세요":
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic].iloc[:, 2].unique().tolist()
            doctor_options = sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none', 'doctor']])
            if not doctor_options: doctor_options = ["등록된 의사 없음"]
        
        selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options, key="doctor_select")
        patient = st.text_input("D: Patient Name", key="patient_input")
        
        # 접수일 입력
        receipt_date = st.date_input("📅 Receipt Date (접수일)", datetime.now(), key="receipt_date")

    with col2:
        # 마감일 및 완료일 입력
        due_date = st.date_input("🚨 Due Date (마감일)", datetime.now(), key="due_date")
        completed_date = st.date_input("✅ Date Completed (완료일)", datetime.now(), key="completed_date")
        
        # Arch 설정: Max 우선
        arch_list = ["Max", "Mand", "Note"]
        selected_arch = st.radio("Arch", options=arch_list, horizontal=True, key="arch_radio")
        
        # Material 설정: 요청하신 순서 (Thermo, Dual, Soft, Hard)
        material_list = ["Thermo", "Dual", "Soft", "Hard"]
        selected_material = st.selectbox("Material", options=material_list, key="mat_select")

    notes = st.text_area("F: Check List / 리메이크 사유", key="notes_input")
    
    # 저장 버튼
    if st.button("✅ 구글 시트에 저장하기", use_container_width=True):
        if selected_clinic == "선택하세요" or not patient or selected_doctor in ["클리닉을 먼저 선택하세요", "등록된 의사 없음"]:
            st.warning("필수 항목을 모두 입력해주세요.")
        else:
            new_row = pd.DataFrame([{
                "Case #": case_no,
                "Clinic": selected_clinic,
                "Doctor": selected_doctor,
                "Patient": patient,
                "Arch
