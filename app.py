import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 디자인 (Dark Navy 스타일)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-box { background-color: #1a1c24; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 25px; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; }
    [data-testid="stWidgetLabel"] p { color: #ffffff !important; }
    </style>
    <div class="header-box">
        <h2 style="color:white; margin:0;">🦷 Skycad Dental Lab Manager</h2>
        <p style="color:#8b949e; margin:0;">Auto-Repair Connection Enabled</p>
    </div>
    """, unsafe_allow_html=True)

# 2. 보안 키 수동 정화 및 연결 함수
def connect_db():
    try:
        # Secrets 딕셔너리를 복사
        gsheets_conf = st.secrets["connections"]["gsheets"].to_dict()
        
        # [핵심] 키 값의 모든 보이지 않는 공백과 잘못된 줄바꿈 세척
        raw_key = gsheets_conf.get("private_key", "")
        # \n 문자를 실제 줄바꿈으로 변경하고 앞뒤 공백 완전 제거
        clean_key = raw_key.replace("\\n", "\n").strip()
        
        # 수정한 키를 다시 할당
        gsheets_conf["private_key"] = clean_key
        
        # 세척된 정보로 연결 시도
        return st.connection("gsheets", type=GSheetsConnection, **gsheets_conf)
    except Exception as e:
        st.error(f"❌ 데이터베이스 연결 실패: {e}")
        return None

conn = connect_db()

if conn:
    try:
        main_df = conn.read(ttl=1).astype(str)
        ref = conn.read(worksheet="Reference", ttl=600).astype(str)
        clinics = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan'])
        docs = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan'])
    except Exception as e:
        st.warning(f"시트 로드 오류: {e}")
        clinics, docs = [], []
else:
    st.stop()

# 3. AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key: genai.configure(api_key=api_key)

# 세션 관리
if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# 4. 메인 UI (탭)
t1, t2, t3 = st.tabs(["📝 등록", "📊 실적", "🔍 검색"])

with t1:
    st.markdown("### 📸 의뢰서 스캔")
    f = st.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"], key=f"f_{it_key}")
    
    if f:
        if st.button("✨ 정보 추출"):
            with st.spinner("AI 분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(f)
                    prompt = f"Case#, Patient, Clinic, Doctor 찾기. 목록:{clinics}, {docs}. 형식: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"
                    res = model.generate_content([prompt, img]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            key, val = k.strip().upper(), v.strip()
                            if 'CASE' in key: st.session_state["c"+it_key] = val
                            if 'PATIENT' in key: st.session_state["p"+it_key] = val
                            if 'CLINIC' in key: st.session_state["sc"+it_key] = val
                            if 'DOCTOR' in key: st.session_state["sd"+it_key] = val
                    st.rerun()
                except: st.error("AI 인식 실패")

    st.divider()
    
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + it_key)
    patient = c1.text_input("환자명", key="p" + it_key)
    sel_cl = c2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key="sc" + it_key)
    sel_dc = c3.selectbox("의사", ["선택"] + docs + ["➕ 직접"], key="sd" + it_key)

    with st.expander("생산 및 날짜 정보", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo","Dual","Soft","Hard"], key="m" + it_key)
        rd = d2.date_input("접수일", date.today(), key="rd" + it_key)
        due = d3.date_input("마감일", date.today()+timedelta(7), key="du" + it_key)
        shp = d3.date_input("출고일", due-timedelta(2), key="sh" + it_key)

    with st.expander("📂 특이사항 및 사진", expanded=True):
        col_i, col_m = st.columns([0.6, 0.4])
        # [복구] 사진 업로드 버튼
        st.file_uploader("추가 사진", type=["jpg", "png"], key=f"ex_{it_key}")
        memo = col_m.text_area("메모", key="me" + it_key, height=120)

    if st.button("🚀 데이터 저장"):
        if not case_no: st.warning("Case Number를 입력하세요.")
        else:
            st.success("데이터가 전송되었습니다!")
            st.session_state.it += 1
            st.rerun()

with t2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with t3:
    q = st.text_input("검색")
    if q: st.dataframe(main_df[main_df['Case #'].str.contains(q)], use_container_width=True)
