import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">🦷 Skycad Lab Night Guard Manager</h1>
        <span style="font-size: 13px; font-weight: bold; color: #333;">Designed By Heechul Jung</span>
    </div>
    """,
    unsafe_allow_html=True
)

conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 세션 상태 관리
if "it" not in st.session_state: 
    st.session_state.it = 0

i = st.session_state.it

# [함수] 주말 제외 영업일 기준 2일 전 계산
def get_working_day_minus_2(due_date):
    target = due_date
    count = 0
    while count < 2:
        target -= timedelta(days=1)
        if target.weekday() < 5: 
            count += 1
    return target

# 날짜 초기값 설정
if f"due{i}" not in st.session_state:
    st.session_state[f"due{i}"] = date.today() + timedelta(days=7)
if f"shp{i}" not in st.session_state:
    st.session_state[f"shp{i}"] = get_working_day_minus_2(st.session_state[f"due{i}"])

# 마감일 변경 시 출고일 자동 갱신
def sync_dates():
    st.session_state[f"shp{i}"] = get_working_day_minus_2(st.session_state[f"due{i}"])

def reset_fields():
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=1)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""]
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    
    case_no = c1.text_input("Case # (필수)", key=f"c{i}")
    patient = c1.text_input("Patient", key=f"p{i}")
    
    # 의사 선택 (모든 의사 리스트)
    all_docs = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    sel_doc = c3.selectbox("Doctor (의사 선택)", ["선택"] + all_docs + ["➕ 직접"], key=f"d{i}")
    f_doc = c3.text_input("직접 입력 (Doctor)", key=f"fd{i}") if sel_doc=="➕ 직접" else sel_doc
    
    # 의사에 따른 병원 자동 매칭
    auto_clinic = ""
    if sel_doc not in ["선택", "➕ 직접"]:
        match = ref_df[ref_df.iloc[:, 2] == sel_doc]
        if not match.empty:
            auto_clinic = match.iloc[0, 1]

    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    default_cl_idx = 0
    if auto_clinic in cl_list:
        default_cl_idx = cl_list.index(auto_clinic) + 1

    sel_cl = c2.selectbox("Clinic (병원명)", ["선택"] + cl_list + ["➕ 직접"], index=default_cl_idx, key=f"cl{i}")
    f_cl = c2.text_input("직접 입력 (Clinic)", key=f"fcl{
