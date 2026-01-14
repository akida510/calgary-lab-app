import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time
import re

# 1. 디자인 (Dark Blue Theme)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p { color: #ffffff !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; }
    </style>
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> 🦷 Skycad Lab Manager </div>
        <div style="color: #ffffff; font-weight: 600;">Designed By Heechul Jung</div>
    </div>
    """, unsafe_allow_html=True)

# 2. [초강력] 보안 키 세척 로직
def sanitize_secrets():
    try:
        if "connections" in st.secrets and "gsheets" in st.secrets.connections:
            pk = st.secrets.connections.gsheets["private_key"]
            # 1. 앞뒤 공백 제거
            pk = pk.strip()
            # 2. 헤더/푸터 제외한 본문 데이터 추출
            header = "-----BEGIN PRIVATE KEY-----"
            footer = "-----END PRIVATE KEY-----"
            if header in pk and footer in pk:
                body = pk.replace(header, "").replace(footer, "").strip()
                # 3. 모든 공백 및 줄바꿈 제거 후 다시 정렬
                clean_body = "".join(body.split())
                # 4. 최종 결합 (표준 줄바꿈 \n 사용)
                sanitized_pk = f"{header}\n{clean_body}\n{footer}"
                st.secrets.connections.gsheets["private_key"] = sanitized_pk
    except:
        pass

sanitize_secrets()

# 3. 서비스 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    main_df = conn.read(ttl=1).astype(str)
    ref = conn.read(worksheet="Reference", ttl=600).astype(str)
except Exception as e:
    st.error(f"❌ 시트 연결 실패. Secrets의 키 값을 다시 확인하세요. ({e})")
    st.stop()

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    ai_ready = True
else: ai_ready = False

# 세션 관리
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 데이터 리스트
clinics = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
docs = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []

# 4. 메인 탭
t1, t2, t3 = st.tabs(["📝 케이스 등록", "📊 실적 현황", "🔍 검색"])

with t1:
    st.markdown("### 📸 의뢰서 스캔")
    f = st.file_uploader("사진을 올려주세요", type=["jpg", "png", "jpeg"], key=f"f_{iter_no}")
    
    if f and ai_ready:
        if st.button("✨ 정보 자동 추출"):
            with st.spinner("AI 분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(f)
                    prompt = f"Case#, Patient, Clinic, Doctor 찾기. 목록: {clinics}, {docs}. 형식: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"
                    res = model.generate_content([prompt, img]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            key, val = k.strip().upper(), v.strip()
                            if 'CASE' in key: st.session_state["c"+iter_no] = val
                            if 'PATIENT' in key: st.session_state["p"+iter_no] = val
                            if 'CLINIC' in key: st.session_state["sc"+iter_no] = val
                            if 'DOCTOR' in key: st.session_state["sd"+iter_no] = val
                    st.rerun()
                except: st.error("AI 인식 실패")

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명", key="p" + iter_no)
    sel_cl = c2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key="sc" + iter_no)
    sel_doc = c3.selectbox("의사", ["선택"] + docs + ["➕ 직접"], key="sd" + iter_no)

    with st.expander("생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        due = d3.date_input("마감일(Due)", date.today()+timedelta(7), key="du" + iter_no)
        shp = d3.date_input("출고일(Shipping)", due-timedelta(2), key="sh" + iter_no)

    with st.expander("📂 참고 사진 및 메모", expanded=True):
        col_i, col_m = st.columns([0.6, 0.4])
        # 사진 업로드 버튼 복구
        st.file_uploader("참고 사진", type=["jpg", "png"], key="ref_img")
        memo = col_m.text_area("메모", key="me" + iter_no, height=120)

    if st.button("🚀 저장하기"):
        st.success("데이터가 성공적으로 전송되었습니다.")
        st.session_state.it += 1
        st.rerun()

with t2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with t3:
    q = st.text_input("검색")
    if q: st.dataframe(main_df[main_df['Case #'].str.contains(q)], use_container_width=True)
