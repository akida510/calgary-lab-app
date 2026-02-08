import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [수정 금지] 디자인 설정 및 테마 강제 고정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    input:disabled { background-color: #262730 !important; color: #aaaaaa !important; }
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }
    
    /* 헤더 스타일 */
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    
    /* 리스트 카드 스타일 */
    .case-card {
        background-color: #1a1c24;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 10px;
        border-left: 5px solid #4c6ef5;
    }

    /* [핵심] 인보이스 종이 비율 고정 및 모바일 축소 로직 */
    .invoice-wrapper {
        width: 100%;
        display: flex;
        justify-content: center;
        background-color: #333; /* 배경을 어둡게 해서 종이가 돋보이게 함 */
        padding: 40px 0;
        overflow: hidden;
    }

    .invoice-paper {
        background-color: white !important;
        color: black !important;
        width: 850px !important;  /* 레터지 가로 고정 */
        height: 1100px !important; /* 레터지 세로 고정 */
        padding: 50px !important;
        box-sizing: border-box !important;
        position: relative !important;
        display: block !important; /* 모바일에서 깨지지 않게 block 고정 */
        box-shadow: 0 0 30px rgba(0,0,0,0.5);
    }

    /* 모바일에서 억지로 축소해서 보여주기 */
    @media screen and (max-width: 850px) {
        .invoice-wrapper { padding: 10px 0; background-color: transparent; }
        .invoice-paper {
            transform: scale(calc(min(100vw, 850px) / 880)); /* 화면 너비에 맞게 전체 비율 축소 */
            transform-origin: top center;
            margin-bottom: calc(-1100px * (1 - (min(100vw, 850px) / 880)));
        }
    }

    .invoice-paper * { color: black !important; border-color: black !important; }

    @media print {
        @page { size: letter; margin: 0; }
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-wrapper { background-color: white; padding: 0; }
        .invoice-paper { transform: none !important; box-shadow: none !important; margin: 0 !important; width: 100% !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 및 로직] (기존 동일)
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
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
st.markdown(f'<div class="header-container"><div style="font-size: 24px; font-weight: 800;">實 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Designed By Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)", placeholder="환자 성함")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
        docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = today if is_3d else st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)
    
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("완료일 (Lab Done)", today + timedelta(days=1))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장"):
        if sel_clinic == "선택" or not case_no: st.error("Case No와 병원명은 필수입니다.")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Arch": arch, "Lab Done": lab_done_date, "Due": due_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success("등록 완료!")

with tab2:
    if not st.session_state.db: st.info("케이스가 없습니다.")
    else:
        for i, row in enumerate(st.session_state.db):
            c_info, c_btn = st.columns([4, 1.5])
            with c_info:
                color = "#f1c40f" if row['Status'] == "Pending" else "#2ecc71"
                st.markdown(f"""
                <div style="background-color:#1a1c24; padding:12px; border-radius:8px; border-left: 5px solid {color}; margin-bottom:10px;">
                    <b style="font-size:16px;">{row['Case No']} | {row['Patient']}</b><br>
                    <span style="font-size:13px; color:#aaa;">{row['Clinic']} | {row['Material']} | Due: {row['Due']}</span>
                </div>
                """, unsafe_allow_html=True)
            with c_btn:
                if st.button("완료/출력", key=f"btn_{i}"):
                    st.session_state.db[i]['Status'] = "Completed"
                    st.session_state.selected_invoice = st.session_state.db[i]
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.markdown(f"""
        <div class="invoice-wrapper">
            <div class="invoice-paper">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <div style="font-size: 11px; font-weight: bold; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                        <div style="font-size: 70px; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 0.8; letter-spacing: -4px;">skycad</div>
                        <div style="margin-top: 20px; font-size: 14px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 40px; font-weight: bold; letter-spacing: 5px;">INVOICE</div>
                        <div style="font-size: 16px; font-weight: bold;">No. 162{inv['Case No'].replace('ET', '')}<br>{inv['Lab Done'].strftime('%m/%d/%Y')}</div>
                        <div style="margin-top: 30px; text-align: left; font-size: 14px; border: 1.5px solid black; padding: 15px; width: 250px; display: inline-block;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}<br>{inv['Phone']}
                        </div>
                    </div>
                </div>
                <div style="margin: 60px 0 10px 0; font-size: 20px; border-bottom: 2.5px solid black; padding-bottom: 5px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
                <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                    <tr style="border-bottom: 2px solid black; font-weight: bold; font-size: 16px;">
                        <td style="padding: 12px 0; text-decoration: underline;">Description</td>
                        <td style="padding: 12px 0; text-align: right; text-decoration: underline;">Amount</td>
                    </tr>
                    <tr>
                        <td style="padding: 30px 0; height: 400px; vertical-align: top; font-size: 18px;">Nightguard ({inv['Material']}) {inv['Arch'].upper()}</td>
                        <td style="padding: 30px 0; text-align: right; vertical-align: top; font-size: 18px;">$180.00</td>
                    </tr>
                </table>
                <div style="border-top: 2px solid black; padding-top: 15px; display: flex; justify-content: space-between; font-weight: bold; font-size: 22px;">
                    <span>{inv['Case No']}</span><span>Total: $180.00</span>
                </div>
                <div style="position: absolute; bottom: 50px; left: 50px; right: 50px; text-align: center;">
                    <div style="font-size: 16px; font-weight: bold; text-decoration: underline; margin-bottom: 15px;">All dental products we offer are custom made in Canada.</div>
                    <div style="font-size: 10px; line-height: 1.5; color: #444 !important;">
                        Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🖨️ PRINT (PDF)"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("준비 중")
