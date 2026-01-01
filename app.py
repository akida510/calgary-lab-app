import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# --- 보안 키 줄바꿈 보정 ---
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# --- 구글 시트 연결 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    @st.cache_data(ttl=5)
    def load_data():
        # 전체 데이터를 읽어온 후, 앞뒤 공백을 싹 제거합니다.
        main_df = conn.read(ttl=0)
        ref_df = conn.read(worksheet="Reference", ttl=0)
        # 모든 데이터의 공백 제거 및 문자열 변환
        ref_df = ref_df.astype(str).apply(lambda x: x.str.strip())
        return main_df, ref_df

    df, ref_df = load_data()

except Exception as e:
    st.error(f"⚠️ 연결 오류: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # 1. 클리닉 목록 가져오기 (B열 제목이 'Clinic'인 경우)
        # 만약 시트 제목이 다르면 아래 ['Clinic'] 부분을 실제 시트 제목과 똑같이 고쳐야 합니다.
        clinic_column = 'Clinic' 
        doctor_column = 'Doctor'
        
        # 실제 값이 있는 클리닉만 추출
        clinics = sorted([c for c in ref_df[clinic_column].unique() if c and c != 'nan' and c != 'None'])
        
        with st.form(key="entry_form_v10"):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                # 클리닉 선택
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clinics)
                
                # --- 닥터 필터링 (가장 확실한 방식) ---
                if selected_clinic != "선택하세요":
                    # 선택한 클리닉 이름과 정확히 일치하는 행만 필터링
                    matched_rows = ref_df[ref_df[clinic_column] == selected_clinic]
                    doctor_options = sorted([d for d in matched_rows[doctor_column].unique() if d and d != 'nan'])
                    
                    if not doctor_options:
                        doctor_options = ["등록된 의사 없음"]
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
                patient = st.text_input("D: Patient Name")

            with col2:
                date_completed = st.date_input("G: Date Completed", datetime.now())
                # Arch와 Material은 시트의 4번째(D), 5번째(E) 열에서 가져옴
                arch_opts = sorted([a for a in ref_df.iloc[:, 3].unique() if a and a != 'nan'])
                selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"])
                
                mat_opts = sorted([m for m in ref_df.iloc[:, 4].unique() if m and m != 'nan'])
                selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])
            
            notes = st.text_area("F: Check List")
            
            if st.form_submit_button("✅ 구글 시트에 저장"):
                if selected_clinic == "선택하세요" or not patient or "선택하세요" in selected_doctor:
                    st.warning("필수 항목을 입력하세요.")
                else:
                    # 저장 데이터 구성
                    new_data = pd.DataFrame([{
                        "Case #": case_no,
                        "Clinic": selected_clinic,
                        "Doctor": selected_doctor,
                        "Patient": patient,
                        "Arch": selected_arch,
                        "Material": selected_material,
                        "Date": date_completed.strftime('%Y-%m-%d'),
                        "Notes": notes
                    }])
                    updated_df = pd.concat([df, new_data], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("저장 완료!")
                    st.cache_data.clear()
