import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 다크 네이비 테마 (가독성 보완)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경: 다시 다크 네이비 톤으로 복구 */
    .main { background-color: #0e1117; }
    
    /* 상단 헤더 섹션: 기존 스타일 유지 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1a1c24;
        padding: 20px 30px;
        border-radius: 10px;
        margin-bottom: 25px;
        border: 1px solid #30363d;
    }

    /* 제목 및 제작자 텍스트 색상 (흰색) */
    .header-container div, .header-container span {
        color: #ffffff !important;
    }

    /* 💡 가독성 핵심: 모든 라벨(Case Number 등)과 텍스트를 흰색으로 강제 고정 */
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, [data-testid="stExpander"] p {
        color: #ffffff !important;
        font-weight: 500 !important;
        font-size: 15px !important;
    }
    
    /* 라디오 버튼 및 체크박스 글자색 고정 */
    div[data-testid="stRadio"] label, .stCheckbox label span {
        color: #ffffff !important;
    }

    /* 탭 메뉴 글자색 */
    button[data-baseweb="tab"] div {
        color: #ffffff !important;
    }

    /* 입력창 디자인: 어두운 배경과 대비되도록 밝은 테두리 적용 */
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important;
        color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }

    /* 저장 버튼: 기존의 포인트 컬러 유지 */
    .stButton>button {
        width: 100%;
        height: 3.5em;
        background-color: #4c6ef5 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 5px;
        border: none !important;
    }
    .stButton>button:hover {
        background-color: #3b5bdb !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 💡 제목과 제작자 (요청 사항 유지)
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800;">
            Skycad Dental Lab Night Guard Manager
        </div>
        <div style="text-align: right;">
            <span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 관리 및 날짜 로직
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

def update_clinic_from_doctor():
    selected_doctor = st.session_state["sd" + iter_no]
    if selected_doctor not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == selected_doctor]
        if not match.empty:
            st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

t1, t2, t3 = st.tabs(["📝 데이터 입력 (Register)", "📊 월간 통계 (Analytics)", "🔍 케이스 검색 (Search)"])

# --- [TAB 1: 등록] ---
with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    
    st.markdown("### 📋 Case Information")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명 (Patient)", key="p" + iter_no)
    
    sel_doc = c3.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=update_clinic_from_doctor)
    f_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else sel_doc

    if "sc_box" + iter_no not in st.session_state: st.session_state["sc_box" + iter_no] = "선택"
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else sel_cl

    with st.expander("생산 세부 설정 (Production Details)", expanded=True):
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

    with st.expander("메모 및 사진 (Notes)", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("특이사항 선택", chks_list, key="ck" + iter_no)
        
        uploaded_file = col_ex1.file_uploader("사진 업로드", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = col_ex2.text_area("메모 사항", key="me" + iter_no, height=125)

    if st.button("데이터 저장하기"):
        if not case_no or f_doc in ["선택", ""]:
            st.error("필수 항목을 입력해주세요.")
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
            st.success("저장 완료!")
            time.sleep(1)
            reset_all()
            st.rerun()

# --- [TAB 2 & 3: 통계 및 검색] ---
with t2:
    st.markdown("### 💰 실적 통계")
    if not main_df.empty:
        st.dataframe(main_df.tail(20), use_container_width=True, hide_index=True)

with t3:
    st.markdown("### 🔍 케이스 검색")
    q_s = st.text_input("검색어 입력", key="search_box")
    if not main_df.empty and q_s:
        f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
        st.dataframe(f_df, use_container_width=True, hide_index=True)
