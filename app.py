import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1] 디자인 설정 (희철님 원본 스타일 테마)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }
    
    /* 등록 버튼 (큰 사이즈) */
    .big-save-btn button {
        width: 100%; height: 3.5em !important; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px;
    }

    /* 리스트 내 완료 버튼 (세련된 슬림 사이즈) */
    .slim-btn button {
        height: 26px !important; min-height: 26px !important;
        font-size: 11px !important; padding: 0 10px !important;
        background-color: #2b3a67 !important; color: #dbe4ff !important;
        border: 1px solid #4c6ef5 !important; line-height: 1 !important;
    }

    /* 인보이스 출력 구역 (흰 배경 고정) */
    .invoice-wrap {
        background-color: white !important; color: black !important;
        padding: 50px; border-radius: 0px; font-family: 'Arial', sans-serif;
        line-height: 1.3;
    }
    .invoice-wrap * { color: black !important; }
    
    @media print {
        .stButton, .stTabs, [data-testid="stSidebar"], .header-container, .stDivider { display: none !important; }
        .invoice-wrap { display: block !important; padding: 0 !important; margin: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2] 데이터 초기화
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])

# [3] 메인 화면 레이아웃
st.markdown('<div class="header-container"><div style="font-size: 24px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 기본정보입력")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No(팬번호)", placeholder="예: ET33")
        patient = st.text_input("Patient(환자명)")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic(병원명)", ["선택"] + clinics)
        sel_doctor = st.selectbox("Doctor(의사명)", ["선택"] + (ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "선택" else []))
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = today if is_3d else st.date_input("접수일", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown('<div class="big-save-btn">', unsafe_allow_html=True)
    if st.button("💾 케이스 저장 (접수 완료)"):
        if sel_clinic != "선택" and case_no:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Arch": arch, "Date": date.today(), "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City']
            })
            st.success("성공적으로 저장되었습니다!")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    for i, row in enumerate(st.session_state.db):
        col_i, col_b1, col_b2 = st.columns([4, 1, 1])
        with col_i: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with col_b1:
            st.markdown('<div class="slim-btn">', unsafe_allow_html=True)
            if st.button("완료/출력", key=f"btn_p_{i}"):
                st.session_state.selected_invoice = row
                st.session_state.db[i]['Status'] = "Completed"
            st.markdown('</div>', unsafe_allow_html=True)
        with col_b2:
            if row['Status'] == "Completed":
                st.markdown('<div class="slim-btn">', unsafe_allow_html=True)
                if st.button("취소", key=f"btn_u_{i}"):
                    st.session_state.db[i]['Status'] = "Pending"
                    st.session_state.selected_invoice = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # [수정] 코드가 밖으로 튀어나오지 않도록 HTML 구조를 문자열 하나로 합쳐서 한 번에 출력
        inv_content = f"""
        <div class="invoice-wrap">
            <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                <div>
                    <div style="font-size: 10px; font-weight: bold;">DENTAL TECHNOLOGY Ltd</div>
                    <div style="font-size: 60px; font-weight: 900; font-style: italic; color: #1a4e8a; line-height: 0.8; letter-spacing: -3px;">skycad</div>
                    <div style="margin-top: 15px; font-size: 13px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 50px; letter-spacing: 5px; margin: 0;">INVOICE</div>
                    <div style="font-size: 16px; margin: 5px 0;">No. {inv['Case No'].replace('ET', '')}<br>{inv['Date'].strftime('%d/%m/%Y')}</div>
                    <div style="border: 1px solid black; padding: 10px; width: 220px; text-align: left; margin-top: 10px; float: right; font-size: 12px;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                    </div>
                </div>
            </div>
            <div style="margin: 60px 0 20px 0; font-size: 22px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>
            <div style="border-top: 2px solid black; border-bottom: 2px solid black;">
                <div style="display: flex; justify-content: space-between; padding: 10px 5px; font-weight: bold; border-bottom: 1px solid black; font-size: 16px;">
                    <span>Description</span><span>Amount</span>
                </div>
                <div style="display: flex; justify-content: space-between; padding: 30px 5px; min-height: 400px; font-size: 17px;">
                    <span>Nightguard ({inv['Material']}) - {inv['Arch']}</span><span>$180.00</span>
                </div>
            </div>
            <div style="display: flex; justify-content: space-between; font-weight: bold; font-size: 20px; margin: 20px 0 80px 0;">
                <span>{inv['Case No']}</span><span>Total: $180.00</span>
            </div>
            <div style="text-align: center; margin-bottom: 60px;">
                <div style="font-size: 18px; font-weight: bold; text-decoration: underline; margin-bottom: 15px;">All dental products we offer are custom made in Canada.</div>
                <div style="font-size: 11px; line-height: 1.6; padding: 0 50px;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </div>
            </div>
            <div style="border-top: 1.5px solid black; width: 220px; padding-top: 10px; font-size: 14px;">Authorized Signature</div>
        </div>
        """
        st.markdown(inv_content, unsafe_allow_html=True)
        if st.button("🖨️ 인쇄하기 (Print)"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("Search...")
