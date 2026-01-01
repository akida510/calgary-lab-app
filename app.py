import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# --- 보안 키 줄바꿈 강제 교정 (폰 작업 에러 방지) ---
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# --- 구글 시트 연결 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 데이터 로드 (캐시 사용으로 속도 향상)
    @st.cache_data(ttl=60)
    def load_data():
        main_df = conn.read(ttl=0)
        ref_df = conn.read(worksheet="Reference", ttl=0)
        return main_df, ref_df

    df, ref_df = load_data()
    st.success("✅ 연결 성공! 실시간 데이터를 불러왔습니다.")

except Exception as e:
    st.error(f"⚠️ 연결 오류가 발생했습니다: {e}")
    st.stop()

# --- 화면 구성 ---
st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

# --- 1. 케이스 등록 탭 ---
with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # Reference 시트 열 매핑 (0부터 시작)
        # B열(1): Clinic, C열(2): Doctor, D열(3): Arch(상/하악), E열(4): Material(재질), F열(5): Check List
        
        clinics = sorted(ref_df.iloc[:, 1].dropna().unique().tolist())
        arch_list = ref_df.iloc[:, 3].dropna().unique().tolist()
        mat_list = ref_df.iloc[:, 4].dropna().unique().tolist()
        
        with st.form(key="entry_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case # (케이스 번호)")
                selected_clinic = st.selectbox("B: Clinic (클리닉)", options=["선택하세요"] + clinics)
                
                # 닥터 필터링 (선택한 클리닉에 해당되는 닥터만 표시)
                if selected_clinic != "선택하세요":
                    filtered_docs = ref_df[ref_df.iloc[:, 1] == selected_clinic].iloc[:, 2].dropna().unique().tolist()
                else:
                    filtered_docs = []
                selected_doctor = st.selectbox("C: Doctor (닥터)", options=filtered_docs)
                
                patient = st.text_input("D: Patient Name (환자이름)")

            with col2:
                date_completed = st.date_input("G: Date Completed (완료일)", datetime.now())
                selected_arch = st.radio("D(Note): Arch (상/하악)", options=arch_list if arch_list else ["Upper", "Lower"], horizontal=True)
                selected_material = st.selectbox("E(Note): Material (재질)", options=mat_list if mat_list else ["Thermo", "Dual", "Soft"])
            
            check_list_reason = st.text_area("F: Check List (참고사항 / 리메이크 사유)")
            
            submit_button = st.form_submit_button("✅ 구글 시트에 저장", use_container_width=True)
            
            if submit_button:
                if selected_clinic == "선택하세요" or not patient:
                    st.warning("클리닉과 환자 이름은 필수 입력 항목입니다.")
                else:
                    # 저장할 데이터 행 구성
                    new_row = pd.DataFrame([{
                        "Case #": case_no,
                        "Clinic": selected_clinic,
                        "Doctor": selected_doctor,
                        "Patient": patient,
                        "Arch": selected_arch,
                        "Material": selected_material,
                        "Date": date_completed.strftime('%Y-%m-%d'),
                        "Notes": check_list_reason
                    }])
                    
                    # 시트 업데이트
                    updated_df = pd.concat([df, new_row], ignore_index=True)
                    conn.update(data=updated_df)
                    st.success(f"🎉 {patient}님의 데이터가 성공적으로 저장되었습니다!")
                    st.cache_data.clear() # 데이터 새로고침

# --- 2. 수당 정산 및 3. 검색 탭 (기존 로직 유지 가능) ---
with tab2:
    st.info("수당 정산 기능은 데이터가 쌓인 후 활성화됩니다.")

with tab3:
    st.subheader("환자 및 케이스 검색")
    search_q = st.text_input("검색어 입력 (이름 또는 케이스 번호)")
    if search_q:
        search_result = df[df.apply(lambda row: search_q in str(row.values), axis=1)]
        st.dataframe(search_result)
