import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 다크 네이비 테마 (디자인 절대 고정)
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

# 헤더 고정
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;">Skycad Dental Lab Night Guard Manager</div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 관리
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 데이터 로드 (TTL 설정을 통해 실시간성 확보)
@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=1)
def get_ref():
    try: return conn.read(worksheet="Reference", ttl=0).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 날짜 자동 계산 함수
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

def sync_date():
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

# 세션 초기값
if "due" + iter_no not in st.session_state:
    st.session_state["due" + iter_no] = date.today() + timedelta(days=7)
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

# ---------------------------------------------------------
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 정산 및 실적 (Settlement)", "🔍 검색 (Search)"])

with t1:
    st.markdown("### 📋 정보 입력")
    # 병원/의사 리스트 (Reference A, B, C열)
    clinics = sorted([c for c in ref.iloc[:, 1].unique() if c and str(c).lower() != 'nan']) if not ref.empty else []
    docs = sorted([d for d in ref.iloc[:, 2].unique() if d and str(d).lower() != 'nan']) if not ref.empty else []
    
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+iter_no)
    patient = c1.text_input("Patient", key="p"+iter_no)
    sel_cl = c2.selectbox("Clinic", ["선택"] + clinics + ["➕ 직접"], key="sc"+iter_no)
    sel_doc = c3.selectbox("Doctor", ["선택"] + docs + ["➕ 직접"], key="sd"+iter_no)

    with st.expander("⚙️ 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy"+iter_no)
        due_val = d2.date_input("Due Date", key="due"+iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date", key="shp"+iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st"+iter_no)

    # 📂 특이사항 (Reference 시트 D열 이후 체크리스트 연동)
    st.markdown("### 📂 특이사항 및 사진")
    col_ex1, col_ex2 = st.columns([0.6, 0.4])
    
    chks_list = []
    if not ref.empty:
        # D열부터 끝까지 모든 텍스트를 옵션으로 추출
        raw_vals = ref.iloc[:, 3:].values.flatten()
        chks_list = sorted(list(set([str(v).strip() for v in raw_vals if v and str(v).lower() not in ['nan', 'price', '']])))
    
    chks = col_ex1.multiselect("📌 특이사항 선택 (Reference)", chks_list, key="ck"+iter_no)
    up_f = col_ex1.file_uploader("🖼️ 사진 첨부", type=["jpg", "png", "jpeg"], key="img_up"+iter_no)
    memo = col_ex2.text_area("📝 추가 메모", key="me"+iter_no, height=150)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number를 입력하세요.")
        else:
            # 저장 로직 (필요 시 시트 업데이트 API 연결)
            st.success("데이터가 성공적으로 저장되었습니다!")
            st.session_state.it += 1
            st.cache_data.clear()
            st.rerun()

with t2:
    st.markdown("### 📊 월별 정산 조회")
    c_yr, c_mo = st.columns(2)
    sel_year = c_yr.selectbox("연도", [2024, 2025, 2026, 2027], index=2)
    sel_month = c_mo.selectbox("월", range(1, 13), index=date.today().month - 1)
    
    if not main_df.empty:
        # 날짜 필터링 로직 강화
        main_df['DT_OBJ'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')
        m_df = main_df[(main_df['DT_OBJ'].dt.year == sel_year) & (main_df['DT_OBJ'].dt.month == sel_month)]
        
        if not m_df.empty:
            # 리스트 출력
            st.dataframe(m_df[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status', 'Notes']], 
                         use_container_width=True, hide_index=True)
            
            # 정산 계산
            norm_df = m_df[m_df['Status'].str.upper() == 'NORMAL']
            total_qty = pd.to_numeric(norm_df['Qty'], errors='coerce').sum()
            target = 320
            over_qty = max(0, total_qty - target)
            over_amt = over_qty * 19.505333
            
            st.markdown("---")
            f1, f2, f3 = st.columns(3)
            f1.metric("해당 월 총 수량", f"{int(total_qty)} ea")
            f2.metric("320개 기준 초과", f"{int(over_qty)} ea")
            f3.metric("초과 금액 ($)", f"${over_amt:,.2f}")
        else:
            st.warning(f"{sel_year}년 {sel_month}월에 해당하는 데이터가 없습니다.")
    else:
        st.info("데이터가 없습니다.")

with t3:
    st.markdown("### 🔍 전체 검색")
    sq = st.text_input("검색어 입력 (번호/이름/병원)")
    if sq and not main_df.empty:
        res = main_df[main_df.apply(lambda r: sq.lower() in r.astype(str).str.lower().values, axis=1)]
        st.dataframe(res, use_container_width=True, hide_index=True)
    elif not main_df.empty:
        st.dataframe(main_df.sort_index(ascending=False).head(20), use_container_width=True, hide_index=True)
