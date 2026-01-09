import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 프리미엄 디자인 스타일 (CSS 강화)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경색 */
    .main { background-color: #f0f2f6; }
    
    /* 카드 스타일 디자인 */
    div[data-testid="stExpander"] {
        background-color: white;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: none;
        margin-bottom: 1rem;
    }
    
    /* 상단 헤더 및 제작자 정보 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
        padding: 20px 30px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    
    /* 버튼 커스텀 */
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 3em;
        background-color: #3b82f6 !important;
        font-weight: bold;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2563eb !important;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
    }
    
    /* 탭 디자인 */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: transparent !important;
        border: none;
        font-weight: 600;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# 제작자 정보 및 헤더 (디자인 고정)
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; letter-spacing: -0.5px;">🦷 Skycad Night Guard Manager</div>
        <div style="font-size: 14px; opacity: 0.8; font-weight: 500;">Designed By Heechul Jung</div>
    </div>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 및 상태 관리
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

def sync_date():
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

if "due" + iter_no not in st.session_state:
    st.session_state["due" + iter_no] = date.today() + timedelta(days=7)
if "shp" + iter_no not in st.session_state:
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

def reset_all():
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ref():
    try:
        return conn.read(worksheet="Reference", ttl=600).astype(str)
    except Exception:
        return pd.DataFrame(columns=["Clinic", "Doctor", "Price"])

main_df = get_data()
ref = get_ref()

# 의사-병원 매칭 콜백
def update_clinic_from_doctor():
    selected_doctor = st.session_state["sd" + iter_no]
    if selected_doctor not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == selected_doctor]
        if not match.empty:
            st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

t1, t2, t3 = st.tabs(["📝 Case Registration", "💰 Statistics", "🔍 Search Cases"])

# --- [TAB 1: 등록] ---
with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    
    st.markdown("### 📋 Primary Information")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", placeholder="예: 2024-001", key="c" + iter_no)
    patient = c1.text_input("Patient Name", placeholder="환자명", key="p" + iter_no)
    
    # 의사 선택 (콜백 유지)
    sel_doc = c3.selectbox("Select Doctor", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=update_clinic_from_doctor)
    f_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else sel_doc

    if "sc_box" + iter_no not in st.session_state: st.session_state["sc_box" + iter_no] = "선택"
    sel_cl = c2.selectbox("Select Clinic", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else sel_cl

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
    
    with st.expander("⚙️ Production Details", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch Type", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("Quantity", 1, 10, 1, key="qy" + iter_no)
        
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("Receipt Date", date.today(), key="rd" + iter_no, disabled=is_33)
        cp = d2.date_input("Target Completion", date.today()+timedelta(1), key="cp" + iter_no)
        
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date (출고)", key="shp" + iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("🔗 Attachments & Memo", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            ch_r = ref.iloc[:,3:].values.flatten()
            chks_list = sorted(list(set([str(x) for x in ch_r if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("Checklist / Special Info", chks_list, key="ck" + iter_no)
        
        uploaded_file = col_ex1.file_uploader("Upload Image (Case Photo)", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = col_ex2.text_area("Additional Notes", placeholder="특이사항을 입력하세요", key="me" + iter_no, height=125)

    if st.button("🚀 SAVE CASE DATA", use_container_width=True, type="primary"):
        if not case_no or f_doc in ["선택", ""]:
            st.error("❗ Please fill in Case # and Doctor.")
        else:
            p_u = 180
            final_cl = f_cl if f_cl != "선택" else ""
            if final_cl and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == final_cl]
                if not p_m.empty:
                    try: p_u = int(float(p_m.iloc[0, 3]))
                    except: p_u = 180
            
            dt_fmt = '%Y-%m-%d'
            final_notes = ", ".join(chks)
            if uploaded_file: final_notes += f" | Photo: {uploaded_file.name}"
            if memo: final_notes += f" | {memo}"

            new_row = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": f_doc, "Patient": patient, 
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": "-" if is_33 else rd.strftime(dt_fmt),
                "Completed Date": cp.strftime(dt_fmt),
                "Shipping Date": shp_val.strftime(dt_fmt),
                "Due Date": due_val.strftime(dt_fmt),
                "Status": stt, "Notes": final_notes
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("✅ Data successfully saved!")
            time.sleep(1)
            reset_all()
            st.rerun()

# --- 정산 및 검색 (디자인 일관성 유지) ---
with t2:
    st.markdown("### 💰 Monthly Performance")
    sy, sm = st.columns(2)
    s_y = sy.selectbox("Year", range(date.today().year, date.today().year - 5, -1))
    s_m = sm.selectbox("Month", range(1, 13), index=date.today().month - 1)
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['SD'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD'].dt.year == s_y) & (pdf['SD'].dt.month == s_m)]
        if not m_dt.empty:
            st.dataframe(m_dt[['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']], use_container_width=True, hide_index=True)
            tot = pd.to_numeric(m_dt[m_dt['Status'].str.lower() == 'normal']['Qty'], errors='coerce').sum()
            st.metric("Total Output", f"{int(tot)} Units")

with t3:
    st.markdown("### 🔍 Search Database")
    q_s = st.text_input("Enter Case # or Patient Name", key="search_box")
    if not main_df.empty:
        if q_s:
            f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True, hide_index=True)
        else: st.dataframe(main_df.tail(15), use_container_width=True, hide_index=True)
