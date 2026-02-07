import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [App Configuration]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* Dark Theme Setup */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* Text Visibility */
    label p, .stMarkdown p, .stMetric p, [data-baseweb="tab"] p, span, div { 
        color: #ffffff !important; font-weight: 500 !important;
    }
    
    /* Input Field Styling */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }

    /* Professional Header */
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 15px 25px; border-radius: 8px;
        margin-bottom: 20px; border: 1px solid #30363d;
    }
    
    /* Main Action Button (Case Entry) */
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; 
    }

    /* List Action Buttons (Slim & Professional) */
    div[data-testid="column"] .stButton>button {
        height: 22px !important; width: auto !important; font-size: 10px !important;
        padding: 0 12px !important; background-color: #2b3a67 !important;
        border: 1px solid #4c6ef5 !important; margin-top: 5px; min-height: 22px !important;
    }

    /* [Invoice Frame] Matches physical paper photo */
    .invoice-card {
        background-color: white !important; padding: 50px 45px; 
        border: 2px solid black !important; font-family: 'Arial', sans-serif;
        min-height: 1000px; position: relative; margin: 10px auto;
    }
    .invoice-card * { color: black !important; border-color: black !important; }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider { display: none !important; }
        .invoice-card { display: block !important; border: 2px solid black !important; padding: 50px !important; margin: 0 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# Data Initialization
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Arshpreet Kaur", "Region": "Courier", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
])

def get_business_day(start_date, days_to_subtract):
    curr = start_date
    while days_to_subtract > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days_to_subtract -= 1
    return curr

# Header
st.markdown('<div class="header-container"><div style="font-size: 22px; font-weight: 800;">🦷 Skycad Lab Night Guard Manager</div><div style="font-size: 12px;">Designed by Heechul Jung</div></div>', unsafe_allow_html=True)

# Tabs in English
tab1, tab2, tab3 = st.tabs(["📝 Case Entry", "📊 List & Status", "🔍 Search"])

with tab1:
    st.markdown("### 📋 Primary Information")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No (Pan No)", placeholder="e.g. ET33")
        patient = st.text_input("Patient Name")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic Name", ["Select"] + clinics)
        filtered_docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "Select" else []
        sel_doctor = st.selectbox("Doctor Name", ["Select"] + filtered_docs)
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        rec_date = today if is_3d else st.date_input("Received Date", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown("### 📅 Schedule Management")
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("Due Date", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("Lab Done Date", today + timedelta(days=1))
    with col4:
        ship_days = 1 if (sel_clinic != "Select" and ref_data[ref_data['Clinic']==sel_clinic]['Region'].iloc[0]=="Local") else 2
        ship_date = get_business_day(due_date, ship_days)
        st.date_input("Shipping Date", ship_date)

    if st.button("💾 SAVE CASE (REGISTER)"):
        if sel_clinic != "Select" and case_no:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "CaseNo": case_no, "Patient": patient, "Clinic": sel_clinic, "Doctor": sel_doctor,
                "Material": material, "Arch": arch, "LabDone": lab_done_date,
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success("Case successfully registered!")

with tab2:
    if not st.session_state.db: st.info("No cases pending.")
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([5, 1])
        with c_info: st.write(f"**{row['CaseNo']}** | {row['Patient']} | {row['Clinic']}")
        with c_btn:
            if st.button("Complete / Print", key=f"btn_{i}"):
                st.session_state.selected_invoice = row
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        # Invoice rendering (No Korean allowed here)
        invoice_html = f"""
        <div class="invoice-card">
            <table style="width: 100%; border: none;">
                <tr>
                    <td style="width: 50%; vertical-align: top;">
                        <div style="font-size: 11px; font-weight: bold; font-style: italic; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                        <div style="font-size: 70px; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 0.8; letter-spacing: -4px;">skycad</div>
                        <div style="margin-top: 25px; font-size: 14px; line-height: 1.3;">
                            <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                        </div>
                    </td>
                    <td style="text-align: right; width: 50%; vertical-align: top;">
                        <div style="font-size: 35px; font-weight: bold; letter-spacing: 5px;">INVOICE</div>
                        <div style="font-size: 16px; margin-top: 5px; font-weight: bold;">No. 162{inv['CaseNo'].replace('ET', '')}<br>{inv['LabDone'].strftime('%m/%d/%Y')}</div>
                        <div style="margin-top: 35px; text-align: left; font-size: 14px; line-height: 1.4; border: 1.5px solid black; padding: 15px; width: 230px; float: right;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>Dr. {inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}<br>{inv['Phone']}
                        </div>
                    </td>
                </tr>
            </table>

            <div style="margin: 80px 0 20px 0; font-size: 18px; border-bottom: 2.5px solid black; padding-bottom: 10px;">
                <b>Patient:</b> {str(inv['Patient']).upper()}
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-top: 10px;">
                <tr style="border-bottom: 1.5px solid black; font-weight: bold; font-size: 16px;">
                    <td style="padding: 12px 0; text-decoration: underline;">Description</td>
                    <td style="padding: 12px 0; text-align: right; text-decoration: underline;">Amount</td>
                </tr>
                <tr>
                    <td style="padding: 30px 0; height: 380px; vertical-align: top; font-size: 16px;">
                        Nightguard ({inv['Material']}) {inv['Arch'].upper()}
                    </td>
                    <td style="padding: 30px 0; text-align: right; vertical-align: top; font-size: 16px;">$180.00</td>
                </tr>
            </table>

            <div style="border-top: 2.5px solid black; padding-top: 15px; display: flex; justify-content: space-between; font-weight: bold; font-size: 18px;">
                <span>{inv['CaseNo']}</span>
                <span>Total: $180.00</span>
            </div>

            <div style="position: absolute; bottom: 60px; left: 45px; right: 45px; text-align: center;">
                <div style="font-size: 18px; font-weight: bold; text-decoration: underline; margin-bottom: 20px;">
                    All dental products we offer are custom made in Canada.
                </div>
                <div style="font-size: 11px; line-height: 1.6; padding: 0 20px;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        if st.button("PRINT INVOICE"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3: st.write("Search features...")
