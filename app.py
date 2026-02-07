import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

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
    .metric-card {
        background-color: #1a1c24; padding: 20px; border-radius: 10px;
        border-left: 5px solid #4c6ef5; margin-bottom: 10px;
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
# [데이터/로직 영역]
# ---------------------------------------------------------
if 'ref_data' not in st.session_state:
    st.session_state.ref_data = pd.DataFrame([
        {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local"},
        {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier"},
        {"Clinic": "Calgary Central", "Doctor": "Dr. Smith", "Region": "Local"}, # 테스트용 추가
    ])

if 'temp_db' not in st.session_state:
    st.session_state.temp_db = []

def get_shipping_date(due_date, clinic_name):
    ref = st.session_state.ref_data
    region = ref[ref['Clinic'] == clinic_name]['Region'].values
    if len(region) > 0 and region[0] == "Local":
        return due_date - timedelta(days=1)
    return due_date - timedelta(days=2)

# ---------------------------------------------------------
# [메인 화면]
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 등록 및 완료", "📊 정산 대시보드", "🔍 검색"])

with tab1:
    st.markdown("### 📋 정보 입력")
    c1, c2 = st.columns(2)
    
    with c1:
        case_no = st.text_input("Case #", placeholder="예: ET33")
        patient = st.text_input("Patient", placeholder="환자 성함")
        
        # 병원 선택
        clinics = sorted(list(set(st.session_state.ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic", ["선택"] + clinics)
        
        # 병원에 따른 의사 필터링 로직
        if sel_clinic != "선택":
            filtered_docs = st.session_state.ref_data[st.session_state.ref_data['Clinic'] == sel_clinic]['Doctor'].tolist()
        else:
            filtered_docs = []
        
        sel_doctor = st.selectbox("Doctor", ["선택"] + filtered_docs)
        
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        model_date_val = "-" if is_3d else st.date_input("접수일", date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: 
        due_date = st.date_input("요청일 (Due)", date.today() + timedelta(days=7))
    with col3: 
        lab_done = st.date_input("완료일 (Done)", date.today() + timedelta(days=1))
    with col4:
        ship_date = get_shipping_date(due_date, sel_clinic)
        st.date_input("출고일 (Ship)", ship_date)

    if st.button("🚀 작업 완료 및 저장"):
        if sel_clinic == "선택" or not case_no:
            st.error("Case #와 Clinic은 필수입니다!")
        else:
            st.session_state.temp_db.append({
                "Case #": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Done": lab_done, "Status": "Completed"
            })
            st.success(f"{case_no} 저장 완료!")

with tab2:
    st.subheader("📊 정산 및 인센티브")
    
    # 정산 로직
    total_completed = len(st.session_state.temp_db) + 318 # 시뮬레이션
    goal = 320
    extra_count = max(0, total_completed - goal)
    gross_pay = extra_count * 30.0
    net_pay = extra_count * 19.505333
    
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1: st.markdown(f"<div class='metric-card'><b>완료 실적</b><br><span style='font-size:22px;'>{total_completed} / {goal}</span></div>", unsafe_allow_html=True)
    with col_m2: st.markdown(f"<div class='metric-card'><b>초과 수량</b><br><span style='font-size:22px; color:#00ff00;'>+ {extra_count}</span></div>", unsafe_allow_html=True)
    with col_m3: st.markdown(f"<div class='metric-card'><b>세전 수당</b><br><span style='font-size:22px;'>$ {gross_pay:,.2f}</span></div>", unsafe_allow_html=True)
    with col_m4: st.markdown(f"<div class='metric-card'><b>실수령액</b><br><span style='font-size:22px; color:#00ff00;'>$ {net_pay:,.2f}</span></div>", unsafe_allow_html=True)
    
    st.progress(min(1.0, total_completed / goal))
    
    if st.session_state.temp_db:
        st.table(pd.DataFrame(st.session_state.temp_db))

with tab3:
    st.write("🔍 검색 기능 준비 중")
