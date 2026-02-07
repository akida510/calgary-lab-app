import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image

# [수정 금지] 디자인 강제 고정
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
    /* 인보이스 박스 스타일 */
    .invoice-box {
        background-color: white; color: black; padding: 40px;
        border: 1px solid #ddd; border-radius: 5px; font-family: 'Courier New', Courier, monospace;
        margin-top: 20px; line-height: 1.6;
    }
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
tab1, tab2, tab3 = st.tabs(["📝 등록 및 완료", "📊 정산", "🔍 검색"])

with tab1:
    uploaded_file = st.file_uploader("📷 프리스크립션 사진 촬영/업로드", type=["jpg", "jpeg", "png"])
    
    st.markdown("### 📋 정보 입력 및 저장")
    c1, c2 = st.columns(2)
    
    with c1:
        case_no = st.text_input("Case # (워크팬 번호)", placeholder="예: ET33")
        patient = st.text_input("Patient (환자명)", placeholder="환자 성함을 입력하세요")
        clinics = st.session_state.ref_data['Clinic'].tolist()
        doctors = st.session_state.ref_data['Doctor'].tolist()
        sel_clinic = st.selectbox("Clinic (병원명)", ["선택"] + clinics)
        sel_doctor = st.selectbox("Doctor (의사명)", ["선택"] + doctors)
        
    with c2:
        is_3d = st.checkbox("3D 모델 수신")
        model_date = "-" if is_3d else st.date_input("모델 수신일", date.today())
        material = st.radio("Material (재질)", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch (위치)", ["Max", "Mand", "Both"], horizontal=True)
        
    st.markdown("---")
    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    
    with col5:
        due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col3:
        lab_done = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
    with col4:
        ship_date = get_shipping_date(due_date, sel_clinic)
        st.date_input("출고일 (Shipping Date)", ship_date)

    st.divider()

    # 저장 및 인보이스 미리보기 로직
    if st.button("🚀 작업 완료 및 인보이스 생성"):
        if not case_no or sel_clinic == "선택":
            st.error("Case #와 Clinic은 필수 입력 사항입니다.")
        else:
            st.success("데이터가 저장되었습니다. 인보이스를 확인해 주세요.")
            
            # 인보이스 미리보기 영역
            st.markdown("### 📑 Invoice Preview")
            invoice_html = f"""
            <div class="invoice-box">
                <h2 style="text-align: center;">INVOICE</h2>
                <hr>
                <p><strong>Invoice No:</strong> INV-{case_no}-{datetime.now().strftime('%m%d')}</p>
                <p><strong>Clinic:</strong> {sel_clinic}</p>
                <p><strong>Doctor:</strong> {sel_doctor}</p>
                <p><strong>Patient:</strong> {patient}</p>
                <hr>
                <table style="width:100%; text-align:left;">
                    <tr><th>Item Description</th><th>Arch</th><th>Amount</th></tr>
                    <tr><td>Night Guard ({material})</td><td>{arch}</td><td>$ ---.--</td></tr>
                </table>
                <hr>
                <p style="text-align: right;"><strong>Total: $ ---.--</strong></p>
                <p style="font-size: 10px; color: gray;">Completed Date: {lab_done}</p>
            </div>
            """
            st.markdown(invoice_html, unsafe_allow_html=True)
            
            # 실제 출력 버튼 (PDF 등 연동 예정)
            if st.button("🖨️ 인보이스 인쇄하기 (Print)"):
                st.info("프린터 연결 기능을 실행합니다...")

with tab2:
    st.write("📊 정산 현황 및 색상 표시 리스트 준비 중")

with tab3:
    st.write("🔍 검색 화면 준비 중")
