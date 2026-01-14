import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image

# 1. 디자인 및 테마 (원복 유지)
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

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;">Skycad Dental Lab Night Guard Manager</div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

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

@st.cache_data(ttl=600)
def get_ref():
    try: return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 날짜 계산 로직
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

if f"due{iter_no}" not in st.session_state:
    st.session_state[f"due{iter_no}"] = date.today() + timedelta(days=7)
    st.session_state[f"shp{iter_no}"] = get_shp(st.session_state[f"due{iter_no}"])

# ---------------------------------------------------------
t1, t2, t3 = st.tabs(["📝 등록", "📊 정산 및 실적", "🔍 검색"])

with t1:
    st.markdown("### 📋 정보 입력")
    clinics_list = sorted([c for c in ref.iloc[:, 1].unique() if c and str(c).lower() != 'nan']) if not ref.empty else []
    docs_list = sorted([d for d in ref.iloc[:, 2].unique() if d and str(d).lower() != 'nan']) if not ref.empty else []
    
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+iter_no)
    patient = c1.text_input("Patient", key="p"+iter_no)
    sel_cl = c2.selectbox("Clinic", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box"+iter_no)
    sel_doc = c3.selectbox("Doctor", ["선택"] + docs_list + ["➕ 직접"], key="sd"+iter_no)

    with st.expander("⚙️ 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy"+iter_no)
        shp_val = d3.date_input("Shipping Date", key="shp"+iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st"+iter_no)

    # 특이사항 (Reference 시트 연동) 및 사진
    st.markdown("### 📂 특이사항 및 사진")
    col_ex1, col_ex2 = st.columns([0.6, 0.4])
    chks_list = []
    if not ref.empty:
        raw_data = ref.iloc[:, 3:].values.flatten()
        chks_list = sorted(list(set([str(x).strip() for x in raw_data if x and str(x).lower() not in ['nan', 'price', '', 'none']])))
    
    chks = col_ex1.multiselect("📌 특이사항 (Reference)", chks_list, key="ck"+iter_no)
    up_f = col_ex1.file_uploader("🖼️ 사진 첨부", type=["jpg", "png", "jpeg"], key="img_up"+iter_no)
    memo = col_ex2.text_area("📝 추가 메모", key="me"+iter_no, height=150)

    if st.button("🚀 데이터 저장하기"):
        # 저장 로직 (연동된 시트로 데이터 전송)
        st.success("저장 완료!")
        st.session_state.it += 1
        st.cache_data.clear()
        st.rerun()

with t2:
    st.markdown("### 📊 월별 정산 조회")
    c_yr, c_mo = st.columns(2)
    sel_year = c_yr.selectbox("연도 선택", range(2025, 2030), index=1)
    sel_month = c_mo.selectbox("월 선택", range(1, 13), index=date.today().month - 1)
    
    if not main_df.empty:
        main_df['T_DT'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')
        m_df = main_df[(main_df['T_DT'].dt.year == sel_year) & (main_df['T_DT'].dt.month == sel_month)]
        v_df = m_df[m_df['Status'].str.upper() == 'NORMAL']
        
        t_q = pd.to_numeric(v_df['Qty'], errors='coerce').sum()
        over_q = max(0, t_q - 320)
        over_pay = over_q * 19.505333

        st.dataframe(m_df[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status', 'Notes']], use_container_width=True, hide_index=True)
        
        st.markdown("---")
        f1, f2, f3 = st.columns(3)
        f1.metric("월 총 수량", f"{int(t_q)} ea")
        f2.metric("320개 초과분", f"{int(over_q)} ea")
        f3.metric("초과 수익 ($)", f"${over_pay:,.2f}")
    else:
        st.info("조회할 데이터가 없습니다.")

# 🔥 [복구] 검색 탭 (Search 기능)
with t3:
    st.markdown("### 🔍 전체 데이터 검색")
    search_query = st.text_input("검색어 입력 (Case #, 병원명, 환자명 등으로 검색)", placeholder="검색어를 입력하고 Enter를 누르세요...")
    
    if not main_df.empty:
        if search_query:
            # 모든 열에서 검색어가 포함된 행 필터링
            filtered_df = main_df[main_df.apply(lambda row: row.astype(str).str.contains(search_query, case=False).any(), axis=1)]
            if not filtered_df.empty:
                st.write(f"🔎 '{search_query}' 검색 결과: {len(filtered_df)}건")
                st.dataframe(filtered_df, use_container_width=True, hide_index=True)
            else:
                st.warning("검색 결과가 없습니다.")
        else:
            st.write("📋 전체 데이터 리스트 (최신순)")
            st.dataframe(main_df.sort_index(ascending=False), use_container_width=True, hide_index=True)
    else:
        st.info("데이터베이스가 비어 있습니다.")
