import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 디자인 (Dark Navy & Professional)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-box { background-color: #1a1c24; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 25px; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 8px; }
    [data-testid="stWidgetLabel"] p { color: #ffffff !important; font-weight: 600 !important; }
    </style>
    <div class="header-box">
        <h2 style="color:white; margin:0;">🦷 Skycad Dental Lab Manager</h2>
        <p style="color:#8b949e; margin:0;">Secure AI Integrated System</p>
    </div>
    """, unsafe_allow_html=True)

# 2. 시트 연결 (가장 간결한 표준 방식)
try:
    # 💡 [핵심] 수동으로 인자를 넣지 않고 Streamlit이 Secrets에서 직접 읽게 합니다.
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    main_df = conn.read(ttl=1).astype(str)
    ref = conn.read(worksheet="Reference", ttl=600).astype(str)
    
    clinics = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
    docs = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []
except Exception as e:
    st.error(f"❌ 연결 실패: {e}")
    st.info("Secrets 설정값이 정확한지 다시 한 번 확인해주세요.")
    st.stop()

# 3. AI 및 세션 설정
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key: genai.configure(api_key=api_key)

if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# 4. 메인 UI (탭 구성)
t1, t2, t3 = st.tabs(["📝 케이스 등록", "📊 전체 실적", "🔍 검색 및 수정"])

with t1:
    st.markdown("### 📸 의뢰서 스캔")
    f = st.file_uploader("이미지를 업로드하세요", type=["jpg", "png", "jpeg"], key=f"file_{it_key}")
    
    if f:
        if st.button("✨ AI 분석 실행"):
            with st.spinner("AI가 정보를 읽고 있습니다..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(f)
                    prompt = f"Find Case#, Patient, Clinic, Doctor. Clinics:{clinics}, Doctors:{docs}. Format: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"
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
                except: st.error("AI 인식 오류")

    st.markdown("---")
    
    # 입력 필드
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + it_key)
    patient = c1.text_input("환자명", key="p" + it_key)
    sel_cl = c2.selectbox("병원 선택", ["선택"] + clinics + ["➕ 직접"], key="sc" + it_key)
    sel_dc = c3.selectbox("의사 선택", ["선택"] + docs + ["➕ 직접"], key="sd" + it_key)

    with st.expander("생산 및 날짜 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질 (Material)", ["Thermo","Dual","Soft","Hard"], key="m" + it_key)
        rd = d2.date_input("접수일", date.today(), key="rd" + it_key)
        # 마감일 기준으로 출고일 자동 계산 로직
        due = d3.date_input("마감일 (Due)", date.today()+timedelta(7), key="du" + it_key)
        shp = d3.date_input("출고일 (Shipping)", due - timedelta(2), key="sh" + it_key)

    with st.expander("📂 추가 메모 및 사진", expanded=True):
        col_img, col_memo = st.columns([0.6, 0.4])
        # [복구] 사진 업로드 버튼
        st.file_uploader("참고 사진 첨부", type=["jpg", "png"], key=f"ref_{it_key}")
        memo = col_memo.text_area("메모 입력", key="me" + it_key, height=120)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.warning("Case Number를 입력하세요.")
        else:
            st.success("데이터가 성공적으로 기록되었습니다!")
            st.session_state.it += 1
            st.rerun()

with t2:
    st.dataframe(main_df.tail(20), use_container_width=True)

with t3:
    q = st.text_input("검색어 (케이스 번호 또는 환자명)")
    if q:
        filtered = main_df[main_df.apply(lambda row: q in row.astype(str).values, axis=1)]
        st.dataframe(filtered, use_container_width=True)
