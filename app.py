import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 희철님 원본 디자인 및 테마 강제 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 글자색 강제 고정 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 모든 텍스트 및 라벨 백색 고정 */
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }
    
    /* 입력창 스타일 */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }

    /* 헤더 */
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    
    /* Tab 1 저장 버튼 (원본 크기 유지) */
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; 
    }

    /* Tab 2 완료 버튼 (슬림하게 수정) */
    div[data-testid="column"] .stButton>button {
        height: 24px !important;
        line-height: 24px !important;
        font-size: 10px !important;
        padding: 0px 10px !important;
        background-color: #2b3a67 !important;
        border: 1px solid #4c6ef5 !important;
        margin-top: 5px;
        min-height: 24px !important;
    }

    /* [인보이스 전용 스타일] 사진과 동일한 비율 구성 */
    .invoice-card {
        background-color: white !important; padding: 30px; 
        border: 1.5px solid black !important; /* 사진 속 큰 테두리 */
        font-family: Arial, sans-serif;
        min-height: 950px; position: relative;
    }
    .invoice-card * { color: black !important; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-card { display: block !important; border: 1.5px solid black !important; padding: 30px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Addr": "13510 127 St NW", "City": "Edmonton, Alberta T5L 1B9", "Phone": "(780) 455-6806"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800; color:white !important;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px; color:white !important;">Designed by Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

# --- Tab 1: 등록창 (희철님 원본 그대로) ---
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
    with col5: due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장 (접수 완료)"):
        if sel_clinic == "선택" or not case_no: st.error("필수 정보를 입력하세요.")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Lab Done": lab_done_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success("등록 완료!")

# --- Tab 2: 인보이스 출력 ---
with tab2:
    if not st.session_state.db: st.info("작업 리스트가 비어있습니다.")
    else:
        for i, row in enumerate(st.session_state.db):
            c_info, c_btn = st.columns([5, 1])
            with c_info: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
            with c_btn:
                if st.button("완료/출력", key=f"inv_{i}"):
                    st.session_state.db[i]['Status'] = "Completed"
                    st.session_state.selected_invoice = st.session_state.db[i]
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # [사진 복사] 실제 인보이스 레이아웃
        st.markdown(f"""
        <div class="invoice-card">
            <div style="display: flex; justify-content: space-between;">
                <div style="width: 50%;">
                    <div style="font-size: 11px; font-weight: bold; color: #1a4e8a !important; font-style: italic;">DENTAL TECHNOLOGY Ltd</div>
                    <div style="font-size: 60px; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 0.8; letter-spacing: -3px;">skycad</div>
                    <div style="margin-top: 15px; font-size: 12px; line-height: 1.2;">
                        <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                    </div>
                </div>
                <div style="text-align: right; width: 40%;">
                    <div style="font-size: 28px; font-weight: bold; letter-spacing: 2px;">INVOICE</div>
                    <div style="font-size: 13px; margin-top: 5px;">No. 162{inv['Case No'].replace('ET', '')}<br>{inv['Lab Done'].strftime('%-m/%-d/%Y')}</div>
                    <div style="margin-top: 20px; text-align: left; font-size: 13px; line-height: 1.3;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}<br>{inv['Phone']}
                    </div>
                </div>
            </div>

            <div style="margin-top: 40px; font-size: 15px; border-bottom: 1.5px solid black; padding-bottom: 10px;">
                <b>Patient:</b> {str(inv['Patient']).upper()}
            </div>

            <div style="margin-top: 15px;">
                <table style="width: 100%; border-collapse: collapse; font-size: 14px;">
                    <tr style="border-bottom: 1px solid black; font-weight: bold;">
                        <td style="padding: 10px 0; text-decoration: underline;">Description</td>
                        <td style="padding: 10px 0; text-align: right; text-decoration: underline;">Amount</td>
                    </tr>
                    <tr>
                        <td style="padding: 15px 0; height: 350px; vertical-align: top;">
                            Nightguard ({inv['Material']}) {inv['Arch'].upper()}
                        </td>
                        <td style="padding: 15px 0; text-align: right; vertical-align: top;">$180.00</td>
                    </tr>
                </table>
            </div>

            <div style="border-top: 1.5px solid black; padding-top: 10px; display: flex; justify-content: space-between; font-weight: bold; font-size: 15px;">
                <span>{inv['Case No']}</span>
                <span>Total: $180.00</span>
            </div>

            <div style="position: absolute; bottom: 40px; left: 30px; right: 30px; text-align: center;">
                <div style="font-size: 16px; font-weight: bold; text-decoration: underline; margin-bottom: 15px;">
                    All dental products we offer are custom made in Canada.
                </div>
                <div style="font-size: 11px; line-height: 1.6; padding: 0 20px; font-weight: 500;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ 인쇄 (Print Invoice)"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("Search...")
