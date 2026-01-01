import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정 및 제목
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")
st.title("🦷 Calgary Lab Manager")

# 2. 보안 키 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드 (캐시 사용 안함)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 제목 없이 전체를 읽어와서 공백을 싹 제거
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)
except Exception as e:
    st.error(f"데이터 연결 실패: {e}")
    st.stop()

# 4. 탭 구성
tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    # --- 입력 필드 시작 (st.form을 쓰지 않고 직접 배치) ---
    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("A: Case #", key="case_input")
        
        # B열(1)에서 클리닉 목록 추출
        raw_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', 'header']])
        
        # 클리닉 선택 (선택 즉시 아래 코드가 실행됨)
        selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics, key="clinic_select")
        
        # --- 닥터 매칭 로직 ---
        doctor_options = ["클리닉을 먼저 선택하세요"]
        if selected_clinic != "선택하세요":
            # 시트의 B열과 선택한 클리닉이 같은 행의 C열(닥터)을 모두 수집
            matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic].iloc[:, 2].unique().tolist()
            doctor_options = sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none', 'doctor']])
            
            if not doctor_options:
                doctor_options = ["등록된 의사 없음"]
        
        selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options, key="doctor_select")
        patient = st.text_input("D: Patient Name", key="patient_input")

    with col2:
        date_completed = st.date_input("G: Date Completed", datetime.now(), key="date_input")
        
        # D열(3) Arch, E열(4) Material 자동 추출
        arch_opts = sorted([a for a in ref_df.iloc[:, 3].unique() if a and a.lower() not in ['nan', 'none', 'arch']])
        selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Mand", "Max"], horizontal=True, key="arch_radio")
        
        mat_opts = sorted([m for m in ref_df.iloc[:, 4].unique() if m and m.lower() not in ['nan', 'none', 'material']])
        selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"], key="mat_select")

    notes = st.text_area("F: Check List / 리메이크 사유", key="notes_input")
    
    # 저장 버튼 (Form이 아니므로 직접 처리)
    if st.button("✅ 구글 시트에 저장하기", use_container_width=True):
        if selected_clinic == "선택하세요" or not patient or selected_doctor in ["클리닉을 먼저 선택하세요", "등록된 의사 없음"]:
            st.warning("정보를 모두 입력해주세요.")
        else:
            new_row = pd.DataFrame([{
                "Case #": case_no, "Clinic": selected_clinic, "Doctor": selected_doctor,
                "Patient": patient, "Arch": selected_arch, "Material": selected_material,
                "Date": date_completed.strftime('%Y-%m-%d'), "Notes": notes
            }])
            try:
                updated_df = pd.concat([main_df, new_row], ignore_index=True)
                conn.update(data=updated_df)
                st.success(f"🎉 {patient}님 데이터 저장 성공!")
                st.balloons()
            except Exception as e:
                st.error(f"저장 중 오류: {e}")

with tab2:
    st.info("수당 정산 화면입니다.")

with tab3:
    st.info("환자 검색 화면입니다.")
