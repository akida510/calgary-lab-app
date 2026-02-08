import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정 및 테마 강제 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 글자색 강제 고정 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 입력창 디자인 */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }
    
    /* 라벨 가독성 */
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }

    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; 
    }

    /* Tab 2 완료/출력 버튼 (슬림하게) */
    div[data-testid="column"] .stButton>button {
        height: 26px !important; width: auto !important; font-size: 11px !important;
        padding: 0 15px !important; background-color: #2b3a67 !important;
        border: 1px solid #4c6ef5 !important; min-height: 26px !important;
    }
    
    /* 인보이스 박스 제거 및 화면 최적화 */
    .invoice-print-area {
        background-color: white !important; color: black !important; 
        padding: 40px; font-family: 'Arial', sans-serif;
        max-width: 850px; margin: 0 auto; /* 중앙 정렬 및 넘침 방지 */
        position: relative;
    }
    .invoice-print-area * { color: black !important; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-print-area { display: block !important; width: 100% !important; padding: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 관리] 
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

# 병원 정보 (주소/전화번호 추가)
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
st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Heechul Jung Edition</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

# --- Tab 1: 케이스 등록 (희철님 원본 코드 복구) ---
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
    with col5: 
        due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: 
        lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장 (접수 완료)"):
        if sel_clinic == "선택" or not case_no:
            st.error("Case No와 Clinic은 필수 입력 사항입니다.")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            new_case = {
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Received": rec_date, "Due": due_date, "Lab Done": lab_done_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            }
            st.session_state.db.append(new_case)
            st.success(f"{case_no}번 케이스 등록 완료!")

# --- Tab 2: 리스트 및 완료 (박스 없는 인보이스) ---
with tab2:
    if not st.session_state.db:
        st.info("현재 대기 중인 케이스가 없습니다.")
    else:
        for i, row in enumerate(st.session_state.db):
            c_info, c_btn = st.columns([5, 1])
            with c_info:
                st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']} | Due: {row['Due']}")
            with c_btn:
                if st.button("Complete/Print", key=f"btn_{i}"):
                    st.session_state.selected_invoice = row
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # 인보이스 레이아웃 (박스 테두리 제거 버전)
        st.markdown(f"""
        <div class="invoice-print-area">
            <div style="display: flex; justify-content: space-between;">
                <div style="width: 50%;">
                    <div style="font-size: 11px; font-weight: bold; font-style: italic; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                    <div style="font-size: 65px; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 0.8; letter-spacing: -4px;">skycad</div>
                    <div style="margin-top: 20px; font-size: 13px;">
                        <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                    </div>
                </div>
                <div style="text-align: right; width: 45%;">
                    <div style="font-size: 30px; font-weight: bold; letter-spacing: 4px;">INVOICE</div>
                    <div style="font-size: 15px; margin-top: 5px; font-weight: bold;">No. 162{inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%m/%d/%Y')}</div>
                    <div style="margin-top: 30px; text-align: left; font-size: 13px; line-height: 1.4; border: 1px solid black; padding: 12px; width: 220px; float: right;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}<br>{inv['Phone']}
                    </div>
                </div>
            </div>

            <div style="margin: 60px 0 15px 0; font-size: 16px; border-bottom: 2px solid black; padding-bottom: 8px;">
                <b>Patient:</b> {str(inv['Patient']).upper()}
            </div>

            <table style="width: 100%; border-collapse: collapse;">
                <tr style="border-bottom: 1.2px solid black; font-weight: bold; font-size: 14px;">
                    <td style="padding: 10px 0; text-decoration: underline;">Description</td>
                    <td style="padding: 10px 0; text-align: right; text-decoration: underline;">Amount</td>
                </tr>
                <tr>
                    <td style="padding: 20px 0; height: 350px; vertical-align: top; font-size: 15px;">
                        Nightguard ({inv['Material']}) {inv['Arch'].upper()}
                    </td>
                    <td style="padding: 20px 0; text-align: right; vertical-align: top; font-size: 15px;">$180.00</td>
                </tr>
            </table>

            <div style="border-top: 2px solid black; padding-top: 10px; display: flex; justify-content: space-between; font-weight: bold; font-size: 16px;">
                <span>{inv['Case No']}</span>
                <span>Total: $180.00</span>
            </div>

            <div style="margin-top: 80px; text-align: center;">
                <div style="font-size: 16px; font-weight: bold; text-decoration: underline; margin-bottom: 15px;">
                    All dental products we offer are custom made in Canada.
                </div>
                <div style="font-size: 10px; line-height: 1.5; color: #555 !important;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("PRINT INVOICE"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3:
    st.write("🔍 검색 기능 준비 중")
