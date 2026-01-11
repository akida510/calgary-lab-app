import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 애플 스타일 프리미엄 CSS
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=SF+Pro+Display:wght@400;500;600;700&display=swap');
    
    /* 전체 배경: 애플 특유의 Off-White */
    .main { background-color: #f5f5f7; font-family: 'SF Pro Display', -apple-system, sans-serif; }
    
    /* 상단 헤더: 애플 스타일 미니멀 바 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: rgba(255, 255, 255, 0.8);
        backdrop-filter: blur(20px);
        padding: 25px 40px;
        border-radius: 20px;
        margin-bottom: 30px;
        border: 1px solid rgba(0,0,0,0.05);
        box-shadow: 0 4px 20px rgba(0,0,0,0.02);
    }
    
    /* 카드 스타일 (Expander) */
    div[data-testid="stExpander"] {
        background-color: white !important;
        border-radius: 18px !important;
        border: 1px solid rgba(0,0,0,0.03) !important;
        box-shadow: 0 8px 30px rgba(0,0,0,0.04) !important;
        margin-bottom: 20px;
    }
    
    /* 레이블 및 텍스트 가독성 (애플 다크 그레이) */
    label p, .stMarkdown p, div[data-testid="stExpander"] p {
        color: #1d1d1f !important;
        font-weight: 500 !important;
        font-size: 15px;
    }

    /* 버튼: 애플 시그니처 블루 */
    .stButton>button {
        width: 100%;
        border-radius: 14px;
        height: 3.8em;
        background-color: #0071e3 !important;
        color: white !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        border: none !important;
        transition: all 0.3s cubic-bezier(0.25, 0.1, 0.25, 1);
        margin-top: 15px;
    }
    .stButton>button:hover {
        background-color: #0077ed !important;
        transform: translateY(-1px);
        box-shadow: 0 8px 20px rgba(0, 113, 227, 0.3);
    }

    /* 탭 메뉴 디자인 */
    .stTabs [data-baseweb="tab-list"] { gap: 40px; }
    .stTabs [data-baseweb="tab"] {
        color: #86868b !important;
        font-weight: 500;
        font-size: 16px;
    }
    .stTabs [aria-selected="true"] {
        color: #1d1d1f !important;
        border-bottom-color: #0071e3 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 💡 수정된 제목과 제작자 정보
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 28px; font-weight: 700; color: #1d1d1f; letter-spacing: -0.8px;">
            Skycad Dental Lab Night Guard Manager
        </div>
        <div style="text-align: right;">
            <div style="font-size: 13px; color: #86868b; font-weight: 400; text-transform: uppercase; letter-spacing: 0.5px;">Director</div>
            <div style="font-size: 18px; color: #1d1d1f; font-weight: 600;">Designed By Heechul Jung</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 및 날짜 로직 (기능 유지)
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
    except: return pd.DataFrame(columns=["Clinic", "Doctor", "Price"])

main_df = get_data()
ref = get_ref()

# 💡 의사-병원 자동 매칭 (핵심 기능 유지)
def update_clinic_from_doctor():
    selected_doctor = st.session_state["sd" + iter_no]
    if selected_doctor not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == selected_doctor]
        if not match.empty:
            st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

t1, t2, t3 = st.tabs(["📝 Case Register", "💰 Monthly Analytics", "🔍 Database Search"])

# --- [TAB 1: 등록] ---
with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    
    st.markdown("<p style='font-size: 20px; font-weight: 600; color: #1d1d1f; margin-bottom: 20px;'>Case Entry</p>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", placeholder="e.g. 2024-001", key="c" + iter_no)
    patient = c1.text_input("Patient Name", placeholder="Enter name", key="p" + iter_no)
    
    sel_doc = c3.selectbox("Doctor", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=update_clinic_from_doctor)
    f_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else sel_doc

    if "sc_box" + iter_no not in st.session_state: st.session_state["sc_box" + iter_no] = "선택"
    sel_cl = c2.selectbox("Clinic", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else sel_cl

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    
    with st.expander("Production Details", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("Quantity", 1, 10, 1, key="qy" + iter_no)
        
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("Receipt Date", date.today(), key="rd" + iter_no, disabled=is_33)
        cp = d2.date_input("Target Date", date.today()+timedelta(1), key="cp" + iter_no)
        
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date (출고)", key="shp" + iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("Media & Notes", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("Checklist Options", chks_list, key="ck" + iter_no)
        
        uploaded_file = col_ex1.file_uploader("Attach Photo", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = col_ex2.text_area("Additional Notes", placeholder="Note any specifics here...", key="me" + iter_no, height=125)

    if st.button("Complete Registration"):
        if not case_no or f_doc in ["선택", ""]:
            st.error("Missing Case Number or Doctor.")
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
            if uploaded_file: final_notes += f" | {uploaded_file.name}"
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
            st.success("Case Successfully Saved.")
            time.sleep(1)
            reset_all()
            st.rerun()

# --- 정산 및 검색 (애플 미니멀 스타일) ---
with t2:
    st.markdown("<p style='font-size: 20px; font-weight: 600; color: #1d1d1f;'>Performance Dashboard</p>", unsafe_allow_html=True)
    today = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("Year", range(today.year, today.year - 5, -1))
    s_m = sm.selectbox("Month", range(1, 13), index=today.month - 1)
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['SD_DT'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD_DT'].dt.year == s_y) & (pdf['SD_DT'].dt.month == s_m)]
        if not m_dt.empty:
            st.dataframe(m_dt[['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']], use_container_width=True, hide_index=True)
            tot_qty = pd.to_numeric(m_dt[m_dt['Status'].str.lower() == 'normal']['Qty'], errors='coerce').sum()
            st.metric("Total Monthly Units", f"{int(tot_qty)} Units")

with t3:
    st.markdown("<p style='font-size: 20px; font-weight: 600; color: #1d1d1f;'>Search Case Records</p>", unsafe_allow_html=True)
    q_s = st.text_input("Quick Search", placeholder="Search Case # or Patient name...")
    if not main_df.empty:
        if q_s:
            f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(main_df.tail(15), use_container_width=True, hide_index=True)
