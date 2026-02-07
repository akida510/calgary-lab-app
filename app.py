import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 디자인 및 테마 설정]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 인보이스 전용: 사진 디자인 그대로 재현 */
    .inv-container {
        background-color: #555; padding: 40px 0; display: flex; justify-content: center;
    }
    .inv-paper {
        background-color: white !important; color: black !important;
        width: 8.5in; min-height: 11in; padding: 0.75in;
        border: 1px solid #000; box-sizing: border-box;
        font-family: 'Arial', sans-serif; position: relative;
    }
    .inv-paper * { color: black !important; line-height: 1.2; }
    
    /* 하단 안내 문구 박스 */
    .notice-box {
        border: 1.5px solid black; padding: 12px; margin-top: 20px;
        font-size: 11px; text-align: left;
    }
    
    @media print {
        body { background: white; }
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"] { display: none !important; }
        .inv-container { padding: 0; background: white; }
        .inv-paper { border: none; width: 100%; padding: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 로직]
if 'db' not in st.session_state: st.session_state.db = []
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084
if 'active_inv' not in st.session_state: st.session_state.active_inv = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Arshpreet Kaur", "Address": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
    {"Clinic": "Calgary Central Dental", "Doctor": "Dr. Lana Huynh", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"}
])

# [3. 메인 화면 구성]
st.title("🦷 Skycad Lab Manager")

tab1, tab2 = st.tabs(["📝 등록", "📊 리스트 및 인보이스"])

with tab1:
    st.session_state.active_inv = None
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No")
        patient = st.text_input("Patient")
        cln_list = sorted(ref_data['Clinic'].tolist())
        sel_cln = st.selectbox("Clinic", ["선택"] + ["직접 입력"] + cln_list)
        final_cln = st.text_input("병원명 입력") if sel_cln == "직접 입력" else (sel_cln if sel_cln != "선택" else "")
    with c2:
        mat = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arc = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)
        inv_date = st.date_input("Invoice Date", date.today())
        
        # 일정 관리 복구
        col_sub1, col_sub2 = st.columns(2)
        with col_sub1:
            rec_date = st.date_input("접수일", date.today())
            req_date = st.date_input("요청일", date.today() + timedelta(days=7))
        with col_sub2:
            com_date = st.date_input("완료일", date.today() + timedelta(days=6))
            ship_date = st.date_input("출고일", date.today() + timedelta(days=7))

    if st.button("💾 저장 및 초기화", use_container_width=True):
        if case_no and final_cln:
            c_info = ref_data[ref_data['Clinic'] == final_cln].iloc[0] if final_cln in ref_data['Clinic'].values else {}
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient,
                "Clinic": final_cln, "Doctor": c_info.get("Doctor", ""), 
                "Address": c_info.get("Address", ""), "City": c_info.get("City", ""), "Phone": c_info.get("Phone", ""),
                "Material": mat, "Arch": arc, "Date": inv_date.strftime('%m/%d/%Y')
            })
            st.session_state.inv_counter += 1
            st.rerun()

with tab2:
    for i, row in enumerate(st.session_state.db):
        col_txt, col_btn = st.columns([5,1])
        with col_txt: st.write(f"No. {row['Inv_No']} | {row['Patient']} ({row['Clinic']})")
        with col_btn:
            if st.button("🔍 인보이스", key=f"btn_{i}"): st.session_state.active_inv = row

    if st.session_state.active_inv:
        inv = st.session_state.active_inv
        st.markdown("---")
        if st.button("❌ 닫기"): 
            st.session_state.active_inv = None
            st.rerun()
            
        # 사진과 동일한 디자인 구현
        st.markdown(f"""
        <div class="inv-container">
            <div class="inv-paper">
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
                        <p style="font-size:12px; margin:8px 0;">No. {inv['Inv_No']}<br>{inv['Date']}</p>
                        <div style="text-align:left; font-size:11px; margin-top:20px; line-height:1.4;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Address']}<br>{inv['City']}
                        </div>
                    </div>
                </div>
                
                <div style="margin-top: 45px; padding: 12px 0; border-top: 1.5px solid #000; border-bottom: 1.5px solid #000; font-size: 14px;">
                    <b>Patient:</b> {str(inv['Patient']).upper()}
                </div>
                
                <div style="height: 400px; margin-top: 30px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr style="border-bottom: 1px solid #000;">
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
                
                <div style="border-top: 1.5px solid #000; padding-top: 15px;">
                    <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:bold;">
                        <div>ET12</div>
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
        
        if st.button("🖨️ 인쇄 (Print PDF)"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
