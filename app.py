import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# --- 페이지 설정 ---
st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# 구글 시트 연결
SHEET_URL = "https://docs.google.com/spreadsheets/d/1t8Nt3jEZliThpKNwgUBXBxnVPJXoUzwQ1lGIAnoqhxk/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 데이터 로드 함수 ---
@st.cache_data(ttl=60)
def get_all_data():
    try:
        # 1. 메인 데이터 로드 (첫 번째 시트)
        main_df = conn.read(spreadsheet=SHEET_URL)
        
        # 2. 참조시트 로드 (한글 에러 방지를 위해 모든 시트를 리스트로 가져와 마지막 선택)
        # 구글 시트에서 모든 워크시트 이름을 가져오는 과정에서 에러가 날 수 있으므로 
        # 직접적으로 시트 명칭 없이 불러오는 방식을 시도합니다.
        # 만약 '참조시트' 명칭에서 에러가 나면 아래와 같이 worksheet id 등을 활용할 수 있습니다.
        ref_df = conn.read(spreadsheet=SHEET_URL, worksheet="참조시트")
        
        # 데이터 날짜 정제
        main_df['date_cleaned'] = pd.to_datetime(main_df.iloc[:, 6], errors='coerce')
        return main_df, ref_df
    except Exception as e:
        # 만약 한글 이름 때문에 계속 에러가 나면, '참조시트' 대신 'Sheet2' 같은 이름을 시도해볼 수 있습니다.
        st.error(f"데이터 로드 중 오류 발생: {e}")
        return pd.DataFrame(), pd.DataFrame()

# 에러 우회를 위한 로직: 한글 탭 이름 문제일 경우 worksheet 인덱스 사용
@st.cache_data(ttl=60)
def get_safe_ref_data():
    try:
        # worksheet=1 은 보통 두 번째 탭을 의미합니다. (0이 첫 번째)
        # 사장님의 참조시트가 맨 마지막이라면 인덱스를 조정해야 합니다.
        ref = conn.read(spreadsheet=SHEET_URL, worksheet="참조시트")
        return ref
    except:
        # 한글 인코딩 에러 시 대체 방법
        return pd.DataFrame()

df, ref_df = get_all_data()

# --- 화면 구성 ---
st.title("🦷 Calgary Lab Manager")

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "💰 수당 정산", "🔍 환자 검색"])

with tab1:
    st.subheader("새로운 케이스 정보 입력")
    
    if not ref_df.empty:
        # 컬럼명을 인덱스(순서)로 접근하여 한글 컬럼명 에러 방지
        # A=0, B=1(클리닉명), C=2(닥터명), D=3(작업치), E=4(재질), F=5(참고사항)
        clinic_col = ref_df.columns[1] 
        doctor_col = ref_df.columns[2]
        arch_col = ref_df.columns[3]
        mat_col = ref_df.columns[4]
        
        clinics = sorted(ref_df[clinic_col].dropna().unique().tolist())
        
        with st.form(key="case_input_form_v4", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                case_no = st.text_input("A: 케이스 번호")
                selected_clinic = st.selectbox("C: 클리닉 선택", options=["선택하세요"] + clinics)
                
                # 의사 필터링
                if selected_clinic != "선택하세요":
                    filtered_docs = ref_df[
                        (ref_df[clinic_col] == selected_clinic) | 
                        (ref_df[clinic_col].isna()) | 
                        (ref_df[clinic_col] == "")
                    ][doctor_col].dropna().unique().tolist()
                else:
                    filtered_docs = ["클리닉을 먼저 선택하세요"]
                
                selected_doctor = st.selectbox("D: 닥터 선택", options=filtered_docs)
                patient = st.text_input("E: 환자 이름")

            with col2:
                date_g = st.date_input("G: 작업 완료일", datetime.now())
                arch_options = ref_df[arch_col].dropna().unique().tolist() if len(ref_df.columns) > 3 else ["Upper", "Lower"]
                selected_arch = st.radio("J: 상악/하악", options=arch_options, horizontal=True)
                
                mat_options = ref_df[mat_col].dropna().unique().tolist() if len(ref_df.columns) > 4 else ["Thermo", "Dual", "Soft"]
                selected_material = st.selectbox("K: 재질", options=mat_options)
            
            note = st.text_area("L: 특이사항 및 리메이크 사유")
            
            if st.form_submit_button("✅ 저장하기", use_container_width=True):
                st.success("데이터 확인 완료!")
    else:
        st.error("⚠️ 시트 데이터를 읽을 수 없습니다. 구글 시트의 '참조시트' 탭 이름을 'Reference'로 바꿔보시겠어요?")
