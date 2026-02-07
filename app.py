import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 제목 스타일 키우기 */
    .main-title {
        font-size: 42px !important; font-weight: 900 !important; color: #4c6ef5 !important;
        margin-bottom: 5px; letter-spacing: -1px;
    }
    .sub-title { font-size: 14px; color: #888; margin-bottom: 30px; }

    /* 입력창 스타일 */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #30363d !important; border-radius: 8px !important;
    }

    /* 버튼 스타일 세련되게 (작고 슬림하게) */
    .stButton>button {
        width: auto !important; min-width: 120px; padding: 5px 20px !important;
        height: 45px !important; background-color: #3b5bdb !important;
        border-radius: 8px !important; border: none !important; font-weight: 600 !important;
    }
    div[data-testid="column"] .stButton>button { width: 100% !important; } /* 리스트 내 버튼만 꽉 차게 */
    
    /* 리스트 카드 스타일 */
    .case-card {
        background-color: #1a1c24; padding: 15px; border-radius: 10px;
        border: 1px solid #30363d; margin-bottom: 10px;
    }

    /* 인보이스 컨테이너 */
    .invoice-paper {
        background-color: white !important; color: black !important;
        padding: 50px; border-radius: 5px; font-family: 'Arial', sans-serif;
        width: 100%; max-width: 850px; margin: 0 auto;
    }
    .invoice-paper * { color: black !important; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider, .no-print { 
            display: none !important; 
        }
        .invoice-paper { display: block !important; border: none !important; padding: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [데이터 및 로직]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'view_invoice' not in st.session_state: st.session_state.view_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])

def get_business_day(start_date, days_to_subtract):
    current_date = start_date
    while days_to_subtract > 0:
        current_date -= timedelta(days=1)
        if current_date.weekday() < 5: days_to_subtract -= 1
    return current_date

# 헤더 섹션
st.markdown('<div class="main-title">🦷 Skycad Lab Night Guard</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Designed by Heechul Jung V1.0.3</div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 작업 리스트", "🔍 검색"])

# --- Tab 1: 등록 ---
with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
    with c2:
        filtered_docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []
        sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + filtered_docs)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    today = date.today()
    with col5: due_date = st.date_input("Due Date", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("Lab Done", today + timedelta(days=1))
    with col4:
        ship_date = get_business_day(due_date, 1 if (sel_clinic != "선택" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2)
        st.date_input("Shipping Date", ship_date)

    if st.button("💾 케이스 저장"):
        if sel_clinic == "선택" or not case_no: st.error("필수 정보를 입력하세요.")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Due": due_date, "Lab Done": lab_done_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City']
            })
            st.success(f"✅ {case_no}번 저장 완료!")

# --- Tab 2: 리스트 및 인보이스 ---
with tab2:
    if not st.session_state.view_invoice:
        for i, row in enumerate(st.session_state.db):
            with st.container():
                st.markdown(f"""<div class="case-card">
                    <b>{row['Case No']}</b> | {row['Patient']} | {row['Clinic']} | <span style="color:{'#fcc419' if row['Status']=='Pending' else '#40c057'}">{row['Status']}</span>
                </div>""", unsafe_allow_html=True)
                
                bc1, bc2 = st.columns([1, 1])
                with bc1:
                    if st.button(f"📄 {'인보이스 보기' if row['Status']=='Pending' else '인보이스 재출력'}", key=f"vi_{i}"):
                        st.session_state.db[i]['Status'] = "Completed"
                        st.session_state.view_invoice = st.session_state.db[i]
                        st.rerun()
                with bc2:
                    if row['Status'] == "Completed":
                        if st.button(f"🔄 완료 취소", key=f"undo_{i}"):
                            st.session_state.db[i]['Status'] = "Pending"
                            st.rerun()
    
    # --- 인보이스 미리보기 모드 ---
    else:
        inv = st.session_state.view_invoice
        cc1, cc2 = st.columns([1, 5])
        with cc1:
            if st.button("⬅️ 닫기"):
                st.session_state.view_invoice = None
                st.rerun()
        with cc2:
            st.info("미리보기 상태입니다. 하단의 인쇄 버튼을 눌러 출력하세요.")

        st.markdown(f"""
        <div class="invoice-paper">
            <table style="width:100%; border:none;">
                <tr>
                    <td style="vertical-align:top; width:60%;">
                        <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:60px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-3px; line-height:1;">skycad</span><br>
                        <div style="margin-top:15px; font-size:13px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </td>
                    <td style="vertical-align:top; text-align:right; width:40%;">
                        <h1 style="font-size:45px; margin:0; font-weight:400; letter-spacing:5px;">INVOICE</h1>
                        <p style="font-size:15px; margin-top:5px;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</p>
                        <div style="text-align:left; border:1px solid #000; padding:15px; width:220px; float:right; margin-top:10px; font-size:13px;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </td>
                </tr>
            </table>

            <div style="margin: 40px 0 15px 0; font-size:20px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>

            <table style="width:100%; border-collapse:collapse; border-top:2.5px solid black; border-bottom:2.5px solid black;">
                <thead>
                    <tr style="border-bottom:1.5px solid black;">
                        <th style="padding:15px 5px; text-align:left; font-size:16px;">Description</th>
                        <th style="padding:15px 5px; text-align:right; font-size:16px; width:120px;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding:30px 5px; vertical-align:top; font-size:17px;">
                            Nightguard ({inv['Material']}) - {inv['Arch']}
                            <div style="height:400px; width:100%;"></div>
                        </td>
                        <td style="padding:30px 5px; vertical-align:top; text-align:right; font-size:17px;">$180.00</td>
                    </tr>
                </tbody>
            </table>

            <table style="width:100%; margin-bottom:50px;">
                <tr>
                    <td style="padding:15px 5px; font-weight:bold; font-size:20px;">{inv['Case No']}</td>
                    <td style="padding:15px 5px; font-weight:bold; font-size:20px; text-align:right;">Total: $180.00</td>
                </tr>
            </table>

            <div style="text-align:center; margin-top:20px;">
                <div style="font-size:18px; font-weight:bold; text-decoration:underline; margin-bottom:20px;">All dental products we offer are custom made in Canada.</div>
                <p style="font-size:12px; line-height:1.7; padding:0 50px;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.</p>
            </div>
            
            <div style="margin-top:60px; border-top:1px solid black; width:220px; padding-top:10px; font-size:13px;">Authorized Signature</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ 인보이스 인쇄"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("🔍 검색 기능 준비 중")
