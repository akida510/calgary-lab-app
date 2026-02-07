import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image

# [수정 금지] 디자인 강제 고정 (시스템 테마 무시 및 가독성 보강)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input::placeholder, textarea::placeholder { color: #aaaaaa !important; opacity: 1; }
    label p, .stMarkdown p, .stMetric p { color: #ffffff !important; font-weight: 600 !important; }
    .stTabs [data-baseweb="tab"] { color: #ffffff !important; }
    .stButton>button {
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important;
        color: white !important; font-weight: bold; border-radius: 5px; border: none;
    }
    .stCheckbox, .stRadio { color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 24px; font-weight: 800; color: #ffffff;">🦷 Skycad Lab Night Guard Manager</div>
        <div style="text-align: right; color: #ffffff; font-size: 12px;">Designed By Heechul Jung</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [로직 영역] 데이터 설정
# ---------------------------------------------------------
if 'ref_data' not in st.session_state:
    st.session_state.ref_data = pd.DataFrame([
        {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local"},
        {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier"},
    ])

def get_shipping_date(due_date, clinic_name):
    ref = st.session_state.ref_data
    region = ref[ref['Clinic'] == clinic_name]['Region'].values
    if len(region) > 0 and region[0] == "Local":
        return due_date - timedelta(days=1)
    return due_date - timedelta(days=2)

# ---------------------------------------------------------
# [메인 화면]
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 정산", "🔍 검색"])

with tab1:
    uploaded_file = st.file_uploader("📷 프리스크립션 사진 촬영/업로드", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        st.info("🤖 사진 분석 기능 준비 중입니다.")

    st.markdown("### 📋 기본 정보 입력")
    c1, c2 = st.columns(2)
    
    with c1:
        case_no = st.text_input("Case # (워크팬 번호)", placeholder="예: ET33")
        patient = st.text_input("Patient (환자명)", placeholder="환자 성함을 입력하세요")
        
        clinics = st.session_state.ref_data['Clinic'].tolist()
        doctors = st.session_state.ref_data['Doctor'].tolist()
        
        sel_clinic = st.selectbox("Clinic (병원명)", ["선택"] + clinics)
        sel_doctor = st.selectbox("Doctor (의사명)", ["선택"] + doctors)
        
    with c2:
        is_3d = st.checkbox("3D 모델 수신 (날짜 대신 '-' 표시)")
        if is_3d:
            st.text_input("모델 수신일", "-", disabled=True)
        else:
            st.date_input("모델 수신일", date.today())
        
        material = st.radio("Material (재질)", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch (위치)", ["Max", "Mand", "Both"], horizontal=True)
        
    st.markdown("---")
    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    
    with col5:
        # 4th -> 요청일
        due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
        
    with col3:
        # 2nd -> 완료일
        lab_done = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
        
    with col4:
        # 3rd -> 출고일
        ship_date = get_shipping_date(due_date, sel_clinic)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("🚀 데이터 저장하기"):
        st.success(f"{case_no} 케이스 등록 완료!")

with tab2:
    st.write("📊 정산 및 리스트 화면 준비 중")

with tab3:
    st.write("🔍 검색 화면 준비 중")
