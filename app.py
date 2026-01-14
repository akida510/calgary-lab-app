import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time
import io

# 1. 페이지 설정 및 다크 네이비 테마
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
    .stButton>button {
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important;
        color: white !important; font-weight: bold !important; border-radius: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> Skycad Dental Lab Night Guard Manager </div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# API 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 데이터 로드
@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

main_df = get_data()
ref = conn.read(worksheet="Reference", ttl=600).astype(str)

# --- [수정] 자동 분석 핵심 로직 ---
def auto_analyze(uploaded_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(uploaded_file)
        # 텍스트 추출 프롬프트 강화
        prompt = "Extract info from this dental order. Output ONLY: CASE:value, PATIENT:value, CLINIC:value, DOCTOR:value"
        response = model.generate_content([prompt, img])
        text = response.text.replace('\n', ',')
        
        parsed = {}
        for item in text.split(','):
            if ':' in item:
                k, v = item.split(':', 1)
                parsed[k.strip().upper()] = v.strip()
        return parsed
    except: return None

# 자동 동기화 함수들
def on_clinic_change():
    sel_cl = st.session_state["sc_box" + iter_no]
    if sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty: st.session_state["sd" + iter_no] = match.iloc[0, 2]

def on_doctor_change():
    sel_doc = st.session_state["sd" + iter_no]
    if sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty: st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

t1, t2, t3 = st.tabs(["📝 등록", "📊 정산", "🔍 검색"])

with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor']) if not ref.empty else []
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic']) if not ref.empty else []

    # 📸 자동 분석 섹션
    st.markdown("### 📸 의뢰서 자동 스캔")
    # 업로드 즉시 실행되도록 함
    ai_file = st.file_uploader("의뢰서 사진 촬영 시 자동으로 입력됩니다", type=["jpg", "jpeg", "png"], key="auto_ai")
    
    if ai_file and "last_analyzed" not in st.session_state or st.session_state.get("last_analyzed") != ai_file.name:
        with st.spinner("AI가 의뢰서를 판독하고 있습니다..."):
            res = auto_analyze(ai_file)
            if res:
                st.session_state["c" + iter_no] = res.get('CASE', '')
                st.session_state["p" + iter_no] = res.get('PATIENT', '')
                # 병원/의사 매칭
                c_val = res.get('CLINIC', '')
                d_val = res.get('DOCTOR', '')
                if c_val in clinics_list: st.session_state["sc_box" + iter_no] = c_val
                if d_val in docs_list: st.session_state["sd" + iter_no] = d_val
                
                st.session_state["last_analyzed"] = ai_file.name
                st.success("분석 완료!")
                time.sleep(0.5)
                st.rerun()

    st.markdown("---")
    st.markdown("### 📋 정보 확인")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명", key="p" + iter_no)
    
    sel_cl = c2.selectbox("병원", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no, on_change=on_clinic_change)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else "")

    sel_doc = c3.selectbox("의사", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=on_doctor_change)
    f_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    # 생산 세부 설정 (날짜 로직 복구)
    with st.expander("📅 생산 날짜 및 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        qty = d1.number_input("수량", 1, 10, 1, key="qy" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        due = d3.date_input("Due Date (마감)", date.today() + timedelta(days=7), key="due" + iter_no)
        shp = d3.date_input("Shipping Date (출고)", due - timedelta(days=2), key="shp" + iter_no)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number를 입력해주세요.")
        else:
            p_u = 180
            if f_cl and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == f_cl]
                if not p_m.empty: p_u = int(float(p_m.iloc[0, 3]))
            
            new_row = {
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient, 
                "Qty": qty, "Price": p_u, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'),
                "Shipping Date": shp.strftime('%Y-%m-%d'),
                "Due Date": due.strftime('%Y-%m-%d'),
                "Status": "Normal", "Notes": ""
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장되었습니다!")
            st.session_state.it += 1
            st.cache_data.clear()
            st.rerun()

# 정산 및 검색은 기존 코드 유지 (생략)
