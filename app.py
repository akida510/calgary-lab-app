import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 1. 보안 키 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 2. 데이터 불러오기
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 제목 없이 전체를 읽어와서 모든 공백을 제거합니다.
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)
except Exception as e:
    st.error(f"연결 실패: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    # B열(Index 1)에서 클리닉 목록을 추출합니다.
    raw_clinics = ref_df.iloc[:, 1].unique().tolist()
    clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', '']])

    with st.form(key="super_match_v40", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            case_no = st.text_input("A: Case #")
            selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics)
            
            # --- 닥터 매칭 로직 (강제 매칭) ---
            doctor_options = ["클리닉을 먼저 선택하세요"]
            
            if selected_clinic != "선택하세요":
                # 선택된 클리닉 이름과 똑같은 행을 모두 찾습니다.
                matched_docs = []
                for i, row in ref_df.iterrows():
                    if row[1] == selected_clinic: # B열 검사
                        doc_name = row[2] # C열(닥터) 추출
                        if doc_name and doc_name.lower() not in ['nan', 'none', 'doctor', '']:
                            matched_docs.append(doc_name)
                
                doctor_options = sorted(list(set(matched_docs))) # 중복 제거 및 정렬
                
                if not doctor_options:
                    doctor_options = ["등록된 의사 없음"]

            selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
            patient = st.text_input("D: Patient Name")

        with col2:
            date_completed = st.date_input("G: Date Completed", datetime.now())
            
            # Arch(Index 3) & Material(Index 4) 옵션 추출
            arch_opts = sorted([a for a in ref_df.iloc[:, 3].unique() if a and a.lower() not in ['nan', 'none', 'arch', '']])
            selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Mand", "Max"], horizontal=True)
            
            mat_opts = sorted([m for m in ref_df.iloc[:, 4].unique() if m and m.lower() not in ['nan', 'none', 'material', '']])
            selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])

        notes = st.text_area("F: Check List")
        
        if st.form_submit_button("✅ 저장하기", use_container_width=True):
            if selected_clinic == "선택하세요" or not patient or selected_doctor in ["클리닉을 먼저 선택하세요", "등록된 의사 없음"]:
                st.warning("필수 항목을 모두 확인해 주세요.")
            else:
                new_row = pd.DataFrame([{
                    "Case #": case_no, "Clinic": selected_clinic, "Doctor": selected_doctor,
                    "Patient": patient, "Arch": selected_arch, "Material": selected_material,
                    "Date": date_completed.strftime('%Y-%m-%d'), "Notes": notes
                }])
                try:
                    updated = pd.concat([main_df, new_row], ignore_index=True)
                    conn.update(data=updated)
                    st.success(f"{patient}님 저장 성공!")
                    st.balloons()
                except Exception as e:
                    st.error(f"저장 중 오류: {e}")
