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

# 3. 데이터 로드
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
        
        # 중복 체크
        if case_no and not main_df.empty:
            is_duplicate = main_df[main_df['Case #'].astype(str) == case_no]
            if not is_duplicate.empty:
                st.warning(f"⚠️ 경고: {case_no}번은 이미 등록된 번호입니다.")
        
        # 클리닉 선택
        raw_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver']])
        clinic_opts = ["선택하세요"] + clean_clinics + ["➕ 새 클리닉 직접 입력"]
        
        selected_clinic_pick = st.selectbox("B: Clinic 선택", options=clinic_opts, key="clinic_select")
        final_clinic = st.text_input("클리닉 이름을 입력하세요", key="new_clinic_input") if selected_clinic_pick == "➕ 새 클리닉 직접 입력" else selected_clinic_pick

        # 닥터 선택
        doctor_options = ["선택하세요"]
        if selected_clinic_pick not in ["선택하세요", "➕ 새 클리닉 직접 입력"]:
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic_pick].iloc[:, 2].unique().tolist()
            doctor_options += sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none', 'doctor']])
        
        doctor_options.append("➕ 새 의사 직접 입력")
        selected_doctor_pick = st.selectbox("C: Doctor 선택", options=doctor_options, key="doctor_select")
        final_doctor = st.text_input("의사 이름을 입력하세요", key="new_doctor_input") if selected_doctor_pick == "➕ 새 의사 직접 입력" else selected_doctor_pick

        patient = st.text_input("D: Patient Name", key="patient_input")

    with col2:
        # 접수일 (기본값: 3D 모델)
        is_3d_model = st.checkbox("3D 모델 (접수일 없음)", value=True, key="is_3d_model")
        if is_3d_model:
            receipt_date_str = "-"
        else:
            receipt_date = st.date_input("📅 Receipt Date (접수일)", datetime.now())
            receipt_date_str = receipt_date.strftime('%Y-%m-%d')

        # --- [순서 변경] 완료일을 마감일보다 위로 배치 ---
        completed_date = st.date_input("✅ Date Completed (완료일)", datetime.now())
        due_date = st.date_input("🚨 Due Date (마감일)", datetime.now())
        
        selected_arch = st.radio("Arch", options=["Max", "Mand"], horizontal=True)
        selected_material = st.selectbox("Material", options=["Thermo", "Dual", "Soft", "Hard"])
        selected_status = st.selectbox("📊 Status", options=["Normal", "Hold", "Canceled"])

    notes = st.text_area("F: Check List / 리메이크 사유", key="notes_input")
    
    if st.button("✅ 구글 시트에 저장하기", use_container_width=True):
        if final_clinic in ["선택하세요", ""] or not patient or final_doctor in ["선택하세요", ""]:
            st.warning("필수 항목을 모두 입력해 주세요.")
        else:
            new_row = pd.DataFrame([{
                "Case #": case_no,
                "Clinic": final_clinic,
                "Doctor": final_doctor,
                "Patient": patient,
                "Arch": selected_arch,
                "Material": selected_material,
                "Receipt Date": receipt_date_str,
                "Due Date": due_date.strftime('%Y-%m-%d'),
                "Completed Date": completed_date.strftime('%Y-%m-%d'),
                "Status": selected_status,
                "Notes": notes
            }])
            try:
                updated_df = pd.concat([main_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 {patient}님 저장 성공!")
                st.balloons()
                st.rerun()
            except Exception as e:
                st.error(f"저장 오류: {e}")
