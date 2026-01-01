import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="centered")
st.title("🦷 Skycad Lab Night Guard Manager")

# 2. 보안 키 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드 (캐시 제거)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("A: Case #", key="case_input")
        
        # B열(Index 1) 클리닉 추출
        raw_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver']])
        selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics, key="clinic_select")
        
        # C열(Index 2) 닥터 매칭
        doctor_options = ["클리닉을 먼저 선택하세요"]
        if selected_clinic != "선택하세요":
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic].iloc[:, 2].unique().tolist()
            doctor_options = sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none', 'doctor']])
            if not doctor_options: doctor_options = ["등록된 의사 없음"]
        
        selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options, key="doctor_select")
        patient = st.text_input("D: Patient Name", key="patient_input")
        receipt_date = st.date_input("📅 Receipt Date (접수일)", datetime.now(), key="receipt_date")

    with col2:
        due_date = st.date_input("🚨 Due Date (마감일)", datetime.now(), key="due_date")
        completed_date = st.date_input("✅ Date Completed (완료일)", datetime.now(), key="completed_date")
        
        # Arch: Max 우선, Note 삭제 요청 반영
        selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True, key="arch_radio")
        
        # Material: 고정 순서
        selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"], key="mat_select")

    notes = st.text_area("F: Check List / 리메이크 사유", key="notes_input")
    
    if st.button("✅ 구글 시트에 저장하기", use_container_width=True):
        if selected_clinic == "선택하세요" or not patient or "선택하세요" in str(selected_doctor):
            st.warning("필수 항목을 모두 입력해 주세요.")
        else:
            new_row = pd.DataFrame([{
                "Case #": case_no,
                "Clinic": selected_clinic,
                "Doctor": selected_doctor,
                "Patient": patient,
                "Arch": selected_arch,
                "Material": selected_material,
                "Receipt Date": receipt_date.strftime('%Y-%m-%d'),
                "Due Date": due_date.strftime('%Y-%m-%d'),
                "Completed Date": completed_date.strftime('%Y-%m-%d'),
                "Notes": notes
            }])
            try:
                updated_df = pd.concat([main_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 {patient}님 저장 성공!")
                st.balloons()
            except Exception as e:
                st.error(f"저장 오류: {e}")

with tab2:
    st.info("정산 기능은 준비 중입니다.")

with tab3:
    st.subheader("🔍 환자 검색")
    search_q = st.text_input("이름 또는 케이스 번호 입력")
    if search_q:
        # main_df가 비어있지 않은지 확인 후 검색
        if not main_df.empty:
            result = main_df[main_df.apply(lambda row: search_q.lower() in str(row.values).lower(), axis=1)]
            st.dataframe(result, use_container_width=True)
        else:
            st.write("데이터가 없습니다.")
