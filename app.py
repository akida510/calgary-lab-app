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
    @st.cache_data(ttl=10) # 닥터 목록 수정을 위해 캐시 시간을 줄였습니다.
    def load_data():
        # 메인 데이터와 Reference 시트 읽기
        # 시트 이름 'Reference' 대소문자 주의!
        main_df = conn.read(ttl=0)
        ref_df = conn.read(worksheet="Reference", ttl=0)
        return main_df, ref_df

    df, ref_df = load_data()

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
        # 1. 시트 데이터 정리 (공백 제거)
        ref_df.columns = [c.strip() for c in ref_df.columns] # 제목 공백 제거
        ref_df['Clinic'] = ref_df['Clinic'].fillna('').astype(str).str.strip()
        ref_df['Doctor'] = ref_df['Doctor'].fillna('').astype(str).str.strip()
        
        # 2. 클리닉 목록 (B열)
        clinics = sorted([c for c in ref_df['Clinic'].unique() if c])
        
        with st.form(key="entry_form_v5", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                case_no = st.text_input("A: Case # (케이스 번호)")
                
                # 클리닉 선택
                selected_clinic = st.selectbox("B: Clinic (클리닉)", options=["선택하세요"] + clinics)
                
                # --- 닥터 필터링 로직 (핵심 수정) ---
                if selected_clinic != "선택하세요":
                    # 선택된 클리닉에 해당하는 모든 닥터를 리스트화
                    doctor_options = sorted(ref_df[ref_df['Clinic'] == selected_clinic]['Doctor'].unique().tolist())
                else:
                    doctor_options = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("C: Doctor (닥터)", options=doctor_options)
                patient = st.text_input("D: Patient Name (환자이름)")

            with col2:
                date_completed = st.date_input("G: Date Completed (완료일)", datetime.now())
                
                # D열(Note)에서 상/하악 옵션 추출
                arch_opts = [a for a in ref_df.iloc[:, 3].dropna().unique() if a]
                selected_arch = st.radio("D(Note): Arch (상/하악)", options=arch_opts if arch_opts else ["Max", "Mand"], horizontal=True)
                
                # E열(Note)에서 재질 옵션 추출
                mat_opts = [m for m in ref_df.iloc[:, 4].dropna().unique() if m]
                selected_material = st.selectbox("E(Note): Material (재질)", options=mat_opts if mat_opts else ["Thermo", "Dual", "Soft"])
            
            check_list_reason = st.text_area("F: Check List (참고사항 / 리메이크 사유)")
            
            submit_button = st.form_submit_button("✅ 구글 시트에 저장", use_container_width=True)
            
            if submit_button:
                if selected_clinic == "선택하세요" or not patient or selected_doctor == "클리닉을 먼저 선택하세요":
                    st.warning("클리닉, 닥터, 환자 이름은 필수입니다.")
                else:
                    # 저장할 데이터 행 (사장님의 메인 시트 제목에 맞춰 이름을 수정하세요)
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
                    try:
                        updated_df = pd.concat([df, new_row], ignore_index=True)
                        conn.update(data=updated_df)
                        st.success(f"🎉 {patient}님의 데이터가 성공적으로 저장되었습니다!")
                        st.cache_data.clear() # 저장 후 새 데이터를 위해 캐시 삭제
                    except Exception as save_error:
                        st.error(f"저장 중 오류 발생: {save_error}")

# --- 2. 수당 정산 탭 ---
with tab2:
    st.subheader("💰 수당 정산")
    if not df.empty:
        # 날짜 컬럼을 날짜 형식으로 변환 (메인 시트의 완료일 열 이름이 'Date'라고 가정)
        try:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            this_month = datetime.now().month
            this_year = datetime.now().year
            
            month_data = df[(df['Date'].dt.month == this_month) & (df['Date'].dt.year == this_year)]
            count = len(month_data)
            
            c1, c2 = st.columns(2)
            c1.metric("이번 달 작업 개수", f"{count} 개")
            # 320개 초과 시 개당 30불 계산 예시
            extra = max(0, count - 320)
            c2.metric("추가 수당 대상", f"{extra} 개")
            
            st.dataframe(month_data, use_container_width=True)
        except:
            st.info("정산할 데이터가 아직 없거나 시트 구조가 다릅니다.")

# --- 3. 환자 검색 탭 ---
with tab3:
    st.subheader("🔍 환자 검색")
    search_q = st.text_input("환자 이름 또는 케이스 번호 입력")
    if search_q:
        search_result = df[df.apply(lambda row: search_q.lower() in str(row.values).lower(), axis=1)]
        st.dataframe(search_result, use_container_width=True)
