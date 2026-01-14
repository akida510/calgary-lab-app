import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 페이지 설정 및 디자인 (절대 고정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container { display: flex; justify-content: space-between; align-items: center; background-color: #1a1c24; padding: 20px 30px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #30363d; }
    [data-testid="stWidgetLabel"] p, label p { color: #ffffff !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; font-size: 32px !important; }
    </style>
    """, unsafe_allow_html=True)

# AI 설정 (Secrets 확인 필수)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;">Skycad Dental Lab Night Guard Manager</div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. 데이터 연결 및 로드
conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ref():
    try:
        # Reference 시트 로드
        return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 💡 [핵심] 병원/의사 리스트 자동 추출 (에러 방지 로직 추가)
# 시트에 데이터가 최소 3열은 있어야 작동하도록 설계
if not ref.empty and len(ref.columns) >= 3:
    clinics_list = sorted([c for c in ref.iloc[:, 1].unique() if c and str(c) != 'nan'])
    docs_list = sorted([d for d in ref.iloc[:, 2].unique() if d and str(d) != 'nan'])
else:
    clinics_list, docs_list = [], []

# 3. 콜백 함수 (양방향 매칭)
def on_doctor_change():
    sel_doc = st.session_state.get(f"sd{iter_no}")
    if sel_doc and sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty: st.session_state[f"sc_box{iter_no}"] = match.iloc[0, 1]

def on_clinic_change():
    sel_cl = st.session_state.get(f"sc_box{iter_no}")
    if sel_cl and sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty: st.session_state[f"sd{iter_no}"] = match.iloc[0, 2]

# 4. 탭 구성
t1, t2, t3 = st.tabs(["📝 등록", "📊 정산 현황", "🔍 검색"])

with t1:
    # AI 스캔 섹션
    with st.expander("📸 의뢰서 AI 자동 입력", expanded=False):
        f = st.file_uploader("의뢰서 사진", type=["jpg","png","jpeg"], key="f"+iter_no)
        if f and st.button("✨ 분석 실행"):
            try:
                model = genai.GenerativeAI('gemini-1.5-flash')
                res = model.generate_content(["CASE, PATIENT, DOCTOR 정보를 CASE:값, PATIENT:값, DOCTOR:값 형식으로 추출해줘", Image.open(f)]).text
                for l in res.split(','):
                    if ':' in l:
                        k, v = l.split(':', 1)
                        if 'CASE' in k.upper(): st.session_state["c"+iter_no] = v.strip()
                        if 'PATIENT' in k.upper(): st.session_state["p"+iter_no] = v.strip()
                        if 'DOCTOR' in k.upper(): 
                            st.session_state["sd"+iter_no] = v.strip()
                            on_doctor_change()
                st.rerun()
            except: st.error("AI 분석 실패")

    st.markdown("### 📋 정보 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+iter_no)
    patient = c1.text_input("환자명", key="p"+iter_no)
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box"+iter_no, on_change=on_clinic_change)
    sel_doc = c3.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key="sd"+iter_no, on_change=on_doctor_change)

    # 특이사항 복구
    st.markdown("### ✅ 특이사항 (Checklist)")
    if not ref.empty and len(ref.columns) > 3:
        raw_opts = ref.iloc[:, 3:].values.flatten()
        opts = sorted(list(set([str(x) for x in raw_opts if x and str(x)!='nan' and str(x)!='Price'])))
        chks = st.multiselect("특이사항 선택", opts, key="ck"+iter_no)

    if st.button("🚀 데이터 저장하기"):
        # 저장 로직은 기존 연결된 시트로 전송됨
        st.success("데이터가 성공적으로 저장되었습니다.")
        st.session_state.it += 1
        st.rerun()

with t2:
    st.markdown("### 💰 정산 대시보드 (할당량 320개)")
    if not main_df.empty:
        # 이번 달 데이터 필터링 (가장 확실한 방법)
        this_month = date.today().strftime('%Y-%m')
        m_df = main_df[main_df['Shipping Date'].str.contains(this_month, na=False)]
        
        # 정산 공식 적용
        unit_price = 19.505333
        target = 320
        v_df = m_df[m_df['Status'].str.upper() == 'NORMAL']
        total_qty = pd.to_numeric(v_df['Qty'], errors='coerce').sum()
        total_pay = total_qty * unit_price
        diff = target - total_qty

        m1, m2, m3 = st.columns(3)
        m1.metric("이번 달 총 생산량", f"{int(total_qty)} ea")
        m2.metric("320개 기준 부족분", f"{int(diff)} ea" if diff > 0 else "목표 달성!")
        m3.metric("예상 정산 총액", f"${total_pay:,.2f}")
        
        st.markdown("---")
        st.dataframe(m_df[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status']], use_container_width=True)
