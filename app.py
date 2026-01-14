import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time
import io

# 1. 페이지 설정 및 다크 네이비 테마 디자인
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1a1c24;
        padding: 20px 30px;
        border-radius: 10px;
        margin-bottom: 25px;
        border: 1px solid #30363d;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, [data-testid="stExpander"] p, .stMetric p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    div[data-testid="stRadio"] label, .stCheckbox label span, button[data-baseweb="tab"] div {
        color: #ffffff !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important;
        color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    .stButton>button {
        width: 100%;
        height: 3.5em;
        background-color: #4c6ef5 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 5px;
        border: none !important;
    }
    [data-testid="stMetricValue"] {
        color: #4c6ef5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 💡 상단 고정 제목
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;">
            Skycad Dental Lab Night Guard Manager
        </div>
        <div style="text-align: right; color: #ffffff;">
            <span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 2. 세션 및 서비스 연결 설정
if "it" not in st.session_state: st.session_state.it = 0
if "last_analyzed" not in st.session_state: st.session_state.last_analyzed = None
iter_no = str(st.session_state.it)

# Gemini AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)

# 3. 데이터 로드 및 캐싱
@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ref():
    try:
        return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 병원/의사 리스트 생성
clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []

# 4. 핵심 분석 함수
def auto_analyze_order(uploaded_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(uploaded_file)
        prompt = "Extract info from this dental order sheet. Response ONLY in this format: CASE:value, PATIENT:value, CLINIC:value, DOCTOR:value"
        response = model.generate_content([prompt, img])
        
        # 텍스트 파싱 로직
        res = {}
        for item in response.text.replace('\n', ',').split(','):
            if ':' in item:
                k, v = item.split(':', 1)
                res[k.strip().upper()] = v.strip()
        return res
    except:
        return None

# 날짜 계산 함수 (영업일 기준 2일 전 출하)
def get_shp_date(due_date):
    target, count = due_date, 0
    while count < 2:
        target -= timedelta(days=1)
        if target.weekday() < 5: # 주말 제외
            count += 1
    return target

# 5. 탭 구성
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 및 정산 (Analytics)", "🔍 검색 (Search)"])

with t1:
    # --- AI 자동 스캔 섹션 ---
    st.markdown("### 📸 의뢰서 자동 스캔")
    ai_file = st.file_uploader("의뢰서 사진을 촬영하거나 업로드하세요", type=["jpg", "jpeg", "png"], key="scanner")

    # [중요] 에러 방지 및 자동 실행 로직
    if ai_file is not None:
        if st.session_state.last_analyzed != ai_file.name:
            with st.spinner("AI가 데이터를 정밀 분석 중입니다..."):
                res = auto_analyze_order(ai_file)
                if res:
                    st.session_state["c" + iter_no] = res.get('CASE', '')
                    st.session_state["p" + iter_no] = res.get('PATIENT', '')
                    
                    c_val = res.get('CLINIC', '')
                    if c_val in clinics_list:
                        st.session_state["sc_box" + iter_no] = c_val
                        # 병원에 맞는 의사 매칭
                        m = ref[ref.iloc[:, 1] == c_val]
                        if not m.empty: st.session_state["sd" + iter_no] = m.iloc[0, 2]
                    
                    st.session_state.last_analyzed = ai_file.name
                    st.success("데이터 추출 완료!")
                    time.sleep(1)
                    st.rerun()

    st.markdown("---")
    st.markdown("### 📋 정보 확인")
    c1, c2, c3 = st.columns(3)
    
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명 (Patient)", key="p" + iter_no)
    
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    
    sel_doc = c3.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no)
    f_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("📅 생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("수량 (Qty)", 1, 10, 1, key="qy" + iter_no)
        
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        # 완료예정일과 출하일 자동 계산 로직
        if "due" + iter_no not in st.session_state:
            st.session_state["due" + iter_no] = date.today() + timedelta(days=7)
        
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no)
        shp_val = d3.date_input("Shipping Date (출고)", get_shp_date(due_val), key="shp" + iter_no)
        stt = d3.selectbox("상태 (Status)", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("📂 특이사항 및 메모", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan' and str(x)!='Price'])))
            chks = col_ex1.multiselect("특이사항 선택", chks_list, key="ck" + iter_no)
        memo = col_ex2.text_area("기타 메모", key="me" + iter_no, height=125)

    if st.button("🚀 데이터베이스 저장하기"):
        if not case_no:
            st.error("Case Number를 입력해주세요.")
        else:
            p_u = 180 # 기본 단가
            if f_cl and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == f_cl]
                if not p_m.empty:
                    try: p_u = int(float(p_m.iloc[0, 3]))
                    except: p_u = 180
            
            new_row = {
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient, 
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'),
                "Shipping Date": shp_val.strftime('%Y-%m-%d'),
                "Due Date": due_val.strftime('%Y-%m-%d'),
                "Status": stt, "Notes": ", ".join(chks) + f" | {memo}"
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("데이터가 성공적으로 저장되었습니다.")
            time.sleep(1)
            # 상태 초기화 후 리런
            st.session_state.it += 1
            st.session_state.last_analyzed = None
            st.cache_data.clear()
            st.rerun()

with t2:
    st.markdown("### 💰 실적 및 부족 수량 확인")
    today = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("연도", range(today.year, today.year - 5, -1))
    s_m = sm.selectbox("월", range(1, 13), index=today.month - 1)
    
    if not main_df.empty:
        pdf = main_df.copy()
        # 숫자 타입 강제 변환 (정산 오류 방지)
        pdf['Qty'] = pd.to_numeric(pdf['Qty'], errors='coerce').fillna(0)
        pdf['Total'] = pd.to_numeric(pdf['Total'], errors='coerce').fillna(0)
        pdf['SD_DT'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        
        m_dt = pdf[(pdf['SD_DT'].dt.year == s_y) & (pdf['SD_DT'].dt.month == s_m)]
        
        if not m_dt.empty:
            st.dataframe(m_dt[['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Total', 'Status']], use_container_width=True, hide_index=True)
            
            # Normal 상태만 집계
            norm_cases = m_dt[m_dt['Status'].str.lower() == 'normal']
            tot_qty = norm_cases['Qty'].sum()
            tot_amt = norm_cases['Total'].sum()
            
            target_qty = 320
            diff_qty = target_qty - tot_qty
            
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("총 생산 수량", f"{int(tot_qty)} ea")
            m2.metric("320개 기준 부족분", f"{int(diff_qty)} ea" if diff_qty > 0 else "목표 달성! ✨")
            m3.metric("총 정산 매출", f"${int(tot_amt):,}")
        else:
            st.info("해당 월의 데이터가 없습니다.")

with t3:
    st.markdown("### 🔍 케이스 검색")
    q_s = st.text_input("검색어 입력 (번호/환자명)", key="search_box")
    if not main_df.empty and q_s:
        f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
        st.dataframe(f_df, use_container_width=True, hide_index=True)
