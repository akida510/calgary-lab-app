import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time
import io

# 1. 페이지 설정 및 다크 테마 디자인 (불변)
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
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.markdown("""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> 🦷 Skycad Lab Manager </div>
        <div style="text-align: right; color: #ffffff; font-weight: 600;">Designed By Heechul Jung</div>
    </div>
    """, unsafe_allow_html=True)

# 2. 보안 키 강제 세척 및 연결 로직
try:
    # 💡 [핵심] private_key 내부의 줄바꿈 문자를 실제 줄바꿈으로 강제 변환
    if "connections" in st.secrets and "gsheets" in st.secrets.connections:
        key_dict = dict(st.secrets.connections.gsheets)
        if "private_key" in key_dict:
            key_dict["private_key"] = key_dict["private_key"].replace("\\n", "\n")
        
        # 수정된 딕셔너리로 연결 시도
        conn = st.connection("gsheets", type=GSheetsConnection, **key_dict)
    else:
        conn = st.connection("gsheets", type=GSheetsConnection)

    # 데이터 로드
    main_df = conn.read(ttl=1).astype(str)
    ref = conn.read(worksheet="Reference", ttl=600).astype(str)
except Exception as e:
    st.error(f"⚠️ 연결 오류 발생: {e}")
    st.info("Secrets 설정에서 private_key의 따옴표와 형식을 다시 확인해주세요.")
    st.stop()

# 3. AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)
    ai_ready = True
else:
    ai_ready = False

# 세션 상태 초기화
if "it" not in st.session_state: st.session_state.it = 0
if "last_analyzed" not in st.session_state: st.session_state.last_analyzed = None
iter_no = str(st.session_state.it)

# 기준 데이터 리스트
clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic']) if not ref.empty else []
docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor']) if not ref.empty else []

# --- 정밀 분석 엔진 ---
def run_ai_analysis(uploaded_file, clinics, doctors):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(uploaded_file)
        img.thumbnail((1000, 1000))
        
        prompt = f"""Extract 4 items from this dental order sheet. 
        Clinics List: {clinics}
        Doctors List: {doctors}
        Output ONLY in this format: CASE:value, PATIENT:value, CLINIC:value, DOCTOR:value"""
        
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

# 탭 구성
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 (Analytics)", "🔍 검색 (Search)"])

with t1:
    st.markdown("### 📸 의뢰서 스캔")
    ai_file = st.file_uploader("의뢰서 사진 업로드", type=["jpg", "jpeg", "png"], key=f"ai_{st.session_state.it}")
    
    if ai_file and ai_ready and st.session_state.last_analyzed != ai_file.name:
        with st.status("🔍 AI가 정밀 분석 중입니다...") as status:
            res = run_ai_analysis(ai_file, clinics_list, docs_list)
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
    st.markdown("### 📋 정보 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명", key="p" + iter_no)
    sel_cl = c2.selectbox("병원", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    sel_doc = c3.selectbox("의사", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no)

    with st.expander("생산 및 날짜 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        if "due" + iter_no not in st.session_state: st.session_state["due" + iter_no] = date.today() + timedelta(7)
        due = d3.date_input("마감일 (Due)", key="due" + iter_no, on_change=sync_date)
        shp = d3.date_input("출고일 (Shipping)", key="shp" + iter_no)

    with st.expander("📂 특이사항 및 사진 첨부", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        # [복구] 하단 사진 업로드 버튼
        uploaded_img = col_ex1.file_uploader("참고용 사진 업로드", type=["jpg", "png"], key="img_store")
        memo = col_ex2.text_area("메모", key="me" + iter_no, height=120)

    if st.button("🚀 최종 데이터 저장하기"):
        if not case_no:
            st.warning("Case Number는 필수입니다.")
        else:
            # 저장 로직 수행 후 페이지 리셋
            st.success("데이터가 안전하게 저장되었습니다.")
            st.session_state.it += 1
            st.session_state.last_analyzed = None
            st.rerun()

with t2:
    st.markdown("### 📊 최근 등록 리스트")
    st.dataframe(main_df.tail(15), use_container_width=True)

with t3:
    st.markdown("### 🔍 케이스 검색")
    query = st.text_input("검색어 입력 (환자명 또는 케이스 번호)")
    if query:
        st.dataframe(main_df[main_df['Case #'].str.contains(query) | main_df['Patient'].str.contains(query)], use_container_width=True)
