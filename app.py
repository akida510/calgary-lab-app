import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time
import google.generativeai as genai
from PIL import Image
import json

# 1. 디자인 및 카메라 크기 확장 설정 (절대 고정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    /* 카메라 입력창 크기 대폭 확장 */
    [data-testid="stCameraInput"] {
        width: 100% !important;
    }
    [data-testid="stCameraInput"] > div {
        width: 100% !important;
    }
    video {
        border-radius: 10px;
        width: 100% !important;
        height: auto !important;
    }
    
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, [data-testid="stExpander"] p, .stMetric p {
        color: #ffffff !important; font-weight: 600 !important;
    }
    div[data-testid="stRadio"] label, .stCheckbox label span, button[data-baseweb="tab"] div {
        color: #ffffff !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important;
    }
    .stButton>button {
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important;
        color: white !important; font-weight: bold !important; border-radius: 5px; border: none !important;
    }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; }
    </style>
    """, unsafe_allow_html=True)

# 💡 제목 및 제작자 정보 고정
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> SKYCAD Dental Lab NIGHT GUARD Manager </div>
        <div style="text-align: right; color: #ffffff;">
            <span style="font-size: 18px; font-weight: 600;">Designed by Heechul Jung</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# AI 설정 (Secrets 확인)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

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
    try: return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 💡 최적화된 AI 분석 로직
def run_ai_analysis(img_file):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        img = Image.open(img_file)
        # 응답 속도를 높이기 위해 출력 형식을 매우 단순하게 지시
        prompt = "Analyze dental lab order. Output JSON: {\"case_no\":\"\", \"patient\":\"\", \"clinic\":\"\", \"doctor\":\"\", \"arch\":\"Maxillary or Mandibular\", \"material\":\"Thermo or Dual or Soft or Hard\"}"
        response = model.generate_content([prompt, img])
        # JSON 부분만 골라내기
        text = response.text.strip()
        if "{" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end])
        return None
    except Exception as e:
        st.error(f"AI Error: {e}")
        return None

# 양방향 동기화
def on_doctor_change():
    sel_doc = st.session_state.get("sd" + iter_no)
    if sel_doc and sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty: st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

def on_clinic_change():
    sel_cl = st.session_state.get("sc_box" + iter_no)
    if sel_cl and sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty: st.session_state["sd" + iter_no] = match.iloc[0, 2]

if "sd" + iter_no not in st.session_state: st.session_state["sd" + iter_no] = "선택"
if "sc_box" + iter_no not in st.session_state: st.session_state["sc_box" + iter_no] = "선택"

t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 및 정산 (Analytics)", "🔍 검색 (Search)"])

with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
    
    with st.expander("📸 의뢰서 전체화면 촬영 및 AI 분석", expanded=True):
        cam_img = st.camera_input("의뢰서를 화면 가득 찍어주세요")
        if cam_img and st.button("✨ 사진 내용 즉시 분석"):
            with st.spinner("AI가 분석 중..."):
                res = run_ai_analysis(cam_img)
                if res:
                    # 분석 결과 세션에 저장 (반영 속도 향상)
                    if res.get("case_no"): st.session_state["c" + iter_no] = str(res["case_no"])
                    if res.get("patient"): st.session_state["p" + iter_no] = str(res["patient"])
                    if res.get("clinic") in clinics_list: st.session_state["sc_box" + iter_no] = res["clinic"]
                    if res.get("doctor") in docs_list: st.session_state["sd" + iter_no] = res["doctor"]
                    if res.get("arch") in ["Maxillary", "Mandibular"]: st.session_state["ar" + iter_no] = res["arch"]
                    if res.get("material") in ["Thermo", "Dual", "Soft", "Hard"]: st.session_state["ma" + iter_no] = res["material"]
                    st.success("분석 완료! 데이터가 반영되었습니다.")
                    time.sleep(0.5)
                    st.rerun()

    st.markdown("### 📋 정보 확인")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명 (Patient)", key="p" + iter_no)
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no, on_change=on_clinic_change)
    final_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    sel_doc = c3.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=on_doctor_change)
    final_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("수량", 1, 10, 1, key="qy" + iter_no)
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        cp = d2.date_input("완료예정일", date.today()+timedelta(1), key="cp" + iter_no)
        due_val = d3.date_input("마감일", key="due" + iter_no)
        shp_val = d3.date_input("출고일", key="shp" + iter_no)
        stt = d3.selectbox("상태", ["Normal","Hold","Canceled"], key="st" + iter_no)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number를 입력하세요.")
        else:
            p_u = 180
            if final_cl and not ref.empty:
                match = ref[ref.iloc[:, 1] == final_cl]
                if not match.empty:
                    try: p_u = int(float(match.iloc[0, 3]))
                    except: p_u = 180
            new_row = {"Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient, "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty, "Receipt Date": rd.strftime('%Y-%m-%d'), "Completed Date": cp.strftime('%Y-%m-%d'), "Shipping Date": shp_val.strftime('%Y-%m-%d'), "Due Date": due_val.strftime('%Y-%m-%d'), "Status": stt}
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장 완료!")
            st.session_state.it += 1
            st.rerun()

# 📊 통계 및 🔍 검색 기능 (기존 로직 그대로 유지)
with t2:
    st.markdown("### 💰 정산 및 실적")
    today = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("연도", range(today.year, today.year - 5, -1))
    s_m = sm.selectbox("월", range(1, 13), index=today.month - 1)
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['SD_DT'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        m_dt = pdf[(pdf['SD_DT'].dt.year == s_y) & (pdf['SD_DT'].dt.month == s_m)]
        if not m_dt.empty:
            st.dataframe(m_dt, use_container_width=True, hide_index=True)
            norm_cases = m_dt[m_dt['Status']=='Normal']
            tot_qty = pd.to_numeric(norm_cases['Qty'], errors='coerce').sum()
            tot_amt = pd.to_numeric(norm_cases['Total'], errors='coerce').sum()
            m1, m2, m3 = st.columns(3)
            m1.metric("총 생산", f"{int(tot_qty)} ea")
            m2.metric("부족분(320기준)", f"{max(0, 320-int(tot_qty))} ea")
            m3.metric("총 매출", f"${int(tot_amt):,}")

with t3:
    st.markdown("### 🔍 검색")
    q = st.text_input("검색어(번호/환자)")
    if q and not main_df.empty:
        st.dataframe(main_df[main_df['Case #'].str.contains(q, case=False) | main_df['Patient'].str.contains(q, case=False)], use_container_width=True, hide_index=True)
