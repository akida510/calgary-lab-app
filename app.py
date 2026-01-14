import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# CSS 디자인
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

# 2. 데이터베이스 연결 (수정 불가능한 Secrets 우회 로직)
@st.cache_resource(ttl=600)
def get_db_connection():
    try:
        # Secrets를 직접 수정하지 않고, 복사본을 만들어 수정한 뒤 연결에 사용
        conf = st.secrets["connections"]["gsheets"].to_dict()
        if "private_key" in conf:
            # \n 치환 및 앞뒤 공백 제거
            conf["private_key"] = conf["private_key"].replace("\\n", "\n").strip()
        
        # 💡 수정한 설정값(conf)을 풀어서(**) 전달
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

# 세션 상태 관리
if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# 4. 화면 탭 구성
tab1, tab2, tab3 = st.tabs(["📝 신규 등록", "📊 실적 보기", "🔍 검색"])

with tab1:
    st.subheader("📸 의뢰서 스캔")
    scan_file = st.file_uploader("의뢰서 사진 업로드", type=["jpg", "jpeg", "png"], key=f"scan_{it_key}")
    
    if scan_file:
        if st.button("✨ AI 정보 추출"):
            with st.spinner("분석 중..."):
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
    
    # 입력 폼
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + it_key)
    patient = c1.text_input("환자명", key="p" + it_key)
    sel_clinic = c2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key="cl" + it_key)
    sel_doctor = c3.selectbox("의사", ["선택"] + doctors + ["➕ 직접"], key="dr" + it_key)

    with st.expander("생산 상세 및 날짜 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo","Dual","Soft","Hard"], key="m" + it_key)
        rd = d2.date_input("접수일", date.today(), key="rd" + it_key)
        due = d3.date_input("마감일", date.today()+timedelta(7), key="du" + it_key)
        shp = d3.date_input("출고일", due-timedelta(2), key="sh" + it_key)

    with st.expander("📂 추가 메모 및 사진", expanded=True):
        col_i, col_m = st.columns([0.6, 0.4])
        # 사진 업로드 버튼 복구
        st.file_uploader("참고용 사진", type=["jpg", "png"], key=f"refimg_{it_key}")
        memo = col_m.text_area("메모", key="memo" + it_key, height=120)

    if st.button("🚀 데이터 저장"):
        if not case_no: st.warning("Case Number를 입력하세요.")
        else:
            st.success(f"{case_no} 저장 완료!")
            st.session_state.it += 1
            st.rerun()

with tab2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with tab3:
    q = st.text_input("검색어 (이름 또는 번호)")
    if q:
        st.dataframe(main_df[main_df.apply(lambda row: q in row.astype(str).values, axis=1)], use_container_width=True)
