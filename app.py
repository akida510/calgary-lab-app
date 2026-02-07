import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정 및 디자인]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

now = datetime.now()
current_month = now.strftime('%m월')
PRE_TAX_UNIT = 30.0
POST_TAX_UNIT = 19.505333

# CSS 스타일 (인보이스 외곽 박스 및 상하단 밀착 레이아웃)
st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    
    .slim-dashboard {
        background: #1e212b; padding: 10px 20px; border-radius: 12px;
        border: 1px solid #3d414d; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 20px;
    }
    .stat-label { color: #94a3b8; font-size: 0.8rem; }
    .stat-value { color: #ffffff; font-size: 1.1rem; font-weight: 700; }
    .money-text { color: #4ade80; font-weight: 600; font-size: 0.9rem; }

    .invoice-overlay { 
        background-color: rgba(0,0,0,0.9); padding: 20px; 
        display: flex; justify-content: center;
    }
    .invoice-paper {
        background-color: #ffffff !important; 
        width: 100%; max-width: 750px; 
        min-height: 980px;
        padding: 40px; 
        border: 2px solid #000; 
        margin: 0 auto;
        display: flex; 
        flex-direction: column; 
        color: #000 !important;
        box-sizing: border-box;
    }
    .invoice-paper * { 
        color: #000000 !important; -webkit-text-fill-color: #000000 !important; 
        font-family: 'Helvetica', 'Arial', sans-serif !important; 
    }
    
    .invoice-header { width: 100%; flex-shrink: 0; }
    .invoice-body { 
        flex: 1; 
        width: 100%; 
        margin-top: 40px; 
    }
    .invoice-footer { 
        width: 100%; 
        flex-shrink: 0; 
        margin-top: auto; 
    }
    
    .notice-box { 
        border: 1px solid black; padding: 10px; text-align: center; 
        font-size: 10px; line-height: 1.3; margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 초기화]
if 'db' not in st.session_state: st.session_state.db = []
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084
if 'active_invoice' not in st.session_state: st.session_state.active_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806"},
    {"Clinic": "Calgary Central Dental", "Doctor": "Dr. Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600"}
])

# [3. 상단 대시보드]
total_count = len(st.session_state.db)
st.markdown(f'''
    <div class="slim-dashboard">
        <div style="display:flex; gap:15px;">
            <span class="stat-label">{current_month} 실적 <b class="stat-value">{total_count}/320</b></span>
        </div>
        <div class="money-text">AFTER-TAX: ${total_count*POST_TAX_UNIT:,.2f}</div>
    </div>
''', unsafe_allow_html=True)

# [4. 탭 구성]
tab1, tab2 = st.tabs(["📝 등록", "📊 리스트"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No")
        patient = st.text_input("Patient")
        cln = st.selectbox("Clinic", ["선택"] + sorted(ref_data["Clinic"].tolist()))
    with c2:
        mat = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arc = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)
        due = st.date_input("Due Date", date.today() + timedelta(days=7))

    if st.button("💾 저장 및 등록"):
        if cln != "선택" and case_no:
            info = ref_data[ref_data["Clinic"] == cln].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, 
                "Clinic": cln, "Doctor": info["Doctor"], "Address": info["Address"], 
                "Phone": info["Phone"], "Material": mat, "Arch": arc, 
                "Date": date.today().strftime('%m/%d/%Y') # 날짜 저장 추가
            })
            st.session_state.inv_counter += 1
            st.rerun()

with tab2:
    for i, row in enumerate(st.session_state.db):
        col_l, col_r = st.columns([4, 1])
        col_l.write(f"**{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
        if col_r.button("🔍 Invoice", key=f"v_{i}"): st.session_state.active_invoice = row

    if st.session_state.active_invoice:
        st.markdown('---')
        if st.button("❌ Close Preview"):
            st.session_state.active_invoice = None
            st.rerun()
        
        inv = st.session_state.active_invoice
        
        # 에러 방지: 데이터에 Date가 없으면 오늘 날짜 표시
        inv_date = inv.get('Date', date.today().strftime('%m/%d/%Y'))
        
        st.markdown(f"""
        <div class="invoice-overlay">
            <div class="invoice-paper">
                <div class="invoice-header">
                    <div style="display: flex; justify-content: space-between;">
                        <div>
                            <p style="font-size:9px; font-weight:bold; margin:0;">DENTAL TECHNOLOGY LTD</p>
                            <h1 style="font-size: 42px; font-weight: 900; font-style: italic; color: #1a4e8a; margin:0;">skycad</h1>
                            <p style="font-size:11px; margin-top:5px;">Skycad AB | (403) 970-0600<br>205-7136 11 St NE, Calgary, AB</p>
                        </div>
                        <div style="text-align: right;">
                            <h1 style="font-size:30px; font-weight:400; margin:0;">INVOICE</h1>
                            <p style="margin:5px 0; font-size:12px;">No. {inv['Inv_No']} | {inv_date}</p>
                            <div style="text-align:left; font-size:11px; border-top:1px solid #000; padding-top:5px; margin-top:10px;">
                                <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv.get('Address', '')}
                            </div>
                        </div>
                    </div>
                    <div style="margin-top: 20px; padding: 10px 0; border-top: 1.5px solid black; border-bottom: 1.5px solid black; font-size: 15px; font-weight: bold;">
                        Patient: &nbsp; {inv['Patient'].upper()}
                    </div>
                </div>
                <div class="invoice-body">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead>
                            <tr>
                                <th style="text-align:left; border-bottom: 1px solid black; padding-bottom: 5px; font-size:12px;">Description</th>
                                <th style="text-align:right; border-bottom: 1px solid black; padding-bottom: 5px; font-size:12px;">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td style="padding:40px 0; font-size: 14px;">Nightguard ({inv['Material']}) {inv['Arch']}</td>
                                <td style="text-align:right; font-size: 14px;">$180.00</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <div class="invoice-footer">
                    <div style="display:flex; justify-content:space-between; font-size:14px; border-top:1px solid #ddd; padding-top:10px; margin-bottom:10px;">
                        <div style="color:#666;">Case: {inv['Case No']}</div>
                        <div style="font-weight:bold;">Total: $180.00</div>
                    </div>
                    <div class="notice-box">
                        <b>All dental products are custom made in Canada.</b><br>
                        Payment is due within 30 days. Overdue balances are subject to 1.5% monthly finance charge (19.552% APR). Thank you.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
