import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    .invoice-wrapper { display: flex; justify-content: center; padding: 20px; background-color: #262730; }
    .invoice-paper {
        background-color: #ffffff !important;
        width: 100%; max-width: 800px; 
        aspect-ratio: 8.5 / 11; padding: 50px; border: 1px solid #000;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; box-sizing: border-box;
    }
    .invoice-paper * {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        font-family: 'Arial', sans-serif !important;
    }
    .logo-main { font-size: 58px !important; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 1; }
    .patient-line { margin: 25px 0; padding: 15px 0; border-top: 2.5px solid black; border-bottom: 2.5px solid black; font-size: 20px; font-weight: bold; }
    .item-table { width: 100%; border-collapse: collapse; flex-grow: 1; }
    .item-table th { border-bottom: 1.5px solid black; padding: 10px 0; text-align: left; }
    .item-table td { padding: 25px 0; font-size: 17px; }
    .bottom-box { margin-top: auto; }
    .notice-box { border: 1.5px solid black; padding: 15px; text-align: center; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 초기화]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806", "Region": "Courier"},
    {"Clinic": "Calgary Central Dental", "Doctor": "Dr. Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"}
])

def get_business_day(start_date, days):
    curr = start_date
    while days > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days -= 1
    return curr

# [3. UI 및 로직]
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET177")
        patient = st.text_input("Patient(환자명)")
        
        # 병원/의사 연동
        cln_list = ["선택"] + sorted(ref_data["Clinic"].tolist())
        doc_list = ["선택"] + sorted(ref_data["Doctor"].tolist())
        def sync_c():
            if st.session_state.ck != "선택":
                st.session_state.dk = ref_data[ref_data["Clinic"] == st.session_state.ck]["Doctor"].iloc[0]
        def sync_d():
            if st.session_state.dk != "선택":
                st.session_state.ck = ref_data[ref_data["Doctor"] == st.session_state.dk]["Clinic"].iloc[0]

        st.selectbox("Clinic(병원명)", cln_list, key="ck", on_change=sync_c)
        st.selectbox("Doctor(의사명)", doc_list, key="dk", on_change=sync_d)

    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        
        # [수정 핵심] 3D Model 체크 시 텍스트 '-' 표시, 체크 해제 시 날짜 입력창 활성화
        if is_3d:
            st.text_input("접수일(Received Date)", value="-", disabled=True)
            final_rec_date = "-"
        else:
            final_rec_date = st.date_input("접수일(Received Date)", value=date.today())

        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    
    clinic_reg = "Courier"
    if st.session_state.ck != "선택":
        clinic_reg = ref_data[ref_data["Clinic"] == st.session_state.ck]["Region"].iloc[0]

    with col5: due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
    with col4:
        ship_days = 1 if clinic_reg == "Local" else 2
        st.date_input("출고일 (Shipping Date)", get_business_day(due_date, ship_days))

    if st.button("💾 케이스 저장 및 등록"):
        if st.session_state.ck == "선택" or not case_no:
            st.error("필수 정보를 입력해주세요.")
        else:
            info = ref_data[ref_data["Clinic"] == st.session_state.ck].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": st.session_state.ck,
                "Doctor": st.session_state.dk, "Address": info["Address"], "Phone": info["Phone"],
                "Material": material, "Arch": arch, "Status": "진행중",
                "Received Date": final_rec_date
            })
            st.success(f"{case_no} 등록 완료!")

# [ tab2 리스트 및 인보이스 코드는 v4.4와 동일하므로 생략하지만, 
#   실제 연동 시에는 final_rec_date 데이터가 db에 저장됩니다. ]
