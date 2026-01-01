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
    
    @st.cache_data(ttl=2)
    def load_data():
        main_df = conn.read(ttl=0)
        # Reference 시트 로드
        ref_df = conn.read(worksheet="Reference", ttl=0)
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
        # 데이터 전처리: 모든 값을 문자열로 바꾸고 공백 제거
        ref_temp = ref_df.astype(str).apply(lambda x: x.str.strip())
        
        # B열(클리닉) 목록 추출 (제목이나 빈칸 제외)
        all_clinics = ref_temp.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in all_clinics if c and c not in ['nan', 'None', 'Clinic', 'Deliver', '']])
        
        with st.form(key="final_v11_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics)
                
                # --- 닥터 필터링 로직 ---
                if selected_clinic != "선택하세요":
                    # B열이 선택된 클리닉인 행들에서 C열(닥터) 값들을 가져옴
                    matched_rows = ref_temp[ref_temp.iloc[:, 1] == selected_clinic]
                    docs = matched_rows.iloc[:, 2].unique().tolist()
                    doctor_options = sorted([d for d in docs if d and d not in ['nan', 'None', 'Doctor', '']])
                    
                    if not doctor_options:
                        doctor_options = ["의사 정보 없음"]
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
                patient = st.text_input("D: Patient Name")

            with col2:
                date_completed = st.date_input("G: Date Completed", datetime.now())
                
                # D열(Arch)과 E열(Material) 옵션 자동 추출
                arch_opts = sorted([a for a in ref_temp.iloc[:, 3].unique() if a and a not in ['nan', 'None', 'Arch', '']])
                selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                mat_opts = sorted([m for m in ref_temp.iloc[:, 4].unique() if m and m not in ['nan', 'None', 'Material', '']])
                selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])
            
            notes = st.text_area("F: Check List")
            
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
                        # 메인 시트 업데이트
                        updated_df = pd.concat([df, new_entry], ignore_index=True)
                        conn.update(data=updated_df)
                        st.success(f"🎉 {patient}님 저장 성공!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
