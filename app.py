import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("### 🦷 Skycad Lab Manager <span style='font-size:0.8rem;color:#888;'>by Heechul Jung</span>", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0

def update_ship(): st.session_state.s_k = st.session_state.d_k - timedelta(days=2)
if 'd_k' not in st.session_state: st.session_state.d_k = datetime.now().date() + timedelta(days=7)
if 's_k' not in st.session_state: st.session_state.s_k = st.session_state.d_k - timedelta(days=2)

def reset():
    st.session_state.it += 1
    st.cache_data.clear()
    st.rerun()

@st.cache_data(ttl=5)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str).apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        df = df[(df['Case #']!="")&(df['Case #']!="nan")&(~df['Case #'].str.contains("Deliver|Remake|작업량|세후|할당량",na=False))]
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_data()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with t1:
    i = st.session_state.it
    st.subheader("📋 케이스 입력")
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no = st.text_input("Case # *", key=f"c{i}")
        patient = st.text_input("Patient *", key=f"p{i}")
    with c2:
        cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c).lower()!='nan' and c!='Clinic'])
        sel_cl = st.selectbox("Clinic *", ["선택"]+cl_list+["➕ 직접"], key=f"cl{i}")
        f_cl = st.text_input("클리닉명", key=f"fcl{i}") if sel_cl=="➕ 직접" else sel_cl
    with c3:
        doc_opts = ["선택","➕ 직접"]
        if sel_cl not in ["선택","➕ 직접"]:
            docs = ref_df[ref_df.iloc[:,1]==sel_cl].iloc[:,2].unique()
            doc_opts += sorted([d for d in docs if d and str(d).lower()!='nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key=f"d{i}")
        f_doc = st.text_input("의사명", key=f"fd{i}") if sel_doc=="➕ 직접" else sel_doc

    with st.expander("⚙️ 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max","Mand"], horizontal=True, key=f"a{i}")
            mat = st.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"m{i}")
            qty = st.number_input("Qty", 1, 10, 1, key=f"q{i}")
        with d2:
            is_3d = st.checkbox("3D 스캔", True, key=f"3d{i}")
            rd = st.date_input("접수일", datetime.now(), key=f"rd{i}", disabled=is_3d)
            comp_d = st.date_input("완료일", datetime.now()+timedelta(1), key=f"cd{i}")
        with d3:
            due_d = st.date_input("마감일", key="d_k", on_change=update_ship)
            ship_d = st.date_input("출고일", key="s_k")
            stat = st.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st{i}")

    with st.expander("✅ 기타", expanded=True):
        chk_opts = sorted(list(set([str(x) for x in ref_df.iloc[:,3:].values.flatten() if x and str(x)!='nan'])))
        chks = st.multiselect("체크리스트", chk_opts, key=f"ck{i}")
        memo = st.text_input("메모", key=f"me{i}")

    if st.
