import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [Configuration] Force Dark Theme for App, White for Invoice
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    /* Global App Styling */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    label p, .stMarkdown p, .stTabs [data-baseweb="tab"] p { 
        color: #ffffff !important; font-weight: 600 !important; 
    }

    /* Header Styling */
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 15px 20px; border-radius: 10px;
        margin-bottom: 20px; border: 1px solid #30363d;
    }

    /* Primary Buttons */
    .stButton>button { 
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important; 
        color: white !important; font-weight: bold; border-radius: 5px; border: none;
    }

    /* List View Buttons (Slim) */
    div[data-testid="column"] .stButton>button {
        height: 32px !important; font-size: 12px !important; padding: 0 15px !important;
        background-color: #2b3a67 !important;
    }
    
    /* Responsive Invoice Container */
    .invoice-wrapper {
        background-color: white !important;
        padding: 20px;
        border-radius: 8px;
        margin-top: 20px;
    }

    .invoice-body {
        color: black !important;
        font-family: 'Helvetica', 'Arial', sans-serif;
        max-width: 800px;
        margin: 0 auto;
        line-height: 1.3;
    }
    .invoice-body * { color: black !important; border-color: black !important; }

    /* Mobile specific adjustments to prevent clipping */
    @media screen and (max-width: 600px) {
        .invoice-header { flex-direction: column !important; }
        .invoice-header-right { text-align: left !important; margin-top: 20px !important; }
        .ship-box { width: 100% !important; }
        .skycad-logo { font-size: 50px !important; }
    }

    @media print {
        .stButton, .header-container, .stTabs, [data-testid="stSidebar"], .stDivider { display: none !important; }
        .invoice-wrapper { padding: 0 !important; }
        .invoice-body { width: 100% !important; max-width: none !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# [Data Management]
# ---------------------------------------------------------
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Addr": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"},
    {"Clinic": "Edmonton North", "Doctor": "Arshpreet Kaur", "Addr": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9", "Phone": "(780) 455-6806"},
])

# ---------------------------------------------------------
# [Main UI - All English]
# ---------------------------------------------------------
st.markdown('<div class="header-container"><div style="font-size: 22px; font-weight: 800;">🦷 Skycad Lab Manager</div><div style="font-size: 11px;">Admin Mode</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Case Entry", "📊 Job List", "🔍 Search"])

with tab1:
    st.markdown("### 📋 Case Information")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No (Pan No)", placeholder="e.g. ET33")
        patient = st.text_input("Patient Name")
        clinics = sorted(list(set(ref_data['Clinic'].tolist())))
        sel_clinic = st.selectbox("Clinic", ["Select Clinic"] + clinics)
        
        docs = ref_data[ref_data['Clinic'] == sel_clinic]['Doctor'].tolist() if sel_clinic != "Select Clinic" else []
        sel_doctor = st.selectbox("Doctor", ["Select Doctor"] + docs)
    
    with c2:
        today = date.today()
        rec_date = st.date_input("Received Date", today)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)
        due_date = st.date_input("Due Date", today + timedelta(days=7))

    if st.button("💾 SAVE CASE"):
        if sel_clinic == "Select Clinic" or not case_no:
            st.error("Please fill in Case No and Clinic.")
        else:
            c_info = ref_data[ref_data['Clinic'] == sel_clinic].iloc[0]
            st.session_state.db.append({
                "Case No": case_no, "Patient": patient, "Clinic": sel_clinic, 
                "Doctor": sel_doctor, "Material": material, "Arch": arch,
                "Date": today, "Due": due_date, "Status": "Pending",
                "Addr": c_info['Addr'], "City": c_info['City'], "Phone": c_info['Phone']
            })
            st.success(f"Case {case_no} Saved!")

with tab2:
    if not st.session_state.db:
        st.info("No active cases.")
    else:
        for i, row in enumerate(st.session_state.db):
            col_idx, col_btn = st.columns([5, 2])
            with col_idx:
                st.write(f"**{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
            with col_btn:
                if st.button("Complete / Print", key=f"btn_{i}"):
                    st.session_state.selected_invoice = row
                    st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        
        # English Invoice with Responsive Layout
        invoice_html = f"""
        <div class="invoice-wrapper">
            <div class="invoice-body">
                <div class="invoice-header" style="display: flex; justify-content: space-between; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 250px;">
                        <div style="font-size: 10px; font-weight: bold; color: #1a4e8a !important;">DENTAL TECHNOLOGY Ltd</div>
                        <div class="skycad-logo" style="font-size: 65px; font-weight: 900; font-style: italic; color: #1a4e8a !important; line-height: 0.8; letter-spacing: -3px;">skycad</div>
                        <div style="margin-top: 15px; font-size: 14px;">
                            <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                        </div>
                    </div>
                    <div class="invoice-header-right" style="flex: 1; min-width: 250px; text-align: right;">
                        <div style="font-size: 32px; font-weight: bold; letter-spacing: 4px;">INVOICE</div>
                        <div style="font-size: 15px; font-weight: bold; margin-bottom: 20px;">
                            No. 162{inv['Case No'].replace('ET','')}<br>{inv['Date'].strftime('%m/%d/%Y')}
                        </div>
                        <div class="ship-box" style="text-align: left; font-size: 13px; border: 1px solid black; padding: 12px; display: inline-block; width: 240px;">
                            <b>Ship To:</b><br>
                            {inv['Clinic']}<br>
                            Dr. {inv['Doctor']}<br>
                            {inv['Addr']}<br>
                            {inv['City']}<br>
                            {inv['Phone']}
                        </div>
                    </div>
                </div>

                <div style="margin: 40px 0 10px 0; font-size: 18px; border-bottom: 2px solid black; padding-bottom: 5px;">
                    <b>Patient:</b> {str(inv['Patient']).upper()}
                </div>

                <div style="display: flex; justify-content: space-between; border-bottom: 1px solid black; font-weight: bold; padding: 10px 0; font-size: 16px;">
                    <span style="text-decoration: underline;">Description</span>
                    <span style="text-decoration: underline;">Amount</span>
                </div>
                
                <div style="display: flex; justify-content: space-between; min-height: 350px; padding: 20px 0; font-size: 16px;">
                    <span>Nightguard ({inv['Material']}) {inv['Arch'].upper()}</span>
                    <span>$180.00</span>
                </div>

                <div style="border-top: 2px solid black; padding-top: 8px; display: flex; justify-content: space-between; font-weight: bold; font-size: 18px;">
                    <span>{inv['Case No']}</span>
                    <span>Total: $180.00</span>
                </div>

                <div style="margin-top: 60px; text-align: center;">
                    <div style="font-size: 15px; font-weight: bold; text-decoration: underline; margin-bottom: 12px;">All dental products we offer are custom made in Canada.</div>
                    <div style="font-size: 10px; line-height: 1.5; color: #444 !important; padding: 0 10px;">
                        Please ensure your monthly payment is made within 30 days of receiving your statement. Balances over 30 days will be subject to a finance charge of 1.5% per month (19.562% APR). Thank you.
                    </div>
                </div>
            </div>
        </div>
        """
        st.markdown(invoice_html, unsafe_allow_html=True)
        
        if st.button("🖨️ PRINT INVOICE"):
            st.markdown('<script>window.print();</script>', unsafe_allow_html=True)

with tab3:
    st.info("Search feature coming soon.")
