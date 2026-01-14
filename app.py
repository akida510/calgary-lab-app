import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time
import io

# 1. 디자인 (희철님 고정 스타일)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p { color: #ffffff !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: #1a1c24 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> Skycad Dental Lab Night Guard Manager </div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. 초기 세션 설정
if "it" not in st.session_state: st.session_state.it = 0
if "last_analyzed" not in st.session_state: st.session_state.last_analyzed = None
iter_no = str(st.session_state.it)

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 데이터 로드 (캐시 1초)
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
clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []

# 4. 고속 AI 분석 함수 (이미지 압축 추가)
def fast_ai_analyze(uploaded_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 이미지 최적화 (속도 향상의 핵심)
        img = Image.open(uploaded_file)
        if img.mode != 'RGB': img = img.convert('RGB')
        img.thumbnail((800, 800)) # 분석 가능한 최소 크기로 압축
        
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=70)
        optimized_img = Image.open(buf)

        prompt = """
        Extract only these 4 items from the dental order. 
        Format: CASE:value | PATIENT:value | CLINIC:value | DOCTOR:value
        If not found, leave value empty.
        """
        
        response = model.generate_content([prompt, optimized_img])
        raw_text = response.text.upper()
        
        # 파싱 강화
        res = {}
        parts = raw_text.replace('\n', '|').split('|')
        for p in parts:
            if ':' in p:
                k, v = p.split(':', 1)
                res[k.strip()] = v.strip()
        return res
    except Exception as e:
        st.error(f"AI 분석 중 오류 발생: {e}")
        return None

# 5. 메인 앱 로직
t1, t2, t3 = st.tabs(["📝 등록", "📊 정산", "🔍 검색"])

with t1:
    st.markdown("### 📸 의뢰서 즉시 스캔")
    ai_file = st.file_uploader("사진을 촬영하면 즉시 입력창이 채워집니다", type=["jpg", "jpeg", "png"], key="scanner")

    # 자동 분석 실행
    if ai_file is not None and st.session_state.last_analyzed != ai_file.name:
        with st.spinner("🚀 고속 엔진으로 의뢰서를 분석 중입니다..."):
            res = fast_ai_analyze(ai_file)
            if res:
                st.session_state["c" + iter_no] = res.get('CASE', '')
                st.session_state["p" + iter_no] = res.get('PATIENT', '')
                
                # 병원/의사 자동 매칭
                c_val = res.get('CLINIC', '')
                if c_val in clinics_list:
                    st.session_state["sc_box" + iter_no] = c_val
                    m = ref[ref.iloc[:, 1] == c_val]
                    if not m.empty: st.session_state["sd" + iter_no] = m.iloc[0, 2]
                
                st.session_state.last_analyzed = ai_file.name
                st.success("✅ 분석 성공!")
                time.sleep(0.5)
                st.rerun()

    st.markdown("---")
    st.markdown("### 📋 정보 확인")
    col1, col2, col3 = st.columns(3)
    
    case_no = col1.text_input("Case Number", key="c" + iter_no)
    patient = col1.text_input("환자명", key="p" + iter_no)
    
    sel_cl = col2.selectbox("병원", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    f_cl = col2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    
    sel_doc = col3.selectbox("의사", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no)
    f_doc = col3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("📅 생산 및 출하 날짜 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        qty = d1.number_input("수량", 1, 10, 1, key="qy" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        due = d3.date_input("Due Date (마감)", date.today() + timedelta(days=7), key="due" + iter_no)
        # 영업일 기준 2일 전 자동 계산
        shp = due - timedelta(days=2) 
        st.info(f"🚚 예상 출하일: {shp.strftime('%Y-%m-%d')}")

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number를 입력하세요.")
        else:
            p_u = 180
            if f_cl:
                p_m = ref[ref.iloc[:, 1] == f_cl]
                if not p_match.empty: p_u = int(float(p_match.iloc[0, 3]))
            
            new_row = {
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient,
                "Qty": qty, "Price": p_u, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'),
                "Shipping Date": shp.strftime('%Y-%m-%d'),
                "Due Date": due.strftime('%Y-%m-%d'),
                "Status": "Normal", "Notes": ""
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장 완료!")
            st.session_state.it += 1
            st.session_state.last_analyzed = None
            st.cache_data.clear()
            st.rerun()

# 📊 정산 탭 (누락 방지 로직)
with t2:
    st.markdown("### 📊 실적 확인")
    t_year = date.today().year
    t_month = date.today().month
    
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['Qty'] = pd.to_numeric(pdf['Qty'], errors='coerce').fillna(0)
        pdf['Total'] = pd.to_numeric(pdf['Total'], errors='coerce').fillna(0)
        pdf['SD_DT'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        m_dt = pdf[(pdf['SD_DT'].dt.year == t_year) & (pdf['SD_DT'].dt.month == t_month)]
        
        c1, c2, c3 = st.columns(3)
        q_sum = m_dt[m_dt['Status'] == 'Normal']['Qty'].sum()
        a_sum = m_dt[m_dt['Status'] == 'Normal']['Total'].sum()
        
        c1.metric("이번 달 생산 수량", f"{int(q_sum)} ea")
        c2.metric("320개까지 부족", f"{max(0, 320-int(q_sum))} ea")
        c3.metric("이번 달 매출액", f"${int(a_sum):,}")
        
        st.dataframe(m_dt, use_container_width=True, hide_index=True)

with t3:
    st.markdown("### 🔍 케이스 검색")
    query = st.text_input("Case# 또는 환자명")
    if query and not main_df.empty:
        st.dataframe(main_df[main_df['Case #'].str.contains(query, case=False) | main_df['Patient'].str.contains(query, case=False)])
