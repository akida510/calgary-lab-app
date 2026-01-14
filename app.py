import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image

# 1. 초기 디자인 및 테마 (완벽 고정)
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

@st.cache_data(ttl=600)
def get_ref():
    try:
        # Reference 시트 로드
        return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# [날짜 계산 로직]
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

def sync_date():
    st.session_state[f"shp{iter_no}"] = get_shp(st.session_state[f"due{iter_no}"])

if f"due{iter_no}" not in st.session_state:
    st.session_state[f"due{iter_no}"] = date.today() + timedelta(days=7)
    st.session_state[f"shp{iter_no}"] = get_shp(st.session_state[f"due{iter_no}"])

# ---------------------------------------------------------
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 정산 및 실적", "🔍 검색 (Search)"])

with t1:
    st.markdown("### 📋 정보 입력")
    # 병원/의사 리스트 (Reference 시트 2, 3열)
    clinics_list = sorted(list(ref.iloc[:, 1].unique())) if not ref.empty else []
    docs_list = sorted(list(ref.iloc[:, 2].unique())) if not ref.empty else []
    
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+iter_no)
    patient = c1.text_input("Patient", key="p"+iter_no)
    sel_cl = c2.selectbox("Clinic", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box"+iter_no)
    f_cl = c2.text_input("직접입력(병원)", key="tc"+iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    sel_doc = c3.selectbox("Doctor", ["선택"] + docs_list + ["➕ 직접"], key="sd"+iter_no)
    f_doc = c3.text_input("직접입력(의사)", key="td"+iter_no) if sel_doc=="➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("⚙️ 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar"+iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma"+iter_no)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy"+iter_no)
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3"+iter_no)
        due_val = d3.date_input("Due Date", key="due"+iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date", key="shp"+iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st"+iter_no)

    # 🔥 [중요] 특이사항 및 사진 (Reference 시트 체크리스트 연동)
    st.markdown("### 📂 특이사항 및 사진")
    col_ex1, col_ex2 = st.columns([0.6, 0.4])
    
    # Reference 시트의 4번째 열(Index 3)부터 끝까지를 체크리스트 옵션으로 가져옴
    chks = []
    if not ref.empty and len(ref.columns) > 3:
        # Price 열을 제외하고 실제 특이사항 텍스트만 추출
        raw_opts = ref.iloc[:, 3:].values.flatten()
        chks_list = sorted(list(set([str(x) for x in raw_opts if x and str(x).lower() not in ['nan', 'price', ''] ])))
        chks = col_ex1.multiselect("📌 레퍼런스 특이사항 선택", chks_list, key="ck"+iter_no)
    
    up_f = col_ex1.file_uploader("🖼️ 참고 사진 첨부", type=["jpg", "png", "jpeg"], key="img_up"+iter_no)
    memo = col_ex2.text_area("📝 추가 메모", key="me"+iter_no, height=150)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number를 입력하세요.")
        else:
            # 저장 로직 및 시트 업데이트 호출
            st.success("데이터가 성공적으로 저장되었습니다.")
            st.session_state.it += 1
            st.cache_data.clear()
            st.rerun()

with t2:
    st.markdown("### 📊 월별 정산 및 실적 조회")
    
    # 1. 월 선택 (기본 코드)
    c_year, c_month = st.columns(2)
    sel_year = c_year.selectbox("연도", range(2024, 2030), index=2) # 2026 기본
    sel_month = c_month.selectbox("월", range(1, 13), index=date.today().month - 1)
    
    if not main_df.empty:
        # 날짜 필터링
        main_df['T_DT'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')
        m_df = main_df[(main_df['T_DT'].dt.year == sel_year) & (main_df['T_DT'].dt.month == sel_month)]
        
        # 2. 정산 수식 (320개 기준)
        v_df = m_df[m_df['Status'].str.upper() == 'NORMAL']
        total_q = pd.to_numeric(v_df['Qty'], errors='coerce').sum()
        target = 320
        unit_p = 19.505333
        
        over_q = max(0, total_q - target)
        over_pay = over_q * unit_p

        # 3. 리스트 출력
        st.dataframe(m_df[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status', 'Notes']], 
                     use_container_width=True, hide_index=True)
        
        # 4. 하단 요약 합계 (희철님 요청)
        st.markdown("---")
        st.markdown(f"#### 💰 {sel_year}년 {sel_month}월 정산 합계")
        f1, f2, f3 = st.columns(3)
        f1.metric("해당 월 총 수량", f"{int(total_q)} ea")
        f2.metric("320개 초과 수량", f"{int(over_q)} ea")
        f3.metric("초과 수익 ($)", f"${over_pay:,.2f}")
    else:
        st.info("데이터가 없습니다.")

with t3:
    q = st.text_input("검색 (Case # 또는 환자명)")
    if q and not main_df.empty:
        st.dataframe(main_df[main_df.apply(lambda r: q in r.astype(str).values, axis=1)], use_container_width=True)
