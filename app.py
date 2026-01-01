import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# --- 보안 키 줄바꿈 강제 교정 ---
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# --- 구글 시트 연결 ---
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    @st.cache_data(ttl=5) # 빠른 확인을 위해 캐시를 더 줄였습니다.
    def load_data():
        main_df = conn.read(ttl=0)
        # Reference 시트를 읽어온 후 빈 행을 즉시 제거합니다.
        ref_df = conn.read(worksheet="Reference", ttl=0).dropna(subset=['Clinic', 'Doctor'], how='all')
        return main_df, ref_df

    df, ref_df = load_data()
    st.success("✅ 시스템 준비 완료")

except Exception as e:
    st.error(f"⚠️ 연결 오류: {e}")
    st.stop()

# --- 화면 구성 ---
st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

# --- 1. 케이스 등록 탭 ---
with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # 데이터 클리닝: 모든 텍스트의 앞뒤 공백 제거
        ref_df['Clinic'] = ref_df['Clinic'].fillna('').astype(str).str.strip()
        ref_df['Doctor'] = ref_df['Doctor'].fillna('').astype(str).str.strip()
        
        # 실제 데이터가 있는 클리닉 목록 추출
        clinics = sorted([c for c in ref_df['Clinic'].unique() if c and c != 'nan'])
        
        with st.form(key="entry_form_final", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case # (케이스 번호)")
                
                # 클리닉 선택
                selected_clinic = st.selectbox("B: Clinic (클리닉)", options=["선택하세요"] + clinics)
                
                # --- 닥터 필터링 로직 (빈 줄 무시하고 매칭) ---
                if selected_clinic != "선택하세요":
                    # 선택된 클리닉 이름과 일치하는 행의 닥터들만 추출
                    doctor_options = sorted(ref_df[ref_df['Clinic'] == selected_clinic]['Doctor'].unique().tolist())
                    # 혹시나 리스트가 비어있을 경우를 대비
                    if not doctor_options:
                        doctor_options = ["등록된 의사 없음"]
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor (닥터)", options=doctor_options)
                patient = st.text_input("D: Patient Name (환자이름)")

            with col2:
                date_completed = st.date_input("G: Date Completed (완료일)", datetime.now())
                
                # D열과 E열 옵션 (Reference 시트에서 가져오기)
                arch_opts = [a for a in ref_df.iloc[:, 3].dropna().unique() if str(a).strip()]
                selected_arch = st.radio("D(Note): Arch (상/하악)", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                mat_opts = [m for m in ref_df.iloc[:, 4].dropna().unique() if str(m).strip()]
                selected_material = st.selectbox("E(Note): Material (재질)", options=mat_opts if mat_opts else ["Thermo", "Dual", "Soft"])
            
            check_list_reason = st.text_area("F: Check List (참고사항 / 리메이크 사유)")
            
            submit_button = st.form_submit_button("✅ 구글 시트에 저장", use_container_width=True)
            
            if submit_button:
                if selected_clinic == "선택하세요" or not patient or "선택하세요" in selected_doctor:
                    st.warning("필수 항목(클리닉, 닥터, 환자이름)을 모두 입력해 주세요.")
                else:
                    # 메인 시트 저장 로직
                    new_entry = pd.DataFrame([{
                        "Case #": case_no,
                        "Clinic": selected_clinic,
                        "Doctor": selected_doctor,
                        "Patient": patient,
                        "Arch": selected_arch,
                        "Material": selected_material,
                        "Date": date_completed.strftime('%Y-%m-%d'),
                        "Notes": check_list_reason
                    }])
                    
                    try:
                        # 기존 데이터 df와 결합 (열 순서 자동 매칭)
                        updated_main = pd.concat([df, new_entry], ignore_index=True)
                        conn.update(data=updated_main)
                        st.success(f"🎉 {patient}님의 케이스가 시트에 저장되었습니다!")
                        st.cache_data.clear() # 다음 입력을 위해 캐시 초기화
                    except Exception as e:
                        st.error(f"저장 실패: {e}")

# (정산 및 검색 탭 로직은 이전과 동일)
