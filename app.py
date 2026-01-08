import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab", layout="wide")
st.markdown("### 🦷 Skycad Lab Night Guard Manager")

conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: st.session_state.it = 0
i = st.session_state.it

# [함수] 주말 제외 2일 전 계산
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

# 날짜 초기화
if f"due{i}" not in st.session_state:
    st.session_state[f"due{i}"] = date.today() + timedelta(days=7)
if f"shp{i}" not in st.session_state:
    st.session_state[f"shp{i}"] = get_shp(st.session_state[f"due{i}"])

def sync():
    st.session_state[f"shp{i}"] = get_shp(st.session_state[f"due{i}"])

def reset():
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=1)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref = conn.read(worksheet="Reference", ttl=600).astype(str)

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with t1:
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key=f"c_{i}")
    patient = c1.text_input("Patient", key=f"p_{i}")
    
    # 의사 선택 (핵심)
    docs = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    s_doc = c3.selectbox("Doctor", ["선택"] + docs + ["➕ 직접"], key=f"sd_{i}")
    f_doc = c3.text_input("직접 입력(의사)", key=f"td_{i}") if s_doc=="➕ 직접" else s_doc
    
    # 병원 자동 매칭
    a_cl = ""
    if s_doc not in ["선택", "➕ 직접"]:
        match = ref[ref.iloc[:, 2] == s_doc]
        if not match.empty: a_cl = match.iloc[0, 1]

    clinics = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    idx = clinics.index(a_cl) + 1 if a_cl in clinics else 0
    s_cl = c2.selectbox("Clinic", ["선택"] + clinics + ["➕ 직접"], index=idx, key=f"sc_{i}")
    f_cl = c2.text_input("직접 입력(병원)", key=f"tc_{i}") if s_cl=="➕ 직접" else (s_cl if s_cl != "선택" else a_cl)

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key=f"ar_{i}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"ma_{i}")
        qty = d1.number_input("Qty", 1, 10, 1, key=f"qy_{i}")
        is_33 = d2.checkbox("3D Scan", True, key=f"d3_{i}")
        rd = d2.date_input("접수일", date.today(), key=f"rd_{i}", disabled=is_33)
        
        # 💡 SyntaxError 해결: cp 변수 짧게 수정
        cp = d2.date_input("완료일", date.today()+timedelta(1), key=f"cp_{i}")
        
        due = d3.date_input("마감일", key=f"due{i}", on_change=sync)
        shp = d3.date_input("출고일", key=f"shp{i}")
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st_{i}")

    with st.expander("✅ 기타", expanded=True):
        ch_r = ref.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크", sorted(list(set([str(x) for x in ch_r if x and str(x)!='nan']))), key=f"ck_{i}")
        memo = st.text_input("메모", key=f"me_{
