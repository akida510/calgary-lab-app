import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-box {
        background-color: #1a1c24; padding: 25px; border-radius: 12px;
        border: 1px solid #30363d; margin-bottom: 25px; text-align: center;
    }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 8px; }
    [data-testid="stWidgetLabel"] p { color: #ffffff !important; font-weight: 600 !important; }
    </style>
    <div class="header-box">
        <h1 style="color:white; margin:0; font-size: 28px;">🦷 Skycad Dental Lab Manager</h1>
        <p style="color:#8b949e; margin:5px 0 0 0;">Secure Cloud Management System</p>
    </div>
    """, unsafe_allow_html=True)

# 2. 데이터베이스 연결 (충돌 방지 로직)
@st.cache_resource(ttl=600)
def get_db_connection():
    try:
        # Secrets 설정값을 딕셔너리로 복사
        conf = st.secrets["connections"]["gsheets"].to_dict()
        
        # private_key 내부의 \n 문자를 실제 줄바꿈으로 변경하여 가공
        if "private_key" in conf:
            conf["private_key"] = conf["private_key"].replace("\\n", "\n").strip()
        
        # 💡 핵심: 딕셔너리에서 'type'을 제거한 뒤, st.connection의 첫 번째 인자로 넘겨 중복 방지
        conn_type = conf.pop("type", "service_account")
        
        # 가공된 conf 딕셔너리를 사용하여 연결
        return st.connection("gsheets", type=GSheetsConnection, **conf)
    except Exception as e:
        st.error(f"❌ 데이터베이스 연결 실패: {e}")
        return None

conn = get_db_connection()

if conn is not None:
    try:
        main_df = conn.read(ttl=1).astype(str)
        ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
        clinics = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan'])
        doctors = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan'])
    except:
        clinics, doctors = [], []
else:
    st.stop()

# 3. AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 세션 상태 관리 (입력 초기화용)
if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# 4. 화면 구성
tab1, tab2, tab3 = st.tabs(["📝 신규 등록", "📊 실적 보기", "🔍 통합 검색"])

with tab1:
    st.markdown("### 📸 의뢰서 스캔")
    scan_file = st.file_uploader("이미지를 업로드하세요", type=["jpg", "png", "jpeg"], key=f"scan_{it_key}")
    
    if scan_file:
        if st.button("✨ 정보 자동 추출"):
            with st.spinner("AI 분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(scan_file)
                    prompt = f"Case#, Patient, Clinic, Doctor 찾기. 목록:{clinics}, {doctors}. 형식: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"
                    res = model.generate_content([prompt, img]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            key, val = k.strip().upper(), v.strip()
                            if 'CASE' in key: st.session_state["c"+it_key] = val
                            if 'PATIENT' in key: st.session_state["p"+it_key] = val
                            if 'CLINIC' in key: st.session_state["cl"+it_key] = val
                            if 'DOCTOR' in key: st.session_state["dr"+it_key] = val
                    st.rerun()
                except: st.error("AI 인식 실패")

    st.divider()
    
    # 입력 필드 레이아웃
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + it_key)
    patient = c1.text_input("환자명", key="p" + it_key)
    sel_clinic = c2.selectbox("치과 선택", ["선택"] + clinics + ["➕ 직접 입력"], key="cl" + it_key)
    sel_doctor = c3.selectbox("의사 선택", ["선택"] + doctors + ["➕ 직접 입력"], key="dr" + it_key)

    with st.expander("생산 정보 및 날짜 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질 (Material)", ["Thermo","Dual","Soft","Hard"], key="m" + it_key)
        rd = d2.date_input("접수일", date.today(), key="rd" + it_key)
        due = d3.date_input("마감일 (Due)", date.today()+timedelta(7), key="du" + it_key)
        # 마감일 기준 2일 전 자동 출고일 계산
        shp = d3.date_input("출고일 (Shipping)", due-timedelta(2), key="sh" + it_key)

    with st.expander("📂 추가 메모 및 사진 업로드", expanded=True):
        col_img, col_memo = st.columns([0.6, 0.4])
        # [복구] 사진 업로드 버튼
        st.file_uploader("참고 사진 첨부", type=["jpg", "png"], key=f"ref_{it_key}")
        memo = col_memo.text_area("메모", key="memo" + it_key, height=130)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.warning("Case Number를 확인하세요.")
        else:
            st.success(f"{case_no} 데이터가 성공적으로 처리되었습니다.")
            st.session_state.it += 1
            st.rerun()

with tab2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with tab3:
    q = st.text_input("검색 (환자명 또는 번호)")
    if q:
        st.dataframe(main_df[main_df.apply(lambda row: q in row.astype(str).values, axis=1)], use_container_width=True)
