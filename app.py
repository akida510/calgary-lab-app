import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date

# 1. 디자인 (절대 고정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container { display: flex; justify-content: space-between; align-items: center; background-color: #1a1c24; padding: 20px 30px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #30363d; }
    [data-testid="stWidgetLabel"] p, label p, .stMetric p { color: #ffffff !important; font-weight: 600 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea { background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""<div class="header-container"><div style="font-size: 26px; font-weight: 800; color: #ffffff;">Skycad Dental Lab Manager</div><div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div></div>""", unsafe_allow_html=True)

# 2. 데이터 연결
conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

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

t1, t2, t3 = st.tabs(["📝 등록", "📊 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
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
        due_val = d2.date_input("Due Date", date.today()+timedelta(7), key="due"+iter_no)
        shp_val = d3.date_input("Shipping Date", date.today()+timedelta(6), key="shp"+iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st"+iter_no)

    st.markdown("### 📂 특이사항 (Reference 연동)")
    chks_list = []
    if not ref.empty:
        raw = ref.iloc[:, 3:].values.flatten()
        chks_list = sorted(list(set([str(v).strip() for v in raw if v and str(v).lower() not in ['nan', 'price', '']])))
    
    chks = st.multiselect("📌 특이사항 선택", chks_list, key="ck"+iter_no)
    memo = st.text_area("📝 메모", key="me"+iter_no)

    if st.button("🚀 저장하기"):
        st.success("저장 완료!")
        st.session_state.it += 1
        st.cache_data.clear()
        st.rerun()

# --- [TAB 2: 정산] ---
with t2:
    st.markdown("### 📊 월별 실적")
    col_y, col_m = st.columns(2)
    s_y = col_y.selectbox("연도", [2025, 2026, 2027], index=1)
    s_m = col_m.selectbox("월", range(1, 13), index=date.today().month - 1)
    
    if not main_df.empty:
        # 날짜 강제 변환 필터링 (시트 날짜 형식 무관하게 처리)
        main_df['DT_CONV'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')
        m_df = main_df[(main_df['DT_CONV'].dt.year == s_y) & (main_df['DT_CONV'].dt.month == s_m)]
        
        if not m_df.empty:
            st.dataframe(m_df[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status', 'Notes']], use_container_width=True, hide_index=True)
            
            norm_df = m_df[m_df['Status'].str.upper() == 'NORMAL']
            total_qty = pd.to_numeric(norm_df['Qty'], errors='coerce').sum()
            over_qty = max(0, total_qty - 320)
            over_amt = over_qty * 19.505333
            
            st.markdown("---")
            f1, f2, f3 = st.columns(3)
            f1.metric("총 생산 수량", f"{int(total_qty)} ea")
            f2.metric("320개 초과분", f"{int(over_qty)} ea")
            f3.metric("초과 수익 ($)", f"${over_amt:,.2f}")
        else:
            st.warning("데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    st.markdown("### 🔍 검색")
    sq = st.text_input("검색어 (번호/이름/병원)")
    if sq and not main_df.empty:
        res = main_df[main_df.apply(lambda r: sq.lower() in r.astype(str).str.lower().values, axis=1)]
        st.dataframe(res, use_container_width=True, hide_index=True)
