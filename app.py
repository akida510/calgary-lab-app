import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 디자인 설정 및 테마 강제 고정]
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 배경 및 글자색 강제 고정 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 입력창 및 선택창 스타일 */
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
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; 
    }
    
    /* [인보이스 디자인 - 레터지 비율 및 박스] */
    .inv-outer-container {
        display: flex; justify-content: center; padding: 20px 0; background-color: #333;
    }
    .invoice-letter {
        background-color: white !important; color: black !important;
        width: 8.5in; min-height: 11in; padding: 0.5in;
        border: 2px solid black; box-sizing: border-box;
        font-family: 'Arial', sans-serif; position: relative;
    }
    .invoice-letter * { color: black !important; line-height: 1.2; }
    
    .notice-box {
        border: 1.5px solid black; padding: 10px; margin-top: 20px;
        font-size: 11px; text-align: left;
    }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .inv-outer-container { padding: 0; background: white; }
        .invoice-letter { border: none; width: 100%; padding: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 관리]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084

# 원본 데이터 유지
ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Address": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# [3. 메인 화면]
st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Heechul Jung Edition</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

# --- Tab 1: 케이스 등록 (보내주신 원본 로직 유지) ---
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
                "Inv_No": st.session_state.inv_counter,
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Received": rec_date, "Due": due_date, "Lab Done": lab_done_date, "Status": "Pending",
                "Address": c_info.get("Address", ""), "City": c_info.get("City", ""), "Phone": c_info.get("Phone", ""),
                "Inv_Date": today.strftime('%m/%d/%Y')
            }
            st.session_state.db.append(new_case)
            st.session_state.inv_counter += 1
            st.success(f"{case_no}번 케이스 등록 완료!")

# --- Tab 2: 리스트 및 인보이스 (사진 디자인 적용) ---
with tab2:
    st.subheader("📊 작업 진행 리스트")
    if not st.session_state.db:
        st.info("현재 대기 중인 케이스가 없습니다.")
    else:
        for i, row in enumerate(st.session_state.db):
            c_info, c_btn = st.columns([4, 1])
            with c_info:
                st.markdown(f"**{'🟡' if row['Status']=='Pending' else '🟢'} {row['Case No']}** | {row['Patient']} | {row['Clinic']} | Due: {row['Due']}")
            with c_btn:
                if row['Status'] == "Pending":
                    if st.button(f"완료 및 인보이스", key=f"comp_{i}"):
                        st.session_state.db[i]['Status'] = "Completed"
                        st.session_state.selected_invoice = st.session_state.db[i]
                        st.rerun()
                else:
                    if st.button(f"인보이스 재출력", key=f"re_{i}"):
                        st.session_state.selected_invoice = st.session_state.db[i]
                        st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        if st.button("❌ 닫기"):
            st.session_state.selected_invoice = None
            st.rerun()

        # [사진 기준 인보이스 재현]
        st.markdown(f"""
        <div class="inv-outer-container">
            <div class="invoice-letter">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <div>
                        <div style="line-height:1;">
                            <span style="font-size:8px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                            <span style="font-size:38px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px;">skycad</span>
                        </div>
                        <div style="font-size:11px; margin-top:15px; line-height:1.4;">
                            <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                        </div>
                    </div>
                    <div style="text-align: right; line-height:1.2;">
                        <h1 style="font-size:32px; font-weight:400; margin:0; letter-spacing:1px;">INVOICE</h1>
                        <p style="font-size:12px; margin:8px 0;">No. {inv['Inv_No']}<br>{inv['Inv_Date']}</p>
                        <div style="text-align:left; font-size:11px; margin-top:20px; line-height:1.4;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['City']}
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 45px; padding: 12px 0; border-top: 1.5px solid black; border-bottom: 1.5px solid black; font-size: 14px;">
                    <b>Patient:</b> {str(inv['Patient']).upper()}
                </div>
                
                <div style="height: 400px; margin-top: 30px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid black;">
                                <th style="text-align:left; padding-bottom: 8px; font-size:12px; text-decoration:underline;">Description</th>
                                <th style="text-align:right; padding-bottom: 8px; font-size:12px; text-decoration:underline;">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding:25px 0; font-size: 14px;">Nightguard ({inv['Material']}) {inv['Arch']}</td>
                                <td style="text-align:right; font-size: 14px; font-weight:bold;">$180.00</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                
                <div style="border-top: 1.5px solid black; padding-top: 15px;">
                    <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:bold;">
                        <div>{inv['Case No']}</div>
                        <div style="font-size:15px;">Total: $180.00</div>
                    </div>
                    <div class="notice-box">
                        <u style="font-weight:bold; font-size:13px;">All dental products we offer are custom made in Canada.</u><br><br>
                        Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🖨️ 인쇄하기"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3:
    st.write("🔍 검색 기능")
