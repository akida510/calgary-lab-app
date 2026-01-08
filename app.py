import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("### 🦷 Skycad Lab Night Guard Manager")

conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: 
    st.session_state.it = 0
i = st.session_state.it

# [함수] 주말 제외 2일 전 계산
def get_shp_date(due_date):
    target, count = due_date, 0
    while count < 2:
        target -= timedelta(days=1)
        if target.weekday() < 5: count += 1
    return target

# 세션 날짜 초기화
if f"due{i}" not in st.session_state:
    st.session_state[f"due{i}"] = date.today() + timedelta(days=7)
if f"shp{i}" not in st.session_state:
    st.session_state[f"shp{i}"] = get_shp_date(st.session_state[f"due{i}"])

def sync_dates():
    st.session_state[f"shp{i}"] = get_shp_date(st.session_state[f"due{i}"])

def reset_fields():
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=1)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with t1:
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    
    case_no = c1.text_input("Case # (필수)", key=f"c_{i}")
    patient = c1.text_input("Patient", key=f"p_{i}")
    
    # 의사 선택 (가장 중요)
    docs = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    sel_doc = c3.selectbox("Doctor (의사)", ["선택"] + docs + ["➕ 직접"], key=f"d_s_{i}")
    f_doc = c3.text_input("직접 입력(Doc)", key=f"d_t_{i}") if sel_doc=="➕ 직접" else sel_doc
    
    # 병원 자동 매칭
    auto_cl = ""
    if sel_doc not in ["선택", "➕ 직접"]:
        match = ref_df[ref_df.iloc[:, 2] == sel_doc]
        if not match.empty: auto_cl = match.iloc[0, 1]

    clinics = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    idx = clinics.index(auto_cl) + 1 if auto_cl in clinics else 0
    sel_cl = c2.selectbox("Clinic (병원)", ["선택"] + clinics + ["➕ 직접"], index=idx, key=f"cl_s_{i}")
    f_cl = c2.text_input("직접 입력(Cl)", key=f"cl_t_{i}") if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else auto_cl)

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key=f"ar_{i}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"ma_{i}")
        qty = d1.number_input("Qty", 1, 10, 1, key=f"qy_{i}")
        
        is_33 = d2.checkbox("3D 스캔", True, key=f"3d_{i}")
        rd = d2.date_input("접수일", date.today(), key=f"rd_{i}", disabled=is_33)
        # 💡 에러 발생 지점 수정 완료
        cp = d2.date_input("완료일", date.today()+timedelta(1), key
