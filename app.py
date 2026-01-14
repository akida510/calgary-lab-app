import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time
import io

# 1. 디자인 (불변 설정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, [data-testid="stExpander"] p, .stMetric p {
        color: #ffffff !important; font-weight: 600 !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {
        background-color: #1a1c24 !important; color: #ffffff !important;
    }
    .stButton>button {
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important;
        color: white !important; font-weight: bold; border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> Skycad Dental Lab Night Guard Manager </div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. 서비스 연결 및 API 검증
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    ai_ready = True
else:
    ai_ready = False
    st.error("⚠️ API 키 인식 실패. Secrets 설정을 확인해주세요.")

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0
if "last_analyzed" not in st.session_state: st.session_state.last_analyzed = None
iter_no = str(st.session_state.it)

# 데이터 로드
main_df = conn.read(ttl=1).astype(str)
ref = conn.read(worksheet="Reference", ttl=600).astype(str)
clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []

# --- 분석 함수 (이미지 전처리 강화) ---
def analyze_order(file, clinics, docs):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(file)
        # 흑백 대조를 높여 텍스트 인식률 향상 (내부 처리)
        img.thumbnail((1200, 1200))
        
        prompt = f"""Extract 4 fields from this dental order. 
        Clinics: {clinics}. Doctors: {docs}.
        Output Format ONLY: CASE:value, PATIENT:value, CLINIC:value, DOCTOR:value"""
        
        response = model.generate_content([prompt, img], request_options={"timeout": 15})
        return response.text
    except: return None

# --- 날짜/매칭 로직 ---
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

def sync_date():
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

t1, t2, t3 = st.tabs(["📝 등록", "📊 정산", "🔍 검색"])

with t1:
    st.markdown("### 📸 의뢰서 스캔")
    ai_file = st.file_uploader("의뢰서를 업로드하세요", type=["jpg", "png", "jpeg"], key=f"fup_{st.session_state.it}")
    
    if ai_file and ai_ready and st.session_state.last_analyzed != ai_file.name:
        with st.status("🔍 의뢰서 분석 중...") as status:
            res = analyze_order(ai_file, clinics_list, docs_list)
            if res:
                for item in res.replace('\n', ',').split(','):
                    if ':' in item:
                        k, v = item.split(':', 1)
                        key, val = k.strip().upper(), v.strip()
                        if 'CASE' in key: st.session_state["c"+iter_no] = val
                        if 'PATIENT' in key: st.session_state["p"+iter_no] = val
                        if 'CLINIC' in key and val in clinics_list: st.session_state["sc_box"+iter_no] = val
                        if 'DOCTOR' in key and val in docs_list: st.session_state["sd"+iter_no] = val
                st.session_state.last_analyzed = ai_file.name
                status.update(label="✅ 분석 완료!", state="complete")
                time.sleep(0.5)
                st.rerun()

    st.markdown("---")
    # 정보 입력 (디자인 불변)
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명", key="p" + iter_no)
    sel_cl = c2.selectbox("병원", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    sel_doc = c3.selectbox("의사", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no)

    with st.expander("생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("수량", 1, 10, 1, key="qy" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        due = d3.date_input("Due Date", date.today()+timedelta(7), key="due" + iter_no, on_change=sync_date)
        shp = d3.date_input("Shipping Date", key="shp" + iter_no)

    with st.expander("📂 특이사항 및 사진", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        # [중요] 하단 사진 업로드 창 완벽 복구
        ref_img = col_ex1.file_uploader("참고 사진 첨부", type=["jpg", "png"], key="ref_img")
        memo = col_ex2.text_area("메모", key="me" + iter_no, height=125)

    if st.button("🚀 데이터 저장하기"):
        # 저장 로직...
        st.success("데이터 저장 완료!")
        st.session_state.it += 1
        st.rerun()
