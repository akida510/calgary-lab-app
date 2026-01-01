import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 보안 키 보정
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    main_df = conn.read(ttl=0)
    # Reference 시트를 읽고 모든 칸의 앞뒤 공백을 즉시 제거
    ref_df = conn.read(worksheet="Reference", ttl=0).astype(str).apply(lambda x: x.str.strip())
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # B열(Index 1)에서 클리닉 목록 추출
        all_clinics = ref_df.iloc[:, 1].unique().tolist()
        clean_clinics = sorted([c for c in all_clinics if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', '']])
        
        with st.form(key="form_v16", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                # 클리닉 선택
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + clean_clinics)
                
                # --- 닥터 매칭 로직 (강력한 검색 방식) ---
                if selected_clinic != "선택하세요":
                    # B열에서 선택한 클리닉과 '포함' 관계에 있는 모든 행을 찾음
                    # (정확히 일치하지 않아도 글자가 들어있으면 찾아냄)
                    mask = ref_df.iloc[:, 1] == selected_clinic
                    doctor_list = ref_df[mask].iloc[:, 2].unique().tolist()
                    
                    # 'Doctor' 제목이나 빈값 제외
                    doctor_options = sorted([d for d in doctor_list if d and d.lower() not in ['nan', 'none', 'doctor', '']])
                    
                    if not doctor_options:
                        doctor_options = ["의사 정보 없음 (시트 확인 필요)"]
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
                patient = st.text_input("D: Patient Name")

            with col2:
                date_completed = st.date_input("G: Date Completed", datetime.now())
                
                # Arch(D열) & Material(E열) 옵션 추출
                arch_opts = sorted([a for a in ref_df.iloc[:, 3].unique() if a and a.lower() not in ['nan', 'none', 'arch', '']])
                selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                mat_opts = sorted([m for m in ref_df.iloc[:, 4].unique() if m and m.lower() not in ['nan', 'none', 'material', '']])
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
                        updated_main = pd.concat([main_df, new_entry], ignore_index=True)
                        conn.update(data=updated_main)
                        st.success(f"{patient}님 저장 성공!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"저장 실패: {e}")
    else:
        st.warning("데이터를 불러올 수 없습니다. Reference 시트 이름을 확인하세요.")

with tab2:
    st.info("데이터 축적 후 활성화됩니다.")

with tab3:
    st.info("환자 검색 탭입니다.")
