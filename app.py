import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 2. 보안 키 보정
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    main_df = conn.read(ttl=0)
    # Reference 시트를 제목 없이(header=None) 읽어와서 수동으로 처리
    ref_df = conn.read(worksheet="Reference", ttl=0, header=None)
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # 모든 데이터 문자열 변환 및 공백 제거
        ref_temp = ref_df.astype(str).apply(lambda x: x.str.strip())
        
        # 1번째 열(B열)에서 클리닉 목록 추출 (실제 데이터만)
        # 'nan', 'Clinic', 'Deliver' 등 제외
        raw_clinics = ref_temp.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in raw_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', 'b', '1', '']])
        
        with st.form(key="form_final_v30", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics)
                
                # 닥터 필터링 (B열 선택 시 C열 닥터 추출)
                if selected_clinic != "선택하세요":
                    # B열(index 1)이 선택값과 같은 행의 C열(index 2) 값을 가져옴
                    matched_docs = ref_temp[ref_temp.iloc[:, 1] == selected_clinic].iloc[:, 2].unique().tolist()
                    doctor_options = sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none', 'doctor', 'c', '2', '']])
                    if not doctor_options:
                        doctor_options = ["등록된 의사 없음"]
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
                patient = st.text_input("D: Patient Name")

            with col2:
                date_completed = st.date_input("G: Date Completed", datetime.now())
                
                # D열(Index 3)에서 Arch 옵션
                arch_opts = sorted([a for a in ref_temp.iloc[:, 3].unique() if a and a.lower() not in ['nan', 'none', 'arch', '']])
                selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                # E열(Index 4)에서 Material 옵션
                mat_opts = sorted([m for m in ref_temp.iloc[:, 4].unique() if m and m.lower() not in ['nan', 'none', 'material', '']])
                selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])
            
            notes = st.text_area("F: Check List / 리메이크 사유")
            
            if st.form_submit_button("✅ 구글 시트에 저장", use_container_width=True):
                if selected_clinic == "선택하세요" or not patient or "선택하세요" in str(selected_doctor):
                    st.warning("필수 항목을 모두 입력하세요.")
                else:
                    new_entry = pd.DataFrame([{
                        "Case #": case_no,
                        "Clinic": selected_clinic,
                        "Doctor": selected_doctor,
                        "Patient": patient,
                        "Arch": selected_arch,
                        "Material": selected_material,
                        "Date": date_completed.strftime('%Y-%m-%d'),
                        "Notes": notes
                    }])
                    try:
                        updated_main = pd.concat([main_df, new_entry], ignore_index=True)
                        conn.update(data=updated_main)
                        st.success(f"🎉 {patient}님 저장 성공!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"저장 중 오류 발생: {e}")
