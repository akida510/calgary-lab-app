import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image

# [수정 금지] 기본 디자인 및 테마 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMetric p { color: #ffffff !important; font-weight: 600 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important;
    }
    .stButton>button {
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important;
        color: white !important; font-weight: bold; border-radius: 5px; border: none;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;">🦷 Skycad Lab Night Guard Manager</div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 14px;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [로직 영역] 임시 레퍼런스 데이터 (나중에 시트와 연결)
# ---------------------------------------------------------
if 'ref_data' not in st.session_state:
    st.session_state.ref_data = pd.DataFrame([
        {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local"},
        {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier"},
    ])

# ---------------------------------------------------------
# [함수] 날짜 및 연동 로직
# ---------------------------------------------------------
def get_shipping_date(due_date, clinic_name):
    ref = st.session_state.ref_data
    region = ref[ref['Clinic'] == clinic_name]['Region'].values
    if len(region) > 0 and region[0] == "Local":
        return due_date - timedelta(days=1)
    return due_date - timedelta(days=2)

# ---------------------------------------------------------
# [메인 화면]
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 프리스크립션 등록", "📊 정산 리스트", "🔍 검색"])

with tab1:
    st.subheader("📷 사진 인식 및 입력")
    
    # 사진 업로드/촬영
    uploaded_file = st.file_uploader("프리스크립션 사진을 찍거나 업로드하세요", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        st.info("🤖 AI가 사진을 분석하여 아래 양식을 자동으로 채웁니다... (Gemini 연동 예정)")
        # 여기서 AI 분석 로직이 들어갈 예정 (현재는 수동 입력 가능 상태)

    st.divider()
    
    # 레이아웃 구성
    col1, col2 = st.columns(2)
    
    with col1:
        case_no = st.text_input("Case # (워크팬 번호)", placeholder="예: ET33")
        patient = st.text_input("Patient (환자명)")
        
        # 클리닉 ↔ 의사 상호 연동 선택창
        clinics = st.session_state.ref_data['Clinic'].tolist()
        doctors = st.session_state.ref_data['Doctor'].tolist()
        
        sel_clinic = st.selectbox("Clinic (병원명)", ["선택"] + clinics)
        sel_doctor = st.selectbox("Doctor (의사명)", ["선택"] + doctors)
        
    with col2:
        is_3d = st.checkbox("3D 모델 수신 (체크 시 날짜 '-' 표시)")
        model_date = "-" if is_3d else st.date_input("모델 수신일", date.today())
        
        material = st.radio("Material (재질)", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch (위치)", ["Maxillary", "Mandibular", "Both"], horizontal=True)
        
    st.divider()
    
    col3, col4, col5 = st.columns(3)
    
    with col5:
        due_date = st.date_input("4th - Due Date (마감일)", date.today() + timedelta(days=7))
        
    with col3:
        # 작업 완료일 기본값: 오늘 + 1일
        lab_done = st.date_input("2nd - Lab Done (작업완료일)", date.today() + timedelta(days=1))
        
    with col4:
        # 클리닉 지역에 따른 쉬핑일 자동 계산
        ship_date = get_shipping_date(due_date, sel_clinic)
        st.date_input("3rd - Shipping Date (쉬핑일)", ship_date)

    if st.button("🚀 데이터 저장하기"):
        st.success(f"{case_no} 케이스가 등록되었습니다! (완료 시 리스트에 색상이 표시됩니다)")

with tab2:
    st.subheader("📊 작업 및 정산 현황")
    st.write("작업이 완료된 항목은 워크팬 번호가 강조됩니다.")
    # 임시 데이터 테이블 시각화 로직 들어갈 자리

with tab3:
    st.subheader("🔍 케이스 검색")
    st.text_input("검색어를 입력하세요 (Case #, Patient...)")
