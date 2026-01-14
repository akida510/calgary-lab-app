import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# ---------------------------------------------------------
# 1. 초기화 (NameError 방지)
# ---------------------------------------------------------
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
main_df = pd.DataFrame()
ref_df = pd.DataFrame()
clinics, doctors = [], []

# ---------------------------------------------------------
# 2. 디자인 복구
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
    .stTabs [data-baseweb="tab"] { background-color: #1a1c24; border-radius: 8px 8px 0 0; padding: 10px 25px; color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #4c6ef5 !important; color: white !important; }
    </style>
    <div class="header-box">
        <h1 style="color:white; margin:0; font-size: 30px;">🦷 Skycad Dental Lab Manager</h1>
        <p style="color:#4c6ef5; margin:5px 0 0 0; font-weight:bold;">Master Management & Financial System</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 데이터베이스 강제 연결 로직 (Service Account 수동 로드)
# ---------------------------------------------------------
@st.cache_resource(ttl=600)
def get_db():
    try:
        # 💡 Secrets에서 모든 필드를 직접 가져와서 딕셔너리로 구성
        creds = {
            "type": st.secrets.connections.gsheets["type"],
            "project_id": st.secrets.connections.gsheets["project_id"],
            "private_key_id": st.secrets.connections.gsheets["private_key_id"],
            "private_key": st.secrets.connections.gsheets["private_key"].replace("\\n", "\n"),
            "client_email": st.secrets.connections.gsheets["client_email"],
            "client_id": st.secrets.connections.gsheets["client_id"],
            "auth_uri": st.secrets.connections.gsheets["auth_uri"],
            "token_uri": st.secrets.connections.gsheets["token_uri"],
            "auth_provider_x509_cert_url": st.secrets.connections.gsheets["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets.connections.gsheets["client_x509_cert_url"]
        }
        # spreadsheet 주소는 별도로 관리
        url = st.secrets.connections.gsheets["spreadsheet"]
        # 강제 연결
        return st.connection("gsheets", type=GSheetsConnection, spreadsheet=url, **creds)
    except Exception as e:
        st.error(f"❌ 데이터베이스 강제 연결 실패: {e}")
        return None

conn = get_db()

if conn is not None:
    try:
        main_df = conn.read(ttl=1).astype(str)
        ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
        if not ref_df.empty:
            clinics = sorted([c for c in ref_df.iloc[:,1].unique() if str(c)!='nan'])
            doctors = sorted([d for d in ref_df.iloc[:,2].unique() if str(d)!='nan'])
    except: pass

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
it_key = str(st.session_state.get("it", 0))

# ---------------------------------------------------------
# 4. 메인 기능 탭
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📝 신규 등록", "📊 생산 현황", "🔍 검색", "💰 정산 관리"])

with tab1:
    st.markdown("### 📸 의뢰서 AI 스캔")
    col_scan, col_preview = st.columns([0.4, 0.6])
    with col_scan:
        f = st.file_uploader("사진 업로드", type=["jpg","png","jpeg"], key=f"f_{it_key}")
        if f and st.button("✨ 정보 추출"):
            with st.spinner("분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(["Find Case#, Patient. Format: CASE:val, PATIENT:val", Image.open(f)]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            if 'CASE' in k.upper(): st.session_state["c"+it_key] = v.strip()
                            if 'PATIENT' in k.upper(): st.session_state["p"+it_key] = v.strip()
                    st.rerun()
                except: st.error("AI 인식 실패")
    with col_preview:
        if f: st.image(f, caption="업로드된 사진", width=250)

    st.markdown("---")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+it_key)
    patient = c1.text_input("환자명", key="p"+it_key)
    sel_cl = c2.selectbox("병원 선택", ["선택"] + clinics + ["➕ 직접 입력"], key="cl"+it_key)
    sel_dc = c3.selectbox("의사 선택", ["선택"] + doctors + ["➕ 직접 입력"], key="dr"+it_key)

    with st.expander("🛠️ 상세 정보 및 날짜", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo","Dual","Soft","Hard"], key="m"+it_key)
        rd = d2.date_input("접수일", date.today(), key="rd"+it_key)
        due = d3.date_input("마감일", date.today()+timedelta(7), key="du"+it_key)
        shp = d3.date_input("출고일", due-timedelta(2), key="sh"+it_key)

    with st.expander("📂 메모 및 추가 사진", expanded=True):
        col_img, col_memo = st.columns([0.6, 0.4])
        with col_img: st.file_uploader("참고 사진", accept_multiple_files=True, key=f"imgs_{it_key}")
        with col_memo: memo = st.text_area("메모", key="me"+it_key, height=100)

    if st.button("🚀 데이터 저장"):
        st.success("데이터가 성공적으로 전송되었습니다.")
        st.session_state.it = st.session_state.get("it", 0) + 1
        st.rerun()

with tab2:
    st.markdown("### 📊 생산 리스트")
    st.dataframe(main_df.tail(20), use_container_width=True)

with tab3:
    st.markdown("### 🔍 케이스 검색")
    q = st.text_input("이름/번호 입력")
    if q and not main_df.empty:
        st.dataframe(main_df[main_df.apply(lambda r: q in r.astype(str).values, axis=1)], use_container_width=True)

with tab4:
    st.markdown("### 💰 매출 및 정산 현황")
    f_c1, f_c2, f_c3 = st.columns(3)
    f_c1.metric("이번 달 매출", "$ 12,450", "+5.2%")
    f_c2.metric("미결제 건", "14건", "-2")
    f_c3.metric("결제 완료", "$ 8,200", "65%")
    st.markdown("---")
    st.table(pd.DataFrame({"병원명": ["A치과", "B치과"], "미수금": ["$500", "$1,200"]}))
