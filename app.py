import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import json
import io

# 1. 디자인 및 테마 고정 (다크 네이비)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    .stFileUploader section { background-color: #1a1c24 !important; border: 2px dashed #4c6ef5 !important; }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, .stMetric p { color: #ffffff !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"] { background-color: #1a1c24 !important; color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> SKYCAD Dental Lab NIGHT GUARD Manager </div>
        <div style="text-align: right; color: #ffffff;">
            <span style="font-size: 18px; font-weight: 600;">Designed by Heechul Jung</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

# AI 설정 (가장 빠른 8B 모델 사용)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 데이터 로드
@st.cache_data(ttl=1)
def get_data():
    try: return conn.read(ttl=0).astype(str)
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ref():
    try: return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 🚀 초고속 AI 분석 함수
def run_ai_analysis(img_file):
    try:
        # 응답 속도가 가장 빠른 8b 모델로 변경
        model = genai.GenerativeModel('gemini-1.5-flash-8b')
        img = Image.open(img_file)
        
        # 이미지 사이즈를 더 작게 줄여 전송 속도 극대화 (텍스트 인식에 충분한 600px)
        img.thumbnail((600, 600))
        
        # 프롬프트를 AI가 고민 안 하도록 JSON 구조만 딱 던져줌
        prompt = "OCR this dental order to JSON: {case_no, patient, clinic, doctor, arch, material}"
        
        response = model.generate_content([prompt, img])
        text = response.text.strip()
        
        # 결과 추출
        if "{" in text:
            start = text.find("{")
            end = text.rfind("}") + 1
            return json.loads(text[start:end])
        return None
    except:
        return None

t1, t2, t3 = st.tabs(["📝 등록", "📊 통계", "🔍 검색"])

with t1:
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
    
    with st.expander("📸 의뢰서 촬영 및 초고속 분석", expanded=True):
        cam_img = st.file_uploader("카메라 열기", type=["jpg","jpeg","png"], key="full_cam")
        
        if cam_img and st.button("✨ 1초 분석 시작"):
            with st.status("분석 중...", expanded=True) as status:
                res = run_ai_analysis(cam_img)
                if res:
                    st.session_state["c" + iter_no] = str(res.get("case_no", ""))
                    st.session_state["p" + iter_no] = str(res.get("patient", ""))
                    if res.get("clinic") in clinics_list: st.session_state["sc_box" + iter_no] = res["clinic"]
                    if res.get("doctor") in docs_list: st.session_state["sd" + iter_no] = res["doctor"]
                    status.update(label="분석 완료!", state="complete", expanded=False)
                    st.rerun()
                else:
                    status.update(label="분석 실패 (직접 입력해주세요)", state="error")

    # 정보 확인 섹션
    st.markdown("### 📋 정보 확인")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명", key="p" + iter_no)
    sel_cl = c2.selectbox("병원", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no)
    final_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl == "➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    sel_doc = c3.selectbox("의사", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no)
    final_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc == "➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("⚙️ 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no)
        cp = d2.date_input("완료일", date.today()+timedelta(1), key="cp" + iter_no)
        stt = d3.selectbox("상태", ["Normal","Hold","Canceled"], key="st" + iter_no)

    # 💡 체크리스트 및 메모 (유지)
    with st.expander("📂 특이사항 및 체크리스트", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("체크리스트", chks_list, key="ck" + iter_no)
        memo = col_ex2.text_area("메모", key="me" + iter_no, height=100)

    if st.button("🚀 최종 저장"):
        if not case_no: st.error("번호를 입력하세요.")
        else:
            new_row = {"Case #": case_no, "Clinic": final_cl, "Doctor": final_doc, "Patient": patient, "Arch": arch, "Material": mat, "Receipt Date": rd.strftime('%Y-%m-%d'), "Completed Date": cp.strftime('%Y-%m-%d'), "Status": stt, "Notes": ", ".join(chks) + f" | {memo}"}
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장되었습니다!")
            st.session_state.it += 1
            st.rerun()

# 검색/통계 생략 (동일 유지)
