import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date

# 1. 초기 디자인 고정
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

# [데이터 로드]
@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=1) # Reference 시트도 즉시 반영되게 변경
def get_ref():
    try:
        # worksheet="Reference" 시트의 모든 내용을 읽어옴
        df_ref = conn.read(worksheet="Reference", ttl=0)
        return df_ref
    except: return pd.DataFrame()

main_df = get_data()
ref_df = get_ref()

# ---------------------------------------------------------
t1, t2, t3 = st.tabs(["📝 등록", "📊 정산 및 실적", "🔍 검색"])

with t1:
    st.markdown("### 📋 정보 입력")
    # 병원/의사 리스트 (A, B, C열 기준)
    clinics = sorted([str(c) for c in ref_df.iloc[:, 1].unique() if pd.notna(c) and str(c) != 'Clinic']) if not ref_df.empty else []
    docs = sorted([str(d) for d in ref_df.iloc[:, 2].unique() if pd.notna(d) and str(d) != 'Doctor']) if not ref_df.empty else []
    
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+iter_no)
    patient = c1.text_input("Patient", key="p"+iter_no)
    sel_cl = c2.selectbox("Clinic", ["선택"] + clinics + ["➕ 직접"], key="sc_box"+iter_no)
    sel_doc = c3.selectbox("Doctor", ["선택"] + docs + ["➕ 직접"], key="sd"+iter_no)

    with st.expander("⚙️ 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy"+iter_no)
        shp_val = d3.date_input("Shipping Date", key="shp"+iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st"+iter_no)

    # 🔥 [핵심 수정] 체크리스트(특이사항) 로직 전면 개편
    st.markdown("### 📂 특이사항 및 사진")
    col_ex1, col_ex2 = st.columns([0.6, 0.4])
    
    chks_options = []
    if not ref_df.empty:
        # 시트의 4번째 열(D열)부터 마지막 열까지 데이터만 추출
        # iloc[row_start:, col_start:] 구조
        subset = ref_df.iloc[:, 3:] 
        # 모든 값을 리스트로 만들고 중복/결측치 제거
        flat_list = subset.values.flatten()
        chks_options = sorted(list(set([str(x).strip() for x in flat_list if pd.notna(x) and str(x).strip() != "" and str(x).lower() != 'price'])))
    
    # 만약 시트 로드 실패 시에도 입력은 가능하게 함
    chks = col_ex1.multiselect("📌 특이사항 선택 (D열 이후 데이터)", chks_options, key="ck"+iter_no)
    up_f = col_ex1.file_uploader("🖼️ 사진 첨부", type=["jpg", "png", "jpeg"], key="img_up"+iter_no)
    memo = col_ex2.text_area("📝 추가 메모", key="me"+iter_no, height=150)

    if st.button("🚀 데이터 저장하기"):
        st.success("저장 완료!")
        st.session_state.it += 1
        st.cache_data.clear()
        st.rerun()

with t2:
    st.markdown("### 📊 월별 정산 조회")
    c_yr, c_mo = st.columns(2)
    sel_year = c_yr.selectbox("연도", [2025, 2026, 2027], index=1)
    sel_month = c_mo.selectbox("월", range(1, 13), index=date.today().month - 1)
    
    if not main_df.empty:
        # 날짜 필터링 강화: Shipping Date 컬럼을 시계열로 변환
        main_df['Date_Filter'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')
        m_df = main_df[(main_df['Date_Filter'].dt.year == sel_year) & (main_df['Date_Filter'].dt.month == sel_month)]
        
        # 1. 월별 리스트 출력
        if not m_df.empty:
            st.dataframe(m_df[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status', 'Notes']], use_container_width=True, hide_index=True)
            
            # 2. 정산 계산
            v_df = m_df[m_df['Status'].str.upper() == 'NORMAL']
            total_q = pd.to_numeric(v_df['Qty'], errors='coerce').sum()
            over_q = max(0, total_q - 320)
            over_pay = over_q * 19.505333
            
            st.markdown("---")
            f1, f2, f3 = st.columns(3)
            f1.metric("월 총 수량", f"{int(total_q)} ea")
            f2.metric("320개 초과분", f"{int(over_q)} ea")
            f3.metric("초과 수익 ($)", f"${over_pay:,.2f}")
        else:
            st.warning("선택하신 월에 해당하는 데이터가 없습니다.")

with t3:
    st.markdown("### 🔍 검색")
    sq = st.text_input("검색어 입력")
    if sq and not main_df.empty:
        res = main_df[main_df.apply(lambda r: sq.lower() in r.astype(str).str.lower().values, axis=1)]
        st.dataframe(res, use_container_width=True, hide_index=True)
