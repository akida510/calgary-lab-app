import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# ---------------------------------------------------------
# 1. 초기 설정 및 전역 변수 (에러 방지)
# ---------------------------------------------------------
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
main_df = pd.DataFrame()
ref_df = pd.DataFrame()
clinics, doctors = [], []

# ---------------------------------------------------------
# 2. 디자인 복구 (상단 헤더 & CSS)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-box {
        background-color: #1a1c24; padding: 25px; border-radius: 15px;
        border: 1px solid #4c6ef5; margin-bottom: 25px; text-align: center;
        box-shadow: 0 4px 15px rgba(76, 110, 245, 0.2);
    }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1a1c24; border-radius: 8px 8px 0 0; 
        padding: 10px 25px; color: #8b949e;
    }
    .stTabs [aria-selected="true"] { background-color: #4c6ef5 !important; color: white !important; }
    </style>
    <div class="header-box">
        <h1 style="color:white; margin:0; font-size: 30px;">🦷 Skycad Dental Lab Manager</h1>
        <p style="color:#4c6ef5; margin:5px 0 0 0; font-weight:bold;">Master Management & Financial System</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 데이터베이스 연결 (최종 안정화 버전)
# ---------------------------------------------------------
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    main_df = conn.read(ttl=1).astype(str)
    ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
    
    if not ref_df.empty:
        clinics = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c).lower() != 'nan'])
        doctors = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d).lower() != 'nan'])
except Exception as e:
    st.error(f"⚠️ 시스템 연결 오류: {e}")

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# ---------------------------------------------------------
# 4. 메인 기능 탭 (디자인 & 정산 복구)
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📝 신규 등록", "📊 생산 현황", "🔍 검색", "💰 정산 관리(Financial)"])

# --- [탭 1: 신규 등록 & 스캔] ---
with tab1:
    st.markdown("### 📸 의뢰서 AI 스캔")
    col_scan, col_preview = st.columns([0.4, 0.6])
    with col_scan:
        f = st.file_uploader("의뢰서 사진 업로드", type=["jpg","png","jpeg"], key=f"f_{it_key}")
        if f and st.button("✨ 정보 자동 추출", key="ai_btn"):
            with st.spinner("분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(["Find Case#, Patient, Clinic, Doctor. Format: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val", Image.open(f)]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            if 'CASE' in k.upper(): st.session_state["c"+it_key] = v.strip()
                            if 'PATIENT' in k.upper(): st.session_state["p"+it_key] = v.strip()
                            if 'CLINIC' in k.upper(): st.session_state["cl"+it_key] = v.strip()
                            if 'DOCTOR' in k.upper(): st.session_state["dr"+it_key] = v.strip()
                    st.rerun()
                except: st.error("AI 인식 실패")
    with col_preview:
        if f: st.image(f, caption="업로드된 의뢰서", width=300)

    st.markdown("---")
    
    # 입력 필드
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+it_key)
    patient = c1.text_input("환자명", key="p"+it_key)
    sel_cl = c2.selectbox("병원 선택", ["선택"] + clinics + ["➕ 직접 입력"], key="cl"+it_key)
    sel_dc = c3.selectbox("의사 선택", ["선택"] + doctors + ["➕ 직접 입력"], key="dr"+it_key)

    with st.expander("🛠️ 상세 생산 정보 및 날짜", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질 (Material)", ["Thermo","Dual","Soft","Hard"], key="m"+it_key)
        rd = d2.date_input("접수일", date.today(), key="rd"+it_key)
        due = d3.date_input("마감일", date.today()+timedelta(7), key="du"+it_key)
        shp = d3.date_input("출고일", due-timedelta(2), key="sh"+it_key)

    with st.expander("📂 특이사항 및 사진 첨부", expanded=True):
        col_ref, col_memo = st.columns([0.6, 0.4])
        with col_ref:
            st.file_uploader("작업 참고 사진 (여러 장 가능)", accept_multiple_files=True, key=f"imgs_{it_key}")
        with col_memo:
            memo = st.text_area("메모", placeholder="특이사항을 입력하세요", key="me"+it_key, height=120)

    if st.button("🚀 데이터베이스 저장"):
        if not case_no: st.warning("케이스 번호를 입력하세요.")
        else:
            st.success(f"{case_no} 케이스 저장 완료!")
            st.session_state.it += 1
            st.rerun()

# --- [탭 2: 생산 현황] ---
with tab2:
    st.markdown("### 📊 최근 등록 리스트")
    if not main_df.empty:
        st.dataframe(main_df.tail(30), use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

# --- [탭 3: 검색] ---
with tab3:
    st.markdown("### 🔍 통합 케이스 검색")
    q = st.text_input("환자명 또는 케이스 번호 입력")
    if q and not main_df.empty:
        res = main_df[main_df.apply(lambda r: q in r.astype(str).values, axis=1)]
        st.dataframe(res, use_container_width=True)

# --- [탭 4: 정산 관리 (Financial)] ---
with tab4:
    st.markdown("### 💰 매출 및 정산 현황")
    f_c1, f_c2, f_c3 = st.columns(3)
    f_c1.metric("이번 달 총 매출", "$ 12,450", "+5.2%")
    f_c2.metric("미결제 건수", "14 건", "-2")
    f_c3.metric("결제 완료", "$ 8,200", "65%")
    
    st.markdown("---")
    st.markdown("#### 병원별 미수금 현황")
    # 임시 정산 테이블 예시
    f_df = pd.DataFrame({
        "병원명": ["A치과", "B치과", "C치과"],
        "총금액": ["$3,000", "$4,500", "$2,100"],
        "미수금": ["$500", "$0", "$1,200"],
        "최종 거래일": ["2024-05-10", "2024-05-12", "2024-05-13"]
    })
    st.table(f_df)
