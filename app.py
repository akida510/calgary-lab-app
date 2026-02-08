import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정 및 테마 강제 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 글자색 강제 고정 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }
    
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }

    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 15px 20px; border-radius: 10px;
        margin-bottom: 20px; border: 1px solid #30363d;
    }
    
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; 
    }

    /* 리스트 버튼 슬림화 (모바일 대응) */
    div[data-testid="column"] .stButton>button {
        height: 32px !important; width: auto !important; font-size: 12px !important;
        padding: 0 10px !important; background-color: #2b3a67 !important;
    }
    
    /* 인보이스 컨테이너: 모바일에서 안 잘리게 '반응형' 설정 */
    .invoice-container {
        background-color: white !important; color: black !important; 
        padding: 5% !important; 
        font-family: 'Arial', sans-serif;
        width: 100% !important;
        max-width: 800px;
        margin: 0 auto;
        box-sizing: border-box; /* 패딩이 너비에 포함되게 */
    }
    .invoice-container * { color: black !important; border-color: black !important; }

    /* 모바일용 텍스트 크기 미세 조정 */
    @media screen and (max-width: 600px) {
        .invoice-container { padding: 15px !important; }
        .skycad-logo { font-size: 45px !important; }
        .invoice-header-right { font-size: 12px !important; }
        .ship-to-box { width: 100% !important; float: none !important; margin-top: 15px !important; }
    }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-container { display: block !important; border: none !important; padding: 0 !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 관리] 
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Arshpreet Kaur", "Region": "Courier", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# ---------------------------------------------------------
# [메인 화면]
# ---------------------------------------------------------
st.markdown(f'<div class="header-container"><div style="font-size: 20px; font-weight: 800;">🦷 Skycad Lab Manager</div><div style="font-size: 10px;">Designed By Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)", placeholder="환자 성함")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
        filtered_docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + filtered_docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        if is_3d:
            st.text_input("접수일", value=today.strftime("%Y-%m-%d"), disabled=True)
            rec_date = today
        else:
            rec_date = st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일", today + timedelta(days=1))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("출고일", ship_date)

    if st.button("💾 케이스 저장"):
        if sel_clinic == "선택" or not case_no:
            st.error("필수 정보를 입력해주세요.")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Received": rec_date, "Due": due_date, "Lab Done": lab_done_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success(f"등록 완료!")

with tab2:
    if not st.session_state.db:
        st.info("진행 중인 케이스가 없습니다.")
    else:
        for i, row in enumerate(st.session_state.db):
            c_info, c_btn = st.columns([4, 1.5])
            with c_info: st.write(f"**{row['Case No']}** | {row['Patient']}")
            with c_btn:
                if st.button("완료/출력", key=f"p_{i}"):
                    st.session_state.selected_invoice = row
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        
        # 반응형 인보이스 (Table 대신 Flex 사용으로 모바일 최적화)
        st.markdown(f"""
        <div class="invoice-container">
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between; align-items: flex-start;">
                <div style="flex: 1; min-width: 200px;">
                    <div style="font-size: 10px; font-weight: bold; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                    <div class="skycad-logo" style="font-size: 60px; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 0.8; letter-spacing: -3px;">skycad</div>
                    <div style="margin-top: 15px; font-size: 13px;">
                        <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                    </div>
                </div>
                <div class="invoice-header-right" style="flex: 1; min-width: 200px; text-align: right;">
                    <div style="font-size: 28px; font-weight: bold; letter-spacing: 3px;">INVOICE</div>
                    <div style="font-size: 14px; font-weight: bold;">No. 162{inv['Case No'].replace('ET', '')}<br>{inv['Lab Done'].strftime('%m/%d/%Y')}</div>
                    <div class="ship-to-box" style="margin-top: 20px; text-align: left; font-size: 13px; border: 1px solid black; padding: 10px; display: inline-block; width: 220px;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}<br>{inv['Phone']}
                    </div>
                </div>
            </div>

            <div style="margin: 40px 0 10px 0; font-size: 16px; border-bottom: 2px solid black; padding-bottom: 5px;">
                <b>Patient:</b> {str(inv['Patient']).upper()}
            </div>

            <div style="display: flex; justify-content: space-between; border-bottom: 1px solid black; font-weight: bold; padding: 10px 0;">
                <span style="text-decoration: underline;">Description</span>
                <span style="text-decoration: underline;">Amount</span>
            </div>
            
            <div style="display: flex; justify-content: space-between; min-height: 300px; padding-top: 15px; font-size: 15px;">
                <span>Nightguard ({inv['Material']}) {inv['Arch'].upper()}</span>
                <span>$180.00</span>
            </div>

            <div style="border-top: 2px solid black; padding-top: 5px; display: flex; justify-content: space-between; font-weight: bold; font-size: 16px;">
                <span>{inv['Case No']}</span>
                <span>Total: $180.00</span>
            </div>

            <div style="margin-top: 50px; text-align: center;">
                <div style="font-size: 14px; font-weight: bold; text-decoration: underline; margin-bottom: 10px;">All dental products we offer are custom made in Canada.</div>
                <div style="font-size: 9px; line-height: 1.4; color: #444 !important;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Balances over 30 days will be subject to a finance charge of 1.5% per month (19.562% APR). Thank you.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ PRINT"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("검색 기능 준비 중")
