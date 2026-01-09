import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 프리미엄 CSS 디자인
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 배경 및 기본 폰트 */
    .main { background-color: #f8fafc; }
    
    /* 상단 헤더 컨테이너 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        padding: 25px 35px;
        border-radius: 15px;
        color: white;
        margin-bottom: 30px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    /* 다크 섹션 (Production Details & Memo) */
    div[data-testid="stExpander"] {
        background-color: #1e293b !important;
        border-radius: 12px;
        border: 1px solid #334155;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 10px;
    }
    
    /* 섹션 내부 글자색 화이트 강제 적용 */
    div[data-testid="stExpander"] p, 
    div[data-testid="stExpander"] label, 
    div[data-testid="stExpander"] .stMarkdown {
        color: #f8fafc !important;
        font-weight: 500 !important;
    }

    /* 저장 버튼 디자인 */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3.5em;
        background: #3b82f6 !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 16px !important;
        border: none !important;
        transition: all 0.3s ease;
        margin-top: 20px;
    }
    .stButton>button:hover {
        background: #2563eb !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(59, 130, 246, 0.4);
    }

    /* 입력창 레이블 가독성 (메인 영역) */
    label[data-testid="stWidgetLabel"] p {
        font-weight: 600;
        color: #334155;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더 섹션
st.markdown(f"""
    <div class="header-container">
        <div>
            <div style="font-size: 28px; font-weight: 800; letter-spacing: -0.5px;">🦷 Skycad Night Guard</div>
            <div style="font-size: 14px; opacity: 0.7; margin-top: 4px;">Dental Lab Management System v2.0</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 12px; opacity: 0.6; text-transform: uppercase; letter-spacing: 1px;">Project Director</div>
            <div style="font-size: 16px; font-weight: 600; color: #60a5fa;">Heechul Jung</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 관리
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 주말 제외 출고일 계산 함수
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

# 날짜 동기화
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
    except:
        return pd.DataFrame(columns=["Clinic", "Doctor", "Price"])

main_df = get_data()
ref = get_ref()

# 의사-병원 매칭 콜백 (핵심 로직)
def update_clinic_from_doctor():
    selected_doctor = st.session_state["sd" + iter_no]
    if selected_doctor not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == selected_doctor]
        if not match.empty:
            st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

t1, t2, t3 = st.tabs(["📝 Case Registration", "💰 Statistics", "🔍 Search Database"])

# --- [TAB 1: 등록] ---
with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    
    st.markdown("### 📋 Primary Information")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", placeholder="Entry Case Number", key="c" + iter_no)
    patient = c1.text_input("Patient Name", placeholder="Full Name", key="p" + iter_no)
    
    sel_doc = c3.selectbox("Select Doctor", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=update_clinic_from_doctor)
    f_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else sel_doc

    if "sc_box" + iter_no not in st.session_state: st.session_state["sc_box" + iter_no] = "선택"
    sel_cl = c2.selectbox("Select Clinic", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else sel_cl

    st.markdown("<div style='margin:10px;'></div>", unsafe_allow_html=True)
    
    # 세부 설정 섹션 (다크 테마 및 화이트 폰트 적용)
    with st.expander("⚙️ Production Details", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch Type", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material Choice", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("Unit Quantity", 1, 10, 1, key="qy" + iter_no)
        
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("Receipt Date", date.today(), key="rd" + iter_no, disabled=is_33)
        cp = d2.date_input("Target Date", date.today()+timedelta(1), key="cp" + iter_no)
        
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date (출고일)", key="shp" + iter_no)
        stt = d3.selectbox("Current Status", ["Normal","Hold","Canceled"], key="st" + iter_no)

    # 기타 및 메모 섹션
    with st.expander("🔗 Attachments & Notes", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_raw = ref.iloc[:,3:].values.flatten()
            chks_list = sorted(list(set([str(x) for x in chks_raw if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("Checklist Options", chks_list, key="ck" + iter_no)
        
        uploaded_file = col_ex1.file_uploader("Upload Case Photo", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = col_ex2.text_area("Additional Remarks", placeholder="Enter specific instructions...", key="me" + iter_no, height=125)

    # 데이터 저장 버튼
    if st.button("🚀 COMPLETE & SAVE DATA", type="primary"):
        if not case_no or f_doc in ["선택", ""]:
            st.error("❗ Case Number and Doctor selection are required.")
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
            st.success("🎉 Case Successfully Registered!")
            time.sleep(1)
            reset_all()
            st.rerun()

# --- [TAB 2: 정산] ---
with t2:
    st.markdown("### 💰 Monthly Performance Stats")
    today = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("Select Year", range(today.year, today.year - 5, -1))
    s_m = sm.selectbox("Select Month", range(1, 13), index=today.month - 1)
    
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['SD_DT'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD_DT'].dt.year == s_y) & (pdf['SD_DT'].dt.month == s_m)]
        
        if not m_dt.empty:
            st.dataframe(m_dt[['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Total']], use_container_width=True, hide_index=True)
            norm_cases = m_dt[m_dt['Status'].str.lower() == 'normal']
            tot_qty = pd.to_numeric(norm_cases['Qty'], errors='coerce').sum()
            tot_amt = pd.to_numeric(norm_cases['Total'], errors='coerce').sum()
            
            m1, m2 = st.columns(2)
            m1.metric("Total Quantity", f"{int(tot_qty)} Units")
            m2.metric("Estimated Revenue", f"${int(tot_amt):,}")
        else:
            st.info("No data found for the selected month.")

# --- [TAB 3: 검색] ---
with t3:
    st.markdown("### 🔍 Case Database Search")
    q_s = st.text_input("Search by Case # or Patient Name", placeholder="Search...")
    if not main_df.empty:
        if q_s:
            f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True, hide_index=True)
        else:
            st.write("Recent Cases (Latest 15)")
            st.dataframe(main_df.tail(15), use_container_width=True, hide_index=True)
