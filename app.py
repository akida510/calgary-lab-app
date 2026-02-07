import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 레터 용지 비율 컨테이너 */
    .invoice-wrapper { display: flex; justify-content: center; padding: 20px; background-color: #262730; }
    
    /* 인보이스 종이 설정 */
    .invoice-paper {
        background-color: #ffffff !important;
        width: 100%; max-width: 800px; 
        aspect-ratio: 8.5 / 11; padding: 60px 50px; border: 1px solid #000;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; box-sizing: border-box;
    }
    
    /* 모든 텍스트 검정색 강제 고정 */
    .invoice-paper, .invoice-paper div, .invoice-paper p, .invoice-paper span, 
    .invoice-paper b, .invoice-paper u, .invoice-paper h1, .invoice-paper table, 
    .invoice-paper td, .invoice-paper th {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        font-family: 'Arial', sans-serif;
    }
    
    /* [수정 포인트] 상단 헤더 레이아웃: 로고와 INVOICE 높이 정렬 및 중앙 여백 확보 */
    .inv-header { 
        display: flex; 
        justify-content: space-between; 
        align-items: flex-start; /* 상단 라인 맞춤 */
        margin-bottom: 50px; 
    }
    
    .logo-section { flex: 1; }
    .invoice-title-section { flex: 1; text-align: right; }
    
    .logo-main { 
        font-size: 58px; font-weight: 900; font-style: italic; 
        color: #1a4e8a !important; -webkit-text-fill-color: #1a4e8a !important;
        letter-spacing: -3px; line-height: 0.8; margin-bottom: 10px;
    }
    
    .inv-title { 
        font-size: 42px; font-weight: 500; line-height: 0.8; 
        margin-bottom: 15px; letter-spacing: 2px;
    }

    .patient-line { 
        margin: 25px 0; padding: 15px 0; border-top: 2.5px solid black; border-bottom: 2.5px solid black; 
        font-size: 20px; font-weight: bold; 
    }
    
    .item-table { width: 100%; border-collapse: collapse; flex-grow: 1; }
    .item-table th { border-bottom: 1.5px solid black; text-align: left; padding: 10px 0; font-size: 16px; }
    .item-table td { padding: 20px 0; vertical-align: top; font-size: 17px; }
    
    .bottom-box { margin-top: auto; }
    .notice-box { border: 1.5px solid black; padding: 20px; text-align: center; margin-top: 15px; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown { display: none !important; }
        .invoice-wrapper { padding: 0; background: none; }
        .invoice-paper { border: none; box-shadow: none; width: 100%; max-width: none; aspect-ratio: auto; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [로직 영역]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806", "Region": "Courier"},
    {"Clinic": "Calgary Central Dental", "Doctor": "Dr. Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"}
])

# ---------------------------------------------------------
# [UI 및 등록 화면]
# ---------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트/완료", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No", placeholder="IT30")
        patient = st.text_input("Patient")
        cln_list = ["선택"] + sorted(ref_data["Clinic"].tolist())
        doc_list = ["선택"] + sorted(ref_data["Doctor"].tolist())

        def sync_cln():
            if st.session_state.c_key != "선택":
                st.session_state.d_key = ref_data[ref_data["Clinic"] == st.session_state.c_key]["Doctor"].iloc[0]
        def sync_doc():
            if st.session_state.d_key != "선택":
                st.session_state.c_key = ref_data[ref_data["Doctor"] == st.session_state.d_key]["Clinic"].iloc[0]

        st.selectbox("Clinic", cln_list, key="c_key", on_change=sync_cln)
        st.selectbox("Doctor", doc_list, key="d_key", on_change=sync_doc)

    with c2:
        st.checkbox("3D Model", value=True)
        st.date_input("접수일", date.today())
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    if st.button("💾 케이스 저장"):
        if st.session_state.c_key != "선택" and case_no:
            info = ref_data[ref_data["Clinic"] == st.session_state.c_key].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": st.session_state.c_key,
                "Doctor": st.session_state.d_key, "Address": info["Address"], "Phone": info["Phone"],
                "Material": material, "Arch": arch, "Status": "진행중"
            })
            st.success("저장되었습니다.")

with tab2:
    for i, row in enumerate(st.session_state.db):
        cols = st.columns([3, 1, 1])
        cols[0].write(f"{'🟡' if row['Status']=='진행중' else '🟢'} {row['Case No']} | {row['Patient']}")
        if cols[1].button("완료/복구", key=f"s_{i}"):
            st.session_state.db[i]['Status'] = "완료" if row['Status']=='진행중' else '진행중'
            st.rerun()
        if cols[2].button("인보이스", key=f"i_{i}"):
            st.session_state.selected_invoice = row

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.markdown('<div class="invoice-wrapper">', unsafe_allow_html=True)
        invoice_html = f"""
        <div class="invoice-paper">
            <div class="inv-header">
                <div class="logo-section">
                    <p style="font-size:10px; font-weight:bold; margin-bottom:5px;">DENTAL TECHNOLOGY LTD</p>
                    <h1 class="logo-main">skycad</h1>
                    <p style="font-size:14px; line-height:1.3;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
                </div>
                <div class="invoice-title-section">
                    <h1 class="inv-title">INVOICE</h1>
                    <p style="font-size:16px; margin-bottom:5px;">No. 162084</p>
                    <p style="font-size:16px; margin-bottom:25px;">{date.today().strftime('%-m/%-d/%Y')}</p>
                    <div style="text-align:left; display:inline-block; font-size:14px; line-height:1.4;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}
                    </div>
                </div>
            </div>
            
            <div class="patient-line">Patient: &nbsp; {inv['Patient'].upper()}</div>
            
            <table class="item-table">
                <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
                <tbody><tr><td style="padding:25px 0;">Nightguard ({inv['Material']}) {inv['Arch']}</td><td style="text-align:right;">$180.00</td></tr></tbody>
            </table>
            
            <div class="bottom-box">
                <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:20px; margin-bottom:15px; border-top:1px solid #eee; padding-top:10px;">
                    <div>{inv['Case No']}</div><div>Total: $180.00</div>
                </div>
                <div class="notice-box">
                    <u style="font-weight:bold; display:block; margin-bottom:10px; font-size:15px;">All dental products we offer are custom made in Canada.</u>
                    <p style="font-size:11.5px; line-height:1.5;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
