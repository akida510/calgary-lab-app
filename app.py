import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 디자인 설정 (절대 고정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, .stMetric p { color: #ffffff !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; border: none !important; }
    </style>
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> 🦷 Skycad Lab Manager </div>
        <div style="text-align: right; color: #ffffff; font-weight: 600;">Designed By Heechul Jung</div>
    </div>
    """, unsafe_allow_html=True)

# 2. 데이터 연결 (에러 핸들링 강화)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    main_df = conn.read(ttl=1).astype(str)
    ref = conn.read(worksheet="Reference", ttl=600).astype(str)
except Exception as e:
    st.error(f"⚠️ 연결 오류 발생: {e}")
    st.stop()

# 3. AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    ai_ready = True
else:
    ai_ready = False

# 세션 관리
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 리스트 필터링
clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic']) if not ref.empty else []
docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor']) if not ref.empty else []

# 탭 구성
t1, t2, t3 = st.tabs(["📝 케이스 등록", "📊 실적 확인", "🔍 검색"])

with t1:
    st.subheader("📸 의뢰서 자동 스캔")
    ai_file = st.file_uploader("의뢰서 사진을 업로드하세요", type=["jpg", "png", "jpeg"], key=f"ai_{iter_no}")
    
    if ai_file and ai_ready:
        if st.button("✨ 자동 스캔 실행"):
            with st.status("분석 중...") as status:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(ai_file)
                    img.thumbnail((800, 800))
                    prompt = f"Case#, Patient, Clinic, Doctor 찾기. 목록: {clinics_list}, {docs_list}. 형식: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"
                    res = model.generate_content([prompt, img]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            key, val = k.strip().upper(), v.strip()
                            if 'CASE' in key: st.session_state["c"+iter_no] = val
                            if 'PATIENT' in key: st.session_state["p"+iter_no] = val
                            if 'CLINIC' in key: st.session_state["sc"+iter_no] = val
                            if 'DOCTOR' in key: st.session_state["sd"+iter_no] = val
                    status.update(label="분석 완료!", state="complete")
                    st.rerun()
                except: st.error("AI 분석 중 오류가 발생했습니다.")

    st.markdown("---")
    
    # 입력 폼
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명", key="p" + iter_no)
    sel_cl = c2.selectbox("병원", ["선택"] + clinics_list + ["➕ 직접"], key="sc" + iter_no)
    sel_doc = c3.selectbox("의사", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no)

    with st.expander("생산 상세 정보", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("재질 (Material)", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        due = d3.date_input("마감일 (Due)", date.today()+timedelta(7), key="du" + iter_no)
        # 배송일 자동 설정 (마감 2일 전)
        shp = d3.date_input("출고일 (Shipping)", due-timedelta(2), key="sh" + iter_no)

    with st.expander("📂 추가 메모 및 사진", expanded=True):
        col_img, col_memo = st.columns([0.6, 0.4])
        # [디자인 복구] 하단 참고 사진 업로드
        st.session_state.file_ref = col_img.file_uploader("참고용 사진 첨부", type=["jpg", "png"], key="ref_img")
        memo = col_memo.text_area("메모", key="me" + iter_no, height=120)

    if st.button("🚀 시트에 저장하기"):
        if not case_no: st.error("Case Number를 확인해 주세요.")
        else:
            # 여기에 구글 시트 저장 로직 추가
            st.success(f"Case {case_no} 저장 성공!")
            st.session_state.it += 1
            st.rerun()

with t2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with t3:
    query = st.text_input("검색 (환자명 또는 번호)")
    if query:
        st.dataframe(main_df[main_df['Case #'].str.contains(query) | main_df['Patient'].str.contains(query)], use_container_width=True)
