import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time
import io

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
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, [data-testid="stExpander"] p, .stMetric p {
        color: #ffffff !important; font-weight: 600 !important;
    }
    div[data-testid="stRadio"] label, .stCheckbox label span, button[data-baseweb="tab"] div {
        color: #ffffff !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important;
    }
    .stButton>button {
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important;
        color: white !important; font-weight: bold !important; border-radius: 5px; border: none !important;
    }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> Skycad Dental Lab Night Guard Manager </div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. 서비스 연결 및 API 보안 로드
conn = st.connection("gsheets", type=GSheetsConnection)

# API 키를 안전하게 가져오고 설정함
api_key = st.secrets.get("GOOGLE_API_KEY")
ai_enabled = False

if api_key:
    try:
        genai.configure(api_key=api_key)
        ai_enabled = True
    except:
        st.warning("⚠️ API Key 인증에 실패했습니다. 키 값을 다시 확인해주세요.")
else:
    st.info("💡 현재 수동 입력 모드입니다. 자동 스캔을 원하시면 Secrets에 GOOGLE_API_KEY를 등록하세요.")

# 세션 관리
if "it" not in st.session_state: st.session_state.it = 0
if "last_analyzed" not in st.session_state: st.session_state.last_analyzed = None
iter_no = str(st.session_state.it)

# 데이터 로드
@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ref():
    try: return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()
clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic']) if not ref.empty else []
docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor']) if not ref.empty else []

# --- 분석 함수 (멈춤 방지) ---
def fast_scan(file, clinics, docs):
    if not ai_enabled: return None
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(file)
        # 선명도는 유지하되 용량만 줄임
        img.thumbnail((1200, 1200))
        
        prompt = f"""Extract Case#, Patient, Clinic, Doctor. 
        Match Clinic from: {clinics}
        Match Doctor from: {docs}
        Format ONLY as: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"""
        
        response = model.generate_content([prompt, img], request_options={"timeout": 20})
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

def on_clinic_change():
    sel_cl = st.session_state.get("sc_box" + iter_no)
    if sel_cl and sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty: st.session_state["sd" + iter_no] = match.iloc[0, 2]

# 탭 구성
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 및 정산 (Analytics)", "🔍 검색 (Search)"])

with t1:
    st.markdown("### 📸 의뢰서 자동 스캔")
    ai_file = st.file_uploader("사진을 찍거나 업로드하세요", type=["jpg", "jpeg", "png"], key=f"scan_{st.session_state.it}")
    
    if ai_file and ai_enabled and st.session_state.last_analyzed != ai_file.name:
        with st.status("🔍 분석 중... 잠시만 기다려주세요.") as status:
            res = fast_scan(ai_file, clinics_list, docs_list)
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
                status.update(label="✅ 분석 완료!", state="complete", expanded=False)
                time.sleep(0.5)
                st.rerun()
            else:
                status.update(label="❌ 분석 지연 또는 실패 (수동 입력해 주세요)", state="error", expanded=True)

    st.markdown("---")
    st.markdown("### 📋 정보 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명 (Patient)", key="p" + iter_no)
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no, on_change=on_clinic_change)
    f_cl = c2.text_input("직접", key="tc" + iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    sel_doc = c3.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no)
    f_doc = c3.text_input("직접", key="td" + iter_no) if sel_doc=="➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("생산 세부 설정 (Production Details)", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("수량", 1, 10, 1, key="qy" + iter_no)
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no, disabled=is_33)
        cp = d2.date_input("완료예정일", date.today()+timedelta(1), key="cp" + iter_no)
        if "due" + iter_no not in st.session_state: st.session_state["due" + iter_no] = date.today() + timedelta(days=7)
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date (출고)", key="shp" + iter_no)
        stt = d3.selectbox("상태", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("📂 특이사항 및 사진 (Notes & Photos)", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan' and str(x)!='Price'])))
            chks = col_ex1.multiselect("특이사항", chks_list, key="ck" + iter_no)
        uploaded_file = col_ex1.file_uploader("참고 사진 첨부", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = col_ex2.text_area("메모", key="me" + iter_no, height=125)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number를 입력해주세요.")
        else:
            p_u = 180
            if f_cl and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == f_cl]
                if not p_m.empty:
                    try: p_u = int(float(p_m.iloc[0, 3]))
                    except: p_u = 180
            
            new_row = {
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient, 
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": "-" if is_33 else rd.strftime('%Y-%m-%d'),
                "Completed Date": cp.strftime('%Y-%m-%d'),
                "Shipping Date": shp_val.strftime('%Y-%m-%d'),
                "Due Date": due_val.strftime('%Y-%m-%d'),
                "Status": stt, "Notes": f"{', '.join(chks)} | {memo}"
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장 완료!")
            st.session_state.it += 1
            st.session_state.last_analyzed = None
            st.rerun()

# t2, t3 디자인 그대로 유지
with t2:
    st.markdown("### 📊 실적 확인")
    if not main_df.empty:
        st.dataframe(main_df.tail(10), use_container_width=True)

with t3:
    st.markdown("### 🔍 검색")
    q = st.text_input("검색어")
    if q:
        st.dataframe(main_df[main_df['Case #'].str.contains(q) | main_df['Patient'].str.contains(q)], use_container_width=True)
