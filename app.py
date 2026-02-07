import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    label p, .stMarkdown p, p, span { color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    
    /* 인보이스 내부 스타일 (절대 검정 고정) */
    .invoice-paper {
        background-color: white !important; padding: 50px; border: 1px solid #000;
        width: 100%; max-width: 800px; margin: 20px auto;
    }
    .invoice-paper * { color: #000000 !important; }
    
    .stButton>button { width: 100%; height: 3em; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

def get_business_day(start_date, days_to_subtract):
    curr = start_date
    while days_to_subtract > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days_to_subtract -= 1
    return curr

tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: IT30")
        patient = st.text_input("Patient(환자명)")
        # 병원명과 의사명을 자유롭게 적으실 수 있도록 text_input으로 배치 (혹은 선택형 유지 가능)
        clinic_name = st.text_input("Clinic(병원명)")
        doctor_name = st.text_input("Doctor(의사명)")
        
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        # 지시사항: 3D model 밑에 날짜입력창 기본으로 표시
        rec_date = st.date_input("접수일(Received Date)", date.today())
        
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    st.markdown("### 📅 일정 관리")
    col3, col4, col5 = st.columns(3)
    with col5: 
        due_date = st.date_input("요청일 (Due Date)", date.today() + timedelta(days=7))
    with col3: 
        # 완료일 기본값: 오늘 + 1일
        lab_done_date = st.date_input("완료일 (Lab Done)", date.today() + timedelta(days=1))
    with col4:
        # 기본 출고일 계산 (임시로 1일 전 평일)
        ship_date = get_business_day(due_date, 1)
        st.date_input("출고일 (Shipping Date)", ship_date)

    if st.button("💾 케이스 저장 및 등록"):
        if not clinic_name or not case_no:
            st.error("Case No와 병원명은 반드시 입력해야 합니다.")
        else:
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": clinic_name, 
                "Doctor": doctor_name, "Material": material, "Arch": arch, 
                "Lab Done": lab_done_date, "Status": "진행중"
            })
            st.success(f"{case_no}번 케이스가 '진행중'으로 등록되었습니다.")

with tab2:
    st.subheader("📊 작업 상황")
    for i, row in enumerate(st.session_state.db):
        st.markdown(f"---")
        c_status, c_info, c_action = st.columns([1, 3, 2])
        with c_status:
            emoji = "🟡" if row['Status'] == "진행중" else "🟢"
            st.markdown(f"**{emoji} {row['Status']}**")
        with c_info:
            st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_action:
            ca, cb = st.columns(2)
            with ca:
                if row['Status'] == "진행중":
                    if st.button("완료처리", key=f"d_{i}"):
                        st.session_state.db[i]['Status'] = "완료"
                        st.session_state.selected_invoice = st.session_state.db[i]
                        st.rerun()
                else:
                    if st.button("되돌리기", key=f"u_{i}"):
                        st.session_state.db[i]['Status'] = "진행중"
                        st.rerun()
            with cb:
                if st.button("인보이스", key=f"i_{i}"):
                    st.session_state.selected_invoice = row
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        invoice_html = f"""
        <div class="invoice-paper">
            <div style="display: flex; justify-content: space-between; margin-bottom: 40px;">
                <div>
                    <p style="font-size:9px; font-weight:bold;">DENTAL TECHNOLOGY LTD</p>
                    <h1 style="font-size:50px; font-style:italic; color:#1a4e8a !important; font-weight:900;">skycad</h1>
                    <p style="font-size:13px;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                </div>
                <div style="text-align:right;">
                    <h1 style="font-size:35px;">INVOICE</h1>
                    <p>No. 162084</p>
                    <p>{date.today().strftime('%-m/%-d/%Y')}</p>
                    <div style="margin-top:20px; text-align:left; float:right;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>병원 주소 정보 등
                    </div>
                </div>
            </div>
            <div style="margin-top:20px; padding:15px 0; border-top:2px solid black; border-bottom:2px solid black; font-size:18px; font-weight:bold;">
                Patient: &nbsp; {inv['Patient'].upper()}
            </div>
            <table style="width:100%; border-collapse:collapse; margin-top:10px; min-height:200px;">
                <thead><tr><th style="border-bottom:1px solid black; text-align:left;">Description</th><th style="border-bottom:1px solid black; text-align:right;">Amount</th></tr></thead>
                <tbody><tr><td style="padding:20px 0;">Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody>
            </table>
            <div style="margin-top:50px;">
                <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:18px; margin-bottom:30px;">
                    <div>{inv['Case No']}</div><div>Total: $180.00</div>
                </div>
                <div style="border:1.5px solid black; padding:20px; text-align:center;">
                    <u style="font-weight:bold; font-size:16px; display:block; margin-bottom:10px;">All dental products we offer are custom made in Canada.</u>
                    <p style="font-size:12px; line-height:1.4;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
