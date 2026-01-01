import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 보안 키 줄바꿈 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 제목행을 무시하고 전체 데이터를 가져온 후 수동으로 처리합니다.
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None)
    main_df = conn.read(ttl=0)
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    if not ref_df.empty:
        # 모든 데이터를 문자열로 변환하고 앞뒤 공백 제거
        ref_data = ref_df.astype(str).apply(lambda x: x.str.strip())
        
        # B열(Index 1)에서 클리닉 목록 추출
        # 제목줄인 'Clinic' 단어나 빈 값(nan)을 철저히 배제합니다.
        raw_clinics = ref_data.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', '123 dentist', '']])
        
        with st.form(key="final_structure_fix", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics)
                
                # 닥터 필터링: 선택한 클리닉 이름이 포함된 모든 행의 C열(Index 2)을 가져옴
                if selected_clinic != "선택하세요":
                    mask = ref_data.iloc[:, 1] == selected_clinic
                    docs = ref_data[mask].iloc[:, 2].unique().tolist()
                    doctor_options = sorted([d for d in docs if d and d.lower() not in ['nan', 'none', 'doctor', '']])
                    if not doctor_options:
                        doctor_options = ["의사 정보 없음"]
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
                patient = st.text_input("D: Patient Name")

            with col2:
                date_completed = st.date_input("G: Date Completed", datetime.now())
                
                # Arch (D열 - Index 3) 및 Material (E열 - Index 4) 옵션
                arch_list = sorted([a for a in ref_data.iloc[:, 3].unique() if a and a.lower() not in ['nan', 'none', 'arch', 'note']])
                selected_arch = st.radio("Arch", options=arch_list if arch_list else ["Max", "Mand"], horizontal=True)
                
                mat_list = sorted([m for m in ref_data.iloc[:, 4].unique() if m and m.lower() not in ['nan', 'none', 'material', 'note']])
                selected_material = st.selectbox("Material", options=mat_list if mat_list else ["Thermo", "Dual", "Soft"])
            
            notes = st.text_area("F: Check List")
            
            if st.form_submit_button("✅ 구글 시트에 저장", use_container_width=True):
                if selected_clinic == "선택하세요" or not patient or "선택하세요" in str(selected_doctor):
                    st.warning("필수 항목을 모두 입력해 주세요.")
                else:
                    new_entry = pd.DataFrame([{
                        "Case #": case_no, "Clinic": selected_clinic, "Doctor": selected_doctor,
                        "Patient": patient, "Arch": selected_arch, "Material": selected_material,
                        "Date": date_completed.strftime('%Y-%m-%d'), "Notes": notes
                    }])
                    try:
                        updated_df = pd.concat([main_df, new_entry], ignore_index=True)
                        conn.update(data=updated_df)
                        st.success(f"{patient}님 저장 완료!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
