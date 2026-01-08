import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 디자인 (기존 디자인 유지)
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">🦷 Skycad Lab Night Guard Manager</h1>
        <span style="font-size: 12px; font-weight: bold; color: #555;">Designed By Heechul Jung</span>
    </div>
    """,
    unsafe_allow_html=True
)

conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 세션 상태 관리 (입력 튕김 방지)
if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0

# 3. 데이터 로딩 (에러 방지용 10초 캐시)
@st.cache_data(ttl=10)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""]
        df = df.apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력")
    # reset_key를 통해 저장 후에만 입력창 초기화
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key=f"case_{st.session_state.reset_key}")
    patient = c1.text_input("Patient", key=f"pat_{st.session_state.reset_key}")
    
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic", ["선택"]+cl_list+["➕ 직접"], key=f"cl_{st.session_state.reset_key}")
    f_cl = c2.text_input("클리닉명 (직접입력 시)", key=f"fcl_{st.session_state.reset_key}") if sel_cl=="➕ 직접" else sel_cl
    
    doc_opts = ["선택","➕ 직접"]
    if sel_cl not in ["선택","➕ 직접"]:
        docs = ref_df[ref_df.iloc[:,1]==sel_cl].iloc[:,2].unique()
        doc_opts += sorted([d for d in docs if d and str(d)!='nan'])
    sel_doc = c3.selectbox("Doctor", doc_opts, key=f"doc_{st.session_state.reset_key}")
    f_doc = c3.text_input("의사명 (직접입력 시)", key=f"fdoc_{st.session_state.reset_key}") if sel_doc=="➕ 직접" else sel_doc

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key=f"arch_{st.session_state.reset_key}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"mat_{st.session_state.reset_key}")
        qty = d1.number_input("Qty", 1, 10, 1, key=f"qty_{st.session_state.reset_key}")
        is_33 = d2.checkbox("3D 스캔", True, key=f"scan_{st.session_state.reset_key}")
        rd = d2.date_input("접수일", date.today(), disabled=is_33, key=f"rd_{st.session_state.reset_key}")
        cp = d2.date_input("완료일", date.today()+timedelta(1), key=f"cp_{st.session_state.reset_key}")
        
        if d2.checkbox("마감일/출고일 지정", True, key=f"h_d_{st.session_state.reset_key}"):
            default_due = date.today() + timedelta(days=7)
            due = d3.date_input("마감일", default_due, key=f"due_{st.session_state.reset_key}")
            shp = d3.date_input("출고일", due - timedelta(days=2), key=f"shp_{st.session_state.reset_key}")
            s_t = d3.selectbox("⚠️ 시간", ["Noon","EOD","ASAP"], key=f"st_{st.session_state.reset_key}") if due==shp else ""
        else: due = shp = s_t = None
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"stat_{st.session_state.reset_key}")

    with st.expander("✅ 기타 (체크리스트 & 사진)", expanded=True):
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))), key=f"chk_{st.session_state.reset_key}")
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'], key=f"img_{st.session_state.reset_key}")
        memo = st.text_input("메모", key=f"memo_{st.session_state.reset_key}")

    if st.button("🚀 데이터 저장", use_container_width
