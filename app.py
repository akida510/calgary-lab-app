import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

st.set_page_config(page_title="Skycad Lab", layout="wide")
st.write("### 🦷 Skycad Lab Manager")

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0

def upd_s():
    if 'd_k' in st.session_state:
        d = st.session_state.d_k
        if isinstance(d, str): d = datetime.strptime(d, '%Y-%m-%d').date()
        st.session_state.s_k = d - timedelta(days=2)

if 'd_k' not in st.session_state: st.session_state.d_k = date.today() + timedelta(days=7)
if 's_k' not in st.session_state: st.session_state.s_k = st.session_state.d_k - timedelta(days=2)

@st.cache_data(ttl=5)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df.apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        df = df[(df['Case #']!="") & (df['Case #']!="nan")]
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

with t1:
    i = st.session_state.it
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key=f"c{i}")
    patient = c1.text_input("Patient", key=f"p{i}")
    
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic", ["선택"]+cl_list+["➕ 직접"], key=f"cl{i}")
    f_cl = c2.text_input("클리닉명", key=f"fcl{i}") if sel_cl=="➕ 직접" else sel_cl
    
    doc_opts = ["선택","➕ 직접"]
    if sel_cl not in ["선택","➕ 직접"]:
        docs = ref_df[ref_df.iloc[:,1]==sel_cl].iloc[:,2].unique()
        doc_opts += sorted([d for d in docs if d and str(d)!='nan'])
    sel_doc = c3.selectbox("Doctor", doc_opts, key=f"d{i}")
    f_doc = c3.text_input("의사명", key=f"fd{i}") if sel_doc=="➕ 직접" else sel_doc

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key=f"a{i}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"m{i}")
        qty = d1.number_input("Qty", 1, 10, 1, key=f"q{i}")
        is_33 = d2.checkbox("3D 스캔", True, key=f"3d{i}")
        rd = d2.date_input("접수일", date.today(), key=f"rd{i}", disabled=is_33)
        cp = d2.date_input("완료일", date.today()+timedelta(1), key=f"cd{i}")
        has_d = d3.checkbox("날짜지정", True, key=f"h_d{i}")
        if has_d:
            due = d3.date_input("마감일", key="d_k", on_change=upd_s)
            shp = d3.date_input("출고일", key="s_k")
            s_t = d3.selectbox("⚠️ 시간", ["Noon","EOD","ASAP"], key=f"st{i}") if due==shp else ""
        else: due = shp = s_t = None
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st{i}")

    if st.button("🚀 저장", use_container_width=True):
        if not case_no or f_cl in ["선택",""]: st.error("정보부족")
        else:
            try:
                p_u = 180
                if sel_cl not in ["선택","➕ 직접"]:
                    # 💡 잘림 방지를 위해 한 줄로 처리
                    p_u = int(float(ref_df[ref_df.iloc[:,1]==sel_cl].iloc[0,3]))
            except: p_u = 180
            
            dfmt = '%Y-%m-%d'
            frd = "-" if is_33 else rd.strftime(dfmt)
            fcp = cp.strftime(dfmt)
            fdue = due.strftime(dfmt) if has_d else "-"
            fshp = shp.strftime(dfmt) if has_d else "-"
            if has_d and s_t: fshp = f"{fshp} {s_t}"
            
            row = {"Case #":case_no, "Clinic":f_cl, "Doctor":f_doc, "Patient":patient, "Arch":arch, "Material":mat, "Price":p_u, "Qty":qty, "Total":p_u*qty, "Receipt Date":frd, "Completed Date":fcp, "Shipping Date":fshp, "Due Date":fdue, "Status":stt, "Notes":""}
            
            try:
                new_df = pd.concat([m_df, pd.DataFrame([row])], ignore_index=True)
                conn.update(data=new_df)
                st.success("완료!"); time.sleep(1)
                st.session_state.it += 1; st.cache_data.clear(); st.rerun()
            except Exception as e: st.error(f"Error: {e}")

with t2
