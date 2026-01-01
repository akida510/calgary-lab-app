import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# --- 보안 키 줄바꿈 보정 (폰 작업 필수) ---
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# --- 구글 시트 연결 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    @st.cache_data(ttl=2) # 즉각적인 반영을 위해 캐시를 거의 없앴습니다.
    def load_data():
        # 시트를 읽어온 후 모든 텍스트의 공백을 제거하고 문자로 변환합니다.
        main_df = conn.read(ttl=0)
        ref_df = conn.read(worksheet="Reference", ttl=0)
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
        # --- 열 번호로 강제 지정 (제목 이름이 달라도 작동함) ---
        # 0: Deliver, 1: Clinic, 2: Doctor, 3: Arch, 4: Material
        
        # 1. 클리닉 목록 (1번 열)
        clinics = sorted([c for c in ref_df.iloc[:, 1].unique() if c and c != 'nan' and c != 'None' and c != 'Clinic'])
        
        with st.form(key="final_fix_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                # 클리닉 선택
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clinics)
                
                # --- 닥터 필터링 (열 번호 방식) ---
                if selected_clinic != "선택하세요":
                    # 1번 열이 선택한 클리닉인 행을 찾아서, 그 행의 2번 열(닥터)을 가져옴
                    matched_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic].iloc[:, 2].unique().tolist()
                    doctor_options = sorted([d for d in matched_docs if d and d != 'nan' and d != 'None' and d != 'Doctor'])
                    
                    if not doctor_options:
                        doctor_options = ["등록된 의사 없음"]
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
                patient = st.text_input("D: Patient Name")

            with col2:
                date_completed = st.date_input("G: Date Completed", datetime.now())
                
                # 3번 열에서 Arch 옵션 추출
                arch_opts = sorted([a for a in ref_df.iloc[:, 3].unique() if a and a != 'nan' and a != 'None' and a != 'Arch'])
                selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                # 4번 열에서 Material 옵션 추출
                mat_opts = sorted([m for m in ref_df.iloc[:, 4].unique() if m and m != 'nan' and m != 'None' and m != 'Material'])
                selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual", "Soft"])
            
            notes = st.text_area("F: Check List")
            
            submit_btn = st.form_submit_button("✅ 구글 시트에 저장", use_container_width=True)
            
            if submit_btn:
                if selected_clinic == "선택하세요" or not patient or "선택하세요" in str(selected_doctor):
                    st.warning("필수 항목(클리닉, 닥터, 환자이름)을 모두 입력하세요.")
                else:
                    # 메인 시트에 저장할 데이터
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
                        updated_main = pd.concat([df, new_entry], ignore_index=True)
                        conn.update(data=updated_main)
                        st.success(f"🎉 {patient}님 저장 성공!")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

# (정산 및 검색 탭 생략 - 위 등록 기능이 성공하면 추가해 드릴게요)
