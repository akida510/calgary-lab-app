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
    # Reference 시트를 읽어오되, 제목줄 없이(header=None) 가져와서 정밀 제어합니다.
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    # 데이터의 모든 칸에서 앞뒤 공백을 완전히 제거합니다.
    ref_df = ref_df.apply(lambda x: x.str.strip())
    
    main_df = conn.read(ttl=0)
except Exception as e:
    st.error(f"데이터 연결 에러: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    # B열(Index 1)이 클리닉 열입니다.
    # 'Clinic'이라는 제목줄이나 빈 값은 리스트에서 뺍니다.
    all_clinics_raw = ref_df.iloc[:, 1].unique().tolist()
    clean_clinics = sorted([c for c in all_clinics_raw if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', '']])

    with st.form(key="final_matching_logic", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            case_no = st.text_input("A: Case #")
            # 클리닉 선택
            selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics)
            
            # --- 닥터 매칭 (이 부분이 핵심입니다) ---
            if selected_clinic != "선택하세요":
                # 선택된 클리닉 이름과 정확히 일치하는 줄(Row)을 모두 찾습니다.
                matched_rows = ref_df[ref_df.iloc[:, 1] == selected_clinic]
                # 그 줄들의 C열(Index 2)에서 의사 이름을 가져옵니다.
                docs = matched_rows.iloc[:, 2].unique().tolist()
                doctor_options = sorted([d for d in docs if d and d.lower() not in ['nan', 'none', 'doctor', '']])
                
                if not doctor_options:
                    doctor_options = ["의사 정보 없음"]
            else:
                doctor_options = ["클리닉을 먼저 선택하세요"]
            
            selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
            patient = st.text_input("D: Patient Name")

        with col2:
            date_completed = st.date_input("G: Date Completed", datetime.now())
            
            # Arch(D열/Index 3) 옵션 추출
            arch_vals = ref_df.iloc[:, 3].unique().tolist()
            arch_opts = sorted([a for a in arch_vals if a and a.lower() not in ['nan', 'none', 'arch', 'note']])
            selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
            
            # Material(E열/Index 4) 옵션 추출
            mat_vals = ref_df.iloc[:, 4].unique().tolist()
            mat_opts = sorted([m for m in mat_vals if m and m.lower() not in ['nan', 'none', 'material', 'note']])
            selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])

        notes = st.text_area("F: Check List")
        
        if st.form_submit_button("✅ 저장하기", use_container_width=True):
            if selected_clinic == "선택하세요" or not patient or "선택하세요" in str(selected_doctor):
                st.warning("모든 필수 항목을 입력해 주세요.")
            else:
                new_data = pd.DataFrame([{
                    "Case #": case_no, "Clinic": selected_clinic, "Doctor": selected_doctor,
                    "Patient": patient, "Arch": selected_arch, "Material": selected_material,
                    "Date": date_completed.strftime('%Y-%m-%d'), "Notes": notes
                }])
                try:
                    updated = pd.concat([main_df, new_data], ignore_index=True)
                    conn.update(data=updated)
                    st.success(f"{patient}님 저장 성공!")
                    st.balloons()
                except Exception as e:
                    st.error(f"저장 실패: {e}")
