import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# [중요] 앱이 실행될 때마다 모든 옛날 데이터를 강제로 지웁니다.
st.cache_data.clear()

st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 1. 보안 키 처리
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 2. 데이터 불러오기 (ttl=0으로 실시간성 확보)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 제목 없이 전체 데이터를 읽어와서 공백을 싹 제거합니다.
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None).astype(str)
    ref_df = ref_df.apply(lambda x: x.str.strip())
    main_df = conn.read(ttl=0)
except Exception as e:
    st.error(f"연결 실패: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    # B열(Index 1)에서 클리닉 목록 추출
    raw_clinics = ref_df.iloc[:, 1].unique().tolist()
    clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', 'header', '']])

    with st.form(key="v50_matching_fix"):
        col1, col2 = st.columns(2)
        
        with col1:
            case_no = st.text_input("A: Case #")
            selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics)
            
            # --- 닥터 매칭 (전수 조사 방식) ---
            doctor_options = ["클리닉을 먼저 선택하세요"]
            
            if selected_clinic != "선택하세요":
                matched_docs = []
                # 시트 전체를 한 줄씩 검사합니다.
                for _, row in ref_df.iterrows():
                    # B열(1)에 선택한 클리닉이 있으면 C열(2)의 닥터를 추가
                    if row[1] == selected_clinic:
                        doc_name = row[2]
                        if doc_name and doc_name.lower() not in ['nan', 'none', 'doctor', '']:
                            matched_docs.append(doc_name)
                
                doctor_options = sorted(list(set(matched_docs)))
                
                if not doctor_options:
                    doctor_options = ["등록된 의사 없음"]
                else:
                    # [진단용] 닥터를 찾았는지 숫자로 알려줍니다.
                    st.info(f"✔️ {len(doctor_options)}명의 의사를 찾았습니다.")

            selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
            patient = st.text_input("D: Patient Name")

        with col2:
            date_completed = st.date_input("G: Date Completed", datetime.now())
            
            # D열(3)에서 Arch 옵션, E열(4)에서 Material 옵션 추출
            arch_opts = sorted([a for a in ref_df.iloc[:, 3].unique() if a and a.lower() not in ['nan', 'none', 'arch', '']])
            selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Mand", "Max"], horizontal=True)
            
            mat_opts = sorted([m for m in ref_df.iloc[:, 4].unique() if m and m.lower() not in ['nan', 'none', 'material', '']])
            selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])

        notes = st.text_area("F: Check List")
        
        if st.form_submit_button("✅ 저장하기", use_container_width=True):
            if selected_clinic == "선택하세요" or not patient or selected_doctor in ["클리닉을 먼저 선택하세요", "등록된 의사 없음"]:
                st.warning("모든 정보를 올바르게 입력했는지 확인해주세요.")
            else:
                new_row = pd.DataFrame([{
                    "Case #": case_no, "Clinic": selected_clinic, "Doctor": selected_doctor,
                    "Patient": patient, "Arch": selected_arch, "Material": selected_material,
                    "Date": date_completed.strftime('%Y-%m-%d'), "Notes": notes
                }])
                try:
                    updated = pd.concat([main_df, new_row], ignore_index=True)
                    conn.update(data=updated)
                    st.success(f"🎉 {patient}님 저장 성공!")
                except Exception as e:
                    st.error(f"저장 오류: {e}")
