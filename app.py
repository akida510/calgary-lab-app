import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 2. 보안 키 줄바꿈 보정
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 3. 데이터 로드 (캐시 제거하여 실시간 반영)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    main_df = conn.read(ttl=0)
    ref_df = conn.read(worksheet="Reference", ttl=0)
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
        
        # 클리닉 목록 추출 (B열 = Index 1)
        all_clinics = sorted([c for c in ref_temp.iloc[:, 1].unique() if c and c.lower() not in ['nan', 'none', 'clinic', 'deliver', '']])
        
        with st.form(key="form_final_v20", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case #")
                selected_clinic = st.selectbox("B: Clinic 선택", options=["선택하세요"] + all_clinics)
                
                # 닥터 필터링 로직 (무조건 매칭 방식)
                if selected_clinic != "선택하세요":
                    # B열이 선택된 클리닉인 행을 찾아서 C열(Index 2)의 값을 가져옴
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
                
                # D열(Index 3)에서 Arch 옵션 추출
                arch_vals = ref_temp.iloc[:, 3].unique()
                arch_opts = sorted([a for a in arch_vals if a and a.lower() not in ['nan', 'none', 'arch', '']])
                selected_arch = st.radio("Arch", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                # E열(Index 4)에서 Material 옵션 추출
                mat_vals = ref_temp.iloc[:, 4].unique()
                mat_opts = sorted([m for m in mat_vals if m and m.lower() not in ['nan', 'none', 'material', '']])
                selected_material = st.selectbox("Material", options=mat_opts if mat_opts else ["Thermo", "Dual"])
            
            notes = st.text_area("F: Check List / 리메이크 사유")
            
            if st.form_submit_button("✅ 구글 시트에 저장", use_container_width=True):
                if selected_clinic == "선택하세요" or not patient or "선택하세요" in str(selected_doctor):
                    st.warning("필수 항목(클리닉, 닥터, 환자이름)을 모두 입력하세요.")
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
                        st.success(f"🎉 {patient}님 데이터가 성공적으로 저장되었습니다!")
                        st.balloons()
                    except Exception as e:
                        st.error(f"저장 중 오류 발생: {e}")

with tab2:
    st.info("데이터가 충분히 쌓이면 월별 수당 정산 화면이 여기에 표시됩니다.")

with tab3:
    st.subheader("🔍 환자 검색")
    search_q = st.text_input("환자 이름이나 케이스 번호를 입력하세요")
    if search_q:
        result = main_df[main_df.apply(lambda row: search_q.lower() in str(row.values).lower(), axis=1)]
        st.dataframe(result, use_container_width=True)
