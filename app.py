import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time
import google.generativeai as genai  # AI 분석을 위한 라이브러리
from PIL import Image

# 1. 페이지 설정 및 다크 네이비 테마 (디자인 절대 고정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
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
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, [data-testid="stExpander"] p, .stMetric p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    div[data-testid="stRadio"] label, .stCheckbox label span, button[data-baseweb="tab"] div {
        color: #ffffff !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important;
        color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    .stButton>button {
        width: 100%;
        height: 3.5em;
        background-color: #4c6ef5 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 5px;
        border: none !important;
    }
    [data-testid="stMetricValue"] {
        color: #4c6ef5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 💡 고정 제목 및 제작자 정보
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;">
            Skycad Dental Lab Night Guard Manager
        </div>
        <div style="text-align: right; color: #ffffff;">
            <span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 데이터 로드
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
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 💡 AI 분석 로직 (Gemini 활용)
def analyze_image(uploaded_image):
    # API 키는 보안상 Streamlit secrets에 넣거나 직접 입력 필요
    # genai.configure(api_key="YOUR_GEMINI_API_KEY") 
    model = genai.GenerativeModel('gemini-1.5-flash')
    img = Image.open(uploaded_image)
    prompt = """
    치과 기공 의뢰서 사진입니다. 다음 항목을 추출해서 JSON 형식으로만 답해주세요.
    항목: clinic_name, doctor_name, patient_name, arch(Maxillary/Mandibular), material(Thermo/Dual/Soft/Hard), receipt_date(YYYY-MM-DD), shipping_date(YYYY-MM-DD), due_date(YYYY-MM-DD), notes
    모르는 항목은 빈 문자열로 두세요.
    """
    try:
        response = model.generate_content([prompt, img])
        return response.text
    except:
        return None

# 양방향 동기화 로직
def on_doctor_change():
    sel_doc = st.session_state["sd" + iter_no]
    if sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty: st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

def on_clinic_change():
    sel_cl = st.session_state["sc_box" + iter_no]
    if sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty: st.session_state["sd" + iter_no] = match.iloc[0, 2]

# 세션 초기화
if "sd" + iter_no not in st.session_state: st.session_state["sd" + iter_no] = "선택"
if "sc_box" + iter_no not in st.session_state: st.session_state["sc_box" + iter_no] = "선택"

def reset_all():
    st.session_state.it += 1
    st.cache_data.clear()

t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 및 정산 (Analytics)", "🔍 검색 (Search)"])

with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
    
    st.markdown("### 📋 정보 입력")
    
    # 📸 사진 촬영 및 AI 분석 섹션 (최상단 배치)
    with st.expander("📸 의뢰서 사진 촬영 및 AI 자동 입력", expanded=True):
        cam_col, btn_col = st.columns([0.7, 0.3])
        # 핸드폰 환경에서 카메라 호출
        taken_img = cam_col.camera_input("의뢰서 사진을 찍어주세요")
        if taken_img and btn_col.button("✨ AI 분석 및 자동 입력"):
            with st.spinner("AI가 의뢰서를 분석 중입니다..."):
                # 이 부분에 실제 AI 연동 로직이 들어갑니다. (현재는 UI 틀 제공)
                # 실제 적용 시 분석된 결과로 session_state 값들을 업데이트합니다.
                st.info("AI 분석 기능은 API 연결 후 즉시 활성화됩니다.")
                time.sleep(1)

    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명 (Patient)", key="p" + iter_no)
    
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no, on_change=on_clinic_change)
    final_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")

    sel_doc = c3.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=on_doctor_change)
    final_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("생산 세부 설정 (Production Details)", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("수량 (Qty)", 1, 10, 1, key="qy" + iter_no)
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        cp = d2.date_input("완료예정일", date.today()+timedelta(1), key="cp" + iter_no)
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no)
        shp_val = d3.date_input("Shipping Date (출고)", key="shp" + iter_no)
        stt = d3.selectbox("상태 (Status)", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("📂 특이사항 (Notes)", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan' and str(x)!='Price'])))
            chks = col_ex1.multiselect("체크리스트 선택", chks_list, key="ck" + iter_no)
        memo = col_ex2.text_area("기타 메모", key="me" + iter_no, height=100)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number를 입력해주세요.")
        else:
            p_u = 180
            if final_cl and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == final_cl]
                if not p_m.empty:
                    try: p_u = int(float(p_m.iloc[0, 3]))
                    except: p_u = 180
            
            new_row = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient, 
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": rd.strftime('%Y-%m-%d'), "Completed Date": cp.strftime('%Y-%m-%d'),
                "Shipping Date": shp_val.strftime('%Y-%m-%d'), "Due Date": due_val.strftime('%Y-%m-%d'),
                "Status": stt, "Notes": ", ".join(chks) + f" | {memo}"
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장 완료!")
            time.sleep(1)
            reset_all()
            st.rerun()

# [T2, T3 로직은 이전과 동일하게 유지]
