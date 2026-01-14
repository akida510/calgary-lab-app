import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# ---------------------------------------------------------
# 1. 전역 변수 초기화 (NameError 방지 핵심!)
# ---------------------------------------------------------
main_df = pd.DataFrame()
clinics = []
doctors = []

# ---------------------------------------------------------
# 2. 페이지 설정 및 디자인
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# 3. 데이터베이스 연결
# ---------------------------------------------------------
try:
    # 라이브러리가 Secrets를 읽도록 표준 방식으로 연결
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # 데이터 로드 시도
    main_df = conn.read(ttl=1).astype(str)
    ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
    
    if not ref_df.empty:
        clinics = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c).lower() != 'nan'])
        doctors = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d).lower() != 'nan'])
except Exception as e:
    st.error(f"⚠️ 연결 중 문제가 발생했습니다: {e}")
    # 연결 실패해도 위에서 선언한 빈 변수들 덕분에 앱은 계속 실행됨

# ---------------------------------------------------------
# 4. AI 및 세션 관리
# ---------------------------------------------------------
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# ---------------------------------------------------------
# 5. UI 메인 탭
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 신규 케이스 등록", "📊 현황 대시보드", "🔍 통합 검색"])

with tab1:
    st.markdown("### 📸 의뢰서 스캔")
    scan_file = st.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"], key=f"scan_{it_key}")
    
    if scan_file:
        if st.button("✨ AI 정보 자동 추출"):
            with st.spinner("의뢰서 분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(scan_file)
                    prompt = f"Case#, Patient 찾기. 형식: CASE:val, PATIENT:val"
                    res = model.generate_content([prompt, img]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            if 'CASE' in k.upper(): st.session_state["c"+it_key] = v.strip()
                            if 'PATIENT' in k.upper(): st.session_state["p"+it_key] = v.strip()
                    st.rerun()
                except: st.error("AI 분석 중 오류가 발생했습니다.")

    st.divider()
    
    # 수동 입력 폼
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + it_key)
    patient = c1.text_input("환자명", key="p" + it_key)
    sel_cl = c2.selectbox("치과 병원", ["선택"] + clinics + ["➕ 직접 입력"], key="cl" + it_key)
    sel_dc = c3.selectbox("담당 의사", ["선택"] + doctors + ["➕ 직접 입력"], key="dr" + it_key)

    with st.expander("생산 상세 및 날짜 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo","Dual","Soft","Hard"], key="m" + it_key)
        rd = d2.date_input("접수일", date.today(), key="rd" + it_key)
        due = d3.date_input("마감일", date.today()+timedelta(7), key="du" + it_key)
        shp = d3.date_input("출고일", due-timedelta(2), key="sh" + it_key)

    with st.expander("📂 특이사항 및 사진 업로드", expanded=True):
        col_i, col_m = st.columns([0.6, 0.4])
        st.file_uploader("참고용 사진 추가", type=["jpg", "png"], key=f"ref_{it_key}")
        memo = col_m.text_area("메모/특이사항", key="me" + it_key, height=120)

    if st.button("🚀 데이터 저장하기"):
        if not case_no:
            st.warning("Case Number를 입력해 주세요.")
        else:
            st.success(f"케이스 {case_no} 정보가 임시 저장되었습니다.")
            st.session_state.it += 1
            st.rerun()

with tab2:
    st.markdown("### 📊 최근 데이터 (20건)")
    if not main_df.empty:
        st.dataframe(main_df.tail(20), use_container_width=True)
    else:
        st.info("데이터베이스에 연결되지 않았거나 표시할 데이터가 없습니다.")

with tab3:
    st.markdown("### 🔍 케이스 검색")
    q = st.text_input("환자 이름 또는 번호 입력")
    if q and not main_df.empty:
        search_res = main_df[main_df.apply(lambda row: q in row.astype(str).values, axis=1)]
        st.dataframe(search_res, use_container_width=True)
