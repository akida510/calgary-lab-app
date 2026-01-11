import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 가독성 끝판왕 CSS
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 1. 전체 배경과 텍스트 색상 강제 고정 */
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
        color: #000000 !important;
    }

    /* 2. 입력창 위에 있는 라벨(Case Number, 환자명 등) 글자색 강제 검정 */
    [data-testid="stWidgetLabel"] p {
        color: #000000 !important;
        font-size: 16px !important;
        font-weight: 700 !important; /* 글씨 두껍게 */
    }

    /* 3. 상단 헤더 섹션 */
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #f8f9fa;
        padding: 20px 30px;
        border-radius: 10px;
        margin-bottom: 25px;
        border: 2px solid #000000; /* 테두리도 검정색으로 확실하게 */
    }

    /* 4. 입력창(Input Box) 테두리와 글자 */
    input, div[data-baseweb="select"], .stNumberInput input {
        border: 1.5px solid #000000 !important;
        color: #000000 !important;
    }

    /* 5. 세부 설정 박스 (Expander) 배경 및 제목 */
    div[data-testid="stExpander"] {
        background-color: #ffffff !important;
        border: 1px solid #000000 !important;
        border-radius: 8px !important;
    }
    
    summary {
        color: #000000 !important;
        font-weight: 800 !important;
    }

    /* 6. 저장 버튼 */
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

# 💡 제목과 제작자 정보 (고정)
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

conn = st.connection("gsheets", type=GSheetsConnection)

# 핵심 로직 세션 관리
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

with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    
    st.markdown("### 📋 정보 입력 섹션")
    
    col_a, col_b, col_c = st.columns(3)
    
    # 💡 이 부분의 글자들이 이제 선명하게 보일 것입니다.
    case_no = col_a.text_input("Case Number", placeholder="번호 입력", key="c" + iter_no)
    patient = col_a.text_input("환자명 (Patient)", placeholder="환자 성함", key="p" + iter_no)
    
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
            st.success("저장되었습니다!")
            time.sleep(1)
            reset_all()
            st.rerun()

# --- 정산 및 검색 ---
with t2:
    st.subheader("월간 정산 데이터")
    # ... (기존 통계 로직과 동일) ...

with t3:
    st.subheader("DB 케이스 검색")
    # ... (기존 검색 로직과 동일) ...
