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

# --- 구글 시트 연결 (캐시 사용 안함) ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 캐시 없이 실시간으로 데이터를 읽어옵니다.
    main_df = conn.read(ttl=0)
    ref_df = conn.read(worksheet="Reference", ttl=0)
    
except Exception as e:
    st.error(f"⚠️ 연결 오류: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # 1. 모든 데이터를 문자열로 변환하고 앞뒤 공백 제거
        # 제목줄이 꼬여있을 수 있으므로 열 이름 대신 번호(Index)를 사용합니다.
        # B열은 index 1, C열은 index 2입니다.
        ref_temp = ref_df.astype(str).apply(lambda x: x.str.strip())
        
        # 2. 클리닉 목록 추출 (B열에서 유효한 값만 골라내기)
        # 'nan', 'None', 'Clinic', 'Deliver' 등 실제 데이터가 아닌 것들을 제외합니다.
        clinics_in_sheet = ref_temp.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in clinics_in_sheet if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', '']])
        
        with st.form(key="super_final_v12", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                
                # 클리닉 선택창
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics)
                
                # --- 닥터 필터링 (가장 단순하고 강력한 매칭) ---
                if selected_clinic != "선택하세요":
                    # B열에서 선택한 클리닉과 일치하는 모든 행의 C열 값을 긁어옵니다.
                    matched_docs = ref_temp[ref_temp.iloc[:, 1] == selected_clinic].iloc[:, 2].unique().tolist()
                    doctor_options = sorted([d for d in matched_docs if d and d.lower() not in ['nan', 'none', 'doctor', '']])
                    
                    if not doctor_options:
                        doctor_options = ["의사 정보 없음"]
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
                patient = st.text_input("D: Patient Name")

            with col2:
                date_completed = st.date_input("G: Date Completed", datetime.now())
                
                # Arch(D열) 및 Material(E열) 옵션 추출
                arch_opts = sorted([a for a in ref_temp.iloc[:, 3].unique() if a and a.lower() not in ['nan', 'none', 'arch', '']])
                selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                mat_opts = sorted([m for m in ref_temp.iloc[:, 4].unique() if m and m.lower() not in ['nan', 'none', 'material', '']])
                selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])
            
            notes = st.text_area("F: Check List")
            
            if st.form_submit_button("✅ 구글 시트에 저장", use_container_width=True):
                if selected_clinic == "선택하세요" or not patient or "선택하세요" in str(selected_doctor):
                    st.warning("필수 항목을 모두 입력해 주세요.")
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
                        updated_df = pd.concat([main_df, new_entry], ignore_index=True)
                        conn.update(data=updated_df)
                        st.success(f"🎉 {patient}님 데이터 저장 성공!")
                        # 성공 후 화면 강제 새로고침
                        st.rerun()
                    except Exception as e:
                        st.error(f"저장 중 오류 발생: {e}")
