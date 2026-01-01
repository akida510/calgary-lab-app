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
    # 시트 전체를 읽어옴 (빈 칸 포함)
    ref_df = conn.read(worksheet="Reference", ttl=0)
except Exception as e:
    st.error(f"연결 오류: {e}")
    st.stop()

st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # 데이터 클리닝 (문자열 변환 및 공백 제거)
        ref_temp = ref_df.astype(str).apply(lambda x: x.str.strip())
        
        # [진단용] 시트에서 읽은 열 이름을 화면에 잠시 보여줌 (나중에 삭제)
        st.write("---")
        st.caption(f"검색된 열 이름: {list(ref_temp.columns)}")
        
        # B열(Index 1) 목록 추출
        all_clinics = sorted([c for c in ref_temp.iloc[:, 1].unique() if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', '']])
        
        with st.form(key="form_v17"):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + all_clinics)
                
                # --- 닥터 매칭 로직 (진단 모드) ---
                if selected_clinic != "선택하세요":
                    # 선택된 클리닉이 있는 행 전체를 찾음
                    matched_rows = ref_temp[ref_temp.iloc[:, 1] == selected_clinic]
                    
                    # [진단용] 매칭된 행의 개수를 보여줌
                    st.write(f"찾은 데이터 개수: {len(matched_rows)}개")
                    
                    doctor_list = matched_rows.iloc[:, 2].unique().tolist()
                    doctor_options = sorted([d for d in doctor_list if d and d.lower() not in ['nan', 'none', 'doctor', '']])
                    
                    if not doctor_options:
                        doctor_options = ["의사 정보 없음"]
                        # [진단용] 왜 없는지 데이터 일부 표시
                        st.write("C열 데이터 샘플:", matched_rows.iloc[:, 2].tolist()[:3])
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor 선택", options=doctor_options)
                patient = st.text_input("D: Patient Name")

            with col2:
                date_completed = st.date_input("G: Date Completed", datetime.now())
                
                # Arch/Material 옵션 (D열, E열)
                arch_opts = sorted([a for a in ref_temp.iloc[:, 3].unique() if a and a.lower() not in ['nan', 'none', 'arch', '']])
                selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                mat_opts = sorted([m for m in ref_temp.iloc[:, 4].unique() if m and m.lower() not in ['nan', 'none', 'material', '']])
                selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])
            
            notes = st.text_area("F: Check List")
            
            if st.form_submit_button("✅ 저장"):
                if selected_clinic == "선택하세요" or not patient:
                    st.warning("항목을 입력하세요.")
                else:
                    # 저장 로직 (이전과 동일)
                    new_row = pd.DataFrame([{"Case #": case_no, "Clinic": selected_clinic, "Doctor": selected_doctor, "Patient": patient, "Arch": selected_arch, "Material": selected_material, "Date": date_completed.strftime('%Y-%m-%d'), "Notes": notes}])
                    updated_df = pd.concat([main_df, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success("저장 성공!")
