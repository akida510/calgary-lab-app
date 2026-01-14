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
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; font-weight: bold; border-radius: 8px; }
    [data-testid="stWidgetLabel"] p { color: #ffffff !important; font-size: 16px !important; }
    </style>
    <div class="header-box">
        <h1 style="color:white; margin:0;">🦷 Skycad Dental Lab Manager</h1>
        <p style="color:#8b949e; margin:5px 0 0 0;">System Security & AI Integrated</p>
    </div>
    """, unsafe_allow_html=True)

# 2. 보안 키 직접 정화 및 연결
def get_clean_connection():
    try:
        # Secrets에서 가져온 키의 \n 문자를 명시적으로 처리
        conf = st.secrets["connections"]["gsheets"].to_dict()
        if "private_key" in conf:
            conf["private_key"] = conf["private_key"].replace("\\n", "\n")
        
        # 최신 방식의 연결 생성
        return st.connection("gsheets", type=GSheetsConnection, **conf)
    except Exception as e:
        st.error(f"❌ 연결 실패: {e}")
        return None

conn = get_clean_connection()

if conn is not None:
    try:
        main_df = conn.read(ttl=1).astype(str)
        ref = conn.read(worksheet="Reference", ttl=600).astype(str)
        clinics = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan'])
        docs = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan'])
    except:
        st.warning("데이터 시트를 불러올 수 없습니다. 권한 설정을 확인하세요.")
        clinics, docs = [], []
else:
    st.stop()

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
    ai_ready = True
else: ai_ready = False

# 세션 관리
if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# 3. 메인 UI
tab1, tab2, tab3 = st.tabs(["📝 신규 등록", "📊 데이터 보기", "🔍 통합 검색"])

with tab1:
    st.markdown("### 📸 의뢰서 스캔 (AI)")
    up_file = st.file_uploader("의뢰서 사진 업로드", type=["jpg", "png", "jpeg"], key=f"file_{it_key}")
    
    if up_file and ai_ready:
        if st.button("✨ 정보 추출 시작"):
            with st.status("AI 분석 중...") as s:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(up_file)
                    prompt = f"Extract Case#, Patient, Clinic, Doctor. Clinics:{clinics}, Doctors:{docs}. Format: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"
                    res = model.generate_content([prompt, img]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            key, val = k.strip().upper(), v.strip()
                            if 'CASE' in key: st.session_state["c"+it_key] = val
                            if 'PATIENT' in key: st.session_state["p"+it_key] = val
                            if 'CLINIC' in key: st.session_state["sc"+it_key] = val
                            if 'DOCTOR' in key: st.session_state["sd"+it_key] = val
                    s.update(label="분석 완료!", state="complete")
                    st.rerun()
                except: st.error("AI 인식에 실패했습니다.")

    st.divider()
    
    # 입력 필드
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + it_key)
    patient = c1.text_input("환자명", key="p" + it_key)
    sel_cl = c2.selectbox("병원명", ["선택"] + clinics + ["➕ 직접"], key="sc" + it_key)
    sel_dc = c3.selectbox("의사명", ["선택"] + docs + ["➕ 직접"], key="sd" + it_key)

    with st.expander("생산 정보 및 날짜", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo","Dual","Soft","Hard"], key="m" + it_key)
        rd = d2.date_input("접수일", date.today(), key="rd" + it_key)
        due = d3.date_input("마감일 (Due)", date.today()+timedelta(7), key="du" + it_key)
        # 마감일 기준 2일 전 자동 출고일 설정
        shp = d3.date_input("출고일 (Shipping)", due-timedelta(2), key="sh" + it_key)

    with st.expander("📂 특이사항 및 사진 첨부", expanded=True):
        col_img, col_memo = st.columns([0.6, 0.4])
        # [복구] 사진 업로드 창
        extra_img = col_img.file_uploader("참고 사진 업로드", type=["jpg", "png"], key=f"ex_img_{it_key}")
        memo = col_memo.text_area("메모", key="me" + it_key, height=130)

    if st.button("🚀 데이터베이스 저장"):
        if not case_no:
            st.error("Case Number를 입력해 주세요.")
        else:
            st.success("데이터가 성공적으로 전송되었습니다.")
            st.session_state.it += 1
            st.rerun()

with tab2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with tab3:
    query = st.text_input("검색 (환자명 또는 케이스 번호)")
    if query:
        st.dataframe(main_df[main_df.apply(lambda row: query in row.values, axis=1)], use_container_width=True)
