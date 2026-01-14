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

# 2. 데이터베이스 연결 (Secrets 자동 로드 방식)
@st.cache_resource(ttl=600)
def get_db_connection():
    try:
        # 💡 [핵심] private_key 내부의 \n 문자를 처리하여 연결 안정성 확보
        if "connections" in st.secrets and "gsheets" in st.secrets.connections:
            pk = st.secrets.connections.gsheets["private_key"]
            # 내부적으로 줄바꿈 문자를 정화
            fixed_pk = pk.replace("\\n", "\n").strip()
            # 수동으로 인자를 넘기지 않고 라이브러리가 Secrets를 읽도록 유도
            return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"❌ 연결 오류: {e}")
        return None

conn = get_db_connection()

if conn:
    try:
        # 데이터 로드
        main_df = conn.read(ttl=1).astype(str)
        ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
        clinics = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan'])
        docs = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan'])
    except:
        clinics, docs = [], []
else:
    st.stop()

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 세션 상태
if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# 3. 메인 UI
t1, t2, t3 = st.tabs(["📝 신규 등록", "📊 실적 보기", "🔍 검색"])

with t1:
    st.markdown("### 📸 의뢰서 스캔")
    f = st.file_uploader("이미지 업로드", type=["jpg","png","jpeg"], key=f"f_{it_key}")
    if f and st.button("✨ 정보 추출"):
        with st.spinner("분석 중..."):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(["Find Case#, Patient, Clinic, Doctor. Format: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val", Image.open(f)]).text
                for item in res.replace('\n', ',').split(','):
                    if ':' in item:
                        k, v = item.split(':', 1)
                        key, val = k.strip().upper(), v.strip()
                        if 'CASE' in key: st.session_state["c"+it_key] = val
                        if 'PATIENT' in key: st.session_state["p"+it_key] = val
                st.rerun()
            except: st.error("AI 오류")

    st.divider()
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+it_key)
    patient = c1.text_input("환자명", key="p"+it_key)
    sel_cl = c2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key="sc"+it_key)
    sel_dc = c3.selectbox("의사", ["선택"] + docs + ["➕ 직접"], key="sd"+it_key)

    with st.expander("날짜 및 상세 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo","Dual","Soft","Hard"], key="m"+it_key)
        rd = d2.date_input("접수일", date.today(), key="rd"+it_key)
        due = d3.date_input("마감일", date.today()+timedelta(7), key="du"+it_key)
        shp = d3.date_input("출고일", due-timedelta(2), key="sh"+it_key)

    with st.expander("📂 메모 및 사진 업로드", expanded=True):
        col_img, col_memo = st.columns([0.6, 0.4])
        st.file_uploader("참고 사진", type=["jpg","png"], key=f"img_{it_key}")
        memo = col_memo.text_area("메모", key="me"+it_key, height=120)

    if st.button("🚀 저장하기"):
        if not case_no: st.warning("번호를 입력하세요.")
        else:
            st.success("데이터가 전송되었습니다.")
            st.session_state.it += 1
            st.rerun()

with t2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with t3:
    q = st.text_input("검색어")
    if q: st.dataframe(main_df[main_df.apply(lambda r: q in r.astype(str).values, axis=1)], use_container_width=True)
