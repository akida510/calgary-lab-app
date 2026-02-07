import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [디자인 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* 전체 테마: 희철님 원본 스타일 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    label p, .stMarkdown p, .stMetric p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }
    
    /* 등록창 버튼: 원본 스타일 (크고 듬직하게) */
    .big-save-btn button {
        width: 100%; height: 3.5em !important; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px;
    }

    /* 리스트 완료 버튼: 세련된 슬림 스타일 (폰트 10px로 축소) */
    .slim-btn button {
        height: 24px !important;
        min-height: 24px !important;
        font-size: 10px !important;
        padding: 0 8px !important;
        background-color: #2b3a67 !important;
        color: #dbe4ff !important;
        border: 1px solid #4c6ef5 !important;
        line-height: 1 !important;
    }

    /* 인보이스 컨테이너: 종이 느낌 그대로 */
    .invoice-box {
        background-color: white !important; color: black !important;
        padding: 40px; border-radius: 0px; font-family: Arial, sans-serif;
        width: 100%; min-height: 1000px;
    }
    .invoice-box * { color: black !important; border-color: black !important; }

    @media print {
        .stButton, .stTabs, [data-testid="stSidebar"], .header-container { display: none !important; }
        .invoice-box { display: block !important; padding: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# 데이터 관리
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

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

    due_date = st.date_input("요청일 (Due Date)", today + timedelta(days=7))
    
    st.markdown('<div class="big-save-btn">', unsafe_allow_html=True)
    if st.button("💾 케이스 저장 (접수 완료)"):
        if sel_clinic != "선택" and case_no:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Arch": arch, "Lab Done": date.today(), "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City']
            })
            st.success("저장되었습니다!")
    st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn1, c_btn2 = st.columns([4, 1, 1])
        with c_info: st.write(f"**{row['Case No']}** | {row['Patient']} | {row['Clinic']}")
        with c_btn1:
            st.markdown('<div class="slim-btn">', unsafe_allow_html=True)
            if st.button("완료/출력", key=f"inv_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
        with c_btn2:
            if row['Status'] == "Completed":
                st.markdown('<div class="slim-btn">', unsafe_allow_html=True)
                if st.button("취소", key=f"un_{i}"):
                    st.session_state.db[i]['Status'] = "Pending"
                    st.session_state.selected_invoice = None
                    st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # [핵심] 인보이스 HTML 구조를 깔끔하게 출력
        st.markdown(f"""
        <div class="invoice-box">
            <table style="width:100%; border:none;">
                <tr>
                    <td style="width:60%;">
                        <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:60px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-4px; line-height:0.8;">skycad</span><br>
                        <div style="margin-top:15px; font-size:12px; line-height:1.2;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </td>
                    <td style="text-align:right; vertical-align:top;">
                        <h1 style="font-size:50px; margin:0; font-weight:400; letter-spacing:8px;">INVOICE</h1>
                        <p style="font-size:15px; margin:5px 0;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</p>
                        <div style="text-align:left; border:1px solid black; padding:12px; width:200px; float:right; margin-top:10px; font-size:12px;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                        </div>
                    </td>
                </tr>
            </table>

            <div style="margin: 40px 0 15px 0; font-size:20px;"><b>Patient:</b> {str(inv['Patient']).upper()}</div>

            <table style="width:100%; border-top:2px solid black; border-bottom:2px solid black; border-collapse:collapse; margin-bottom:20px;">
                <tr style="border-bottom:1px solid black; font-weight:bold; font-size:16px;">
                    <td style="padding:10px 5px;">Description</td>
                    <td style="padding:10px 5px; text-align:right;">Amount</td>
                </tr>
                <tr>
                    <td style="padding:20px 5px; height:400px; vertical-align:top; font-size:16px;">
                        Nightguard ({inv['Material']}) - {inv['Arch']}
                    </td>
                    <td style="padding:20px 5px; text-align:right; vertical-align:top; font-size:16px;">$180.00</td>
                </tr>
            </table>

            <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:18px; margin-bottom:50px;">
                <span>{inv['Case No']}</span><span>Total: $180.00</span>
            </div>

            <div style="text-align:center; margin-top:20px;">
                <div style="font-size:18px; font-weight:bold; text-decoration:underline; margin-bottom:15px;">All dental products we offer are custom made in Canada.</div>
                <p style="font-size:11px; line-height:1.6; padding:0 30px; color:#000 !important;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.</p>
            </div>
            
            <div style="margin-top:60px; border-top:1px solid black; width:220px; padding-top:10px; font-size:13px; text-align:left;">Authorized Signature</div>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("🖨️ 인쇄 (Print)"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("Search...")
