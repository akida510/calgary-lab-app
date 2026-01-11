import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 가시성 강제 고정 CSS (가장 중요)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 1. 전체 배경 및 시스템 텍스트 강제 검정색 고정 */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* 2. 상단 탭 메뉴 글자색 (월간통계, 검색 등) */
    button[data-baseweb="tab"] div {
        color: #000000 !important;
        font-weight: 700 !important;
    }
    
    /* 3. 라벨 및 일반 텍스트 (Case Number, 환자명, Maxillary 등 모든 텍스트) */
    [data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p, label p {
        color: #000000 !important;
        font-weight: 700 !important;
        font-size: 16px !important;
    }

    /* 4. 라디오 버튼 텍스트색 강제 고정 */
    div[data-testid="stRadio"] label div {
        color: #000000 !important;
        font-weight: 600 !important;
    }

    /* 5. 입력창 테두리 및 내부 텍스트 */
    input, div[data-baseweb="select"], .stNumberInput input, textarea {
        border: 2px solid #212529 !important;
        color: #000000 !important;
        background-color: #ffffff !important;
    }

    /* 6. 헤더 디자인 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #f1f3f5;
        padding: 20px 35px;
        border-radius: 12px;
        margin-bottom: 25px;
        border: 2px solid #000000;
    }

    /* 7. 저장 버튼 */
    .stButton>button {
        width: 100%;
        height: 3.5em;
        background-color: #000000 !important;
        color: #ffffff !important;
        font-weight: bold !important;
        font-size: 18px !important;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# 헤더: 제목과 제작자 (요청하신 대로 고정)
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #000000;">
            Skycad Dental Lab Night Guard Manager
        </div>
        <div style="text-align: right; color: #000000;">
            <span style="font-size: 18px; font-weight: 700;">Designed By Heechul Jung</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 관리 (새로고침 시 데이터 유지)
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 날짜 계산 로직
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

# 의사-병원 자동 매칭 함수
def update_clinic_from_doctor():
    selected_doctor = st.session_state["sd" + iter_no]
    if selected_doctor not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == selected_doctor]
        if not match.empty:
            st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

# 탭 메뉴 구성
t1, t2, t3 = st.tabs(["📝 데이터 입력 (Register)", "📊 월간 통계 (Analytics)", "🔍 케이스 검색 (Search)"])

# --- [TAB 1: 등록] ---
with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    
    st.markdown("### 📋 신규 케이스 등록")
    
    col_a, col_b, col_c = st.columns(3)
    case_no = col_a.text_input("Case Number", key="c" + iter_no)
    patient = col_a.text_input("환자명 (Patient)", key="p" + iter_no)
    
    sel_doc = col_c.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=update_clinic_from_doctor)
    f_doc = col_c.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else sel_doc

    if "sc_box" + iter_no not in st.session_state: st.session_state["sc_box" + iter_no] = "선택"
    sel_cl = col_b.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    f_cl = col_b.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else sel_cl

    st.markdown("<br>", unsafe_allow_html=True)
    
    with st.expander("⚙️ 생산 세부 설정 (Production Details)", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("수량 (Qty)", 1, 10, 1, key="qy" + iter_no)
        
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no, disabled=is_33)
        cp = d2.date_input("완료예정일", date.today()+timedelta(1), key="cp" + iter_no)
        
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date (출고)", key="shp" + iter_no)
        stt = d3.selectbox("상태 (Status)", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("📂 메모 및 사진 (Notes)", expanded=True):
        c_ex1, c_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan'])))
            chks = c_ex1.multiselect("특이사항 선택", chks_list, key="ck" + iter_no)
        
        uploaded_file = c_ex1.file_uploader("사진 첨부", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = c_ex2.text_area("비고 사항", key="me" + iter_no, height=125)

    if st.button("🚀 데이터 저장 (SAVE CASE)"):
        if not case_no or f_doc in ["선택", ""]:
            st.error("Case #와 의사명은 필수입니다.")
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
            st.success("데이터가 성공적으로 저장되었습니다.")
            time.sleep(1)
            reset_all()
            st.rerun()

# --- [TAB 2: 통계] ---
with t2:
    st.markdown("### 💰 월간 정산 현황")
    today = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("연도 선택", range(today.year, today.year - 5, -1))
    s_m = sm.selectbox("월 선택", range(1, 13), index=today.month - 1)
    
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
            m1.metric("총 수량", f"{int(tot_qty)} ea")
            m2.metric("총 합계", f"${int(tot_amt):,}")
        else:
            st.info("해당 월의 데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    st.markdown("### 🔍 케이스 통합 검색")
    q_s = st.text_input("케이스 번호 또는 환자명 입력", placeholder="검색어를 입력하세요...")
    if not main_df.empty:
        if q_s:
            f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True, hide_index=True)
        else:
            st.write("최근 등록 케이스 (15건)")
            st.dataframe(main_df.tail(15), use_container_width=True, hide_index=True)
