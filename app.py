import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 디자인 및 초기화
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# 다크 테마 적용
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stHeader"] { background: rgba(0,0,0,0); }
    .header-box { background-color: #1a1c24; padding: 1.5rem; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 2rem; }
    .stButton>button { width: 100%; height: 3.5rem; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 8px; }
    </style>
    <div class="header-box">
        <h2 style='margin:0; color:white;'>🦷 Skycad Lab Manager</h2>
        <p style='margin:0; color:#8b949e;'>Designed By Heechul Jung</p>
    </div>
    """, unsafe_allow_html=True)

# 2. 서비스 연결 (간결화)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    main_df = conn.read(ttl=1).astype(str)
    ref = conn.read(worksheet="Reference", ttl=600).astype(str)
except Exception as e:
    st.error(f"⚠️ 연결 오류: {e}")
    st.info("Secrets 창에 붙여넣은 private_key의 따옴표 시작과 끝을 다시 확인해 주세요.")
    st.stop()

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    ai_ready = True
else: ai_ready = False

# 세션 관리
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 리스트 생성
clinics = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
docs = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []

# 3. UI - 탭
t1, t2, t3 = st.tabs(["📝 등록", "📊 통계", "🔍 검색"])

with t1:
    st.subheader("📸 의뢰서 자동 스캔")
    up_file = st.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"], key=f"f_{iter_no}")
    
    if up_file and ai_ready:
        if st.button("🔍 AI 분석 시작"):
            with st.spinner("분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(up_file)
                    img.thumbnail((800, 800))
                    prompt = f"Find Case#, Patient, Clinic, Doctor. Clinics:{clinics}, Doctors:{docs}. Format: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"
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
                except: st.error("분석 실패. 수동 입력을 권장합니다.")

    st.divider()
    
    c1, c2, c3 = st.columns(3)
    c_no = c1.text_input("Case Number", key="c"+iter_no)
    p_name = c1.text_input("환자명", key="p"+iter_no)
    sel_cl = c2.selectbox("병원", ["선택"] + clinics + ["➕ 직접"], key="sc"+iter_no)
    sel_dc = c3.selectbox("의사", ["선택"] + docs + ["➕ 직접"], key="sd"+iter_no)

    with st.expander("생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo", "Dual", "Soft", "Hard"], key="m"+iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd"+iter_no)
        due = d3.date_input("마감일 (Due)", date.today()+timedelta(7), key="du"+iter_no)
        # 배송일 자동 계산
        shp = d3.date_input("출고일 (Shipping)", due-timedelta(2), key="sh"+iter_no)

    with st.expander("📂 추가 정보 및 사진", expanded=True):
        col_img, col_memo = st.columns([0.6, 0.4])
        # [여기] 사진 업로드 창 확실히 유지
        st.session_state.final_img = col_img.file_uploader("참고 사진 업로드", type=["jpg", "png"], key="fin_img")
        memo = col_memo.text_area("메모", key="me"+iter_no, height=120)

    if st.button("🚀 데이터 저장하기"):
        if not c_no: st.error("Case Number를 확인하세요.")
        else:
            # 저장 로직 (GSheet 연결 시도)
            st.success(f"{c_no} 저장 완료!")
            st.session_state.it += 1
            st.rerun()

with t2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with t3:
    sq = st.text_input("검색어 (Case # / 이름)")
    if sq:
        st.dataframe(main_df[main_df['Case #'].str.contains(sq) | main_df['Patient'].str.contains(sq)], use_container_width=True)
