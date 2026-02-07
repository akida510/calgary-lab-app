import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정 및 디자인]
st.set_page_config(page_title="skycad lab night gaurd manager", layout="wide")

now = datetime.now()
current_month = now.strftime('%m월')
PRE_TAX_UNIT = 30.0
POST_TAX_UNIT = 19.505333

st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; }
    .main-header { padding: 10px 0 20px 0; border-bottom: 1px solid #333; margin-bottom: 20px; }
    .main-title { color: #ffffff !important; font-size: 1.8rem; font-weight: 800; margin: 0; text-transform: uppercase; }
    .author-info { color: #94a3b8 !important; font-size: 0.85rem; margin-top: 5px; }
    .slim-dashboard {
        background: #1e212b; padding: 12px 20px; border-radius: 12px;
        border: 1px solid #3d414d; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 25px;
    }
    .stat-label { color: #94a3b8; font-size: 0.8rem; }
    .stat-value { color: #ffffff; font-size: 1.2rem; font-weight: 700; }
    .money-badge {
        background: #2d323e; padding: 4px 12px; border-radius: 6px;
        border: 1px solid #4ade80; margin-left: 10px; display: flex;
        flex-direction: column; align-items: center;
    }
    .money-text { color: #4ade80; font-weight: 600; font-size: 0.95rem; }
    
    /* 인보이스 디자인 고정 */
    .inv-container { background-color: rgba(0,0,0,0.9); padding: 40px 10px; display: flex; justify-content: center; width: 100%; }
    .inv-paper { 
        background-color: white !important; width: 100%; max-width: 800px; 
        min-height: 1000px; padding: 60px; border: 2.3px solid black; box-sizing: border-box;
    }
    .inv-paper * { color: black !important; font-family: 'Arial', sans-serif !important; }
    .notice-box { border: 1.5px solid black; padding: 15px; text-align: center; font-size: 11px; line-height: 1.4; margin-top: 30px; }
</style>
""", unsafe_allow_html=True)

# [2. 데이터 및 참조 정보]
if 'db' not in st.session_state: st.session_state.db = []
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084
if 'active_invoice' not in st.session_state: st.session_state.active_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Dr": "Dr. Arshpreet Kaur", "Address": "13510 127 St NW", "City": "Edmonton, Alberta T5L 1B9", "Phone": "(780) 455-6806"},
    {"Clinic": "Calgary Central Dental", "Dr": "Dr. Lana Huynh", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9", "Phone": "(403) 970-0600"}
])
all_clinics = sorted(ref_data["Clinic"].unique().tolist())
all_doctors = sorted(ref_data["Dr"].unique().tolist())

# [3. 대시보드 표시]
st.markdown(f"""
    <div class="main-header">
        <h1 class="main-title">🦷 skycad lab night gaurd manager</h1>
        <p class="author-info">Designed by <b>Heechul</b> | Calgary, AB</p>
    </div>
    <div class="slim-dashboard">
        <div class="stat-group"><span class="stat-label">{current_month} 실적</span> <span class="stat-value">{len(st.session_state.db)} / 320</span></div>
        <div style="display: flex;">
            <div class="money-badge" style="border-color: #555;"><span style="font-size:0.6rem; color:#94a3b8;">PRE-TAX</span><span class="money-text" style="color:#eee;">${len(st.session_state.db)*PRE_TAX_UNIT:,.2f}</span></div>
            <div class="money-badge"><span style="font-size:0.6rem; color:#4ade80;">AFTER-TAX</span><span class="money-text">${len(st.session_state.db)*POST_TAX_UNIT:,.2f}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# [4. 케이스 등록 탭]
tab1, tab2 = st.tabs(["📝 케이스 등록", "📊 리스트"])

with tab1:
    with st.form("case_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            case_no = st.text_input("Case No (팬번호)")
            patient = st.text_input("Patient (환자명)")
            
            # 의사명 입력/선택 및 병원 연동
            sel_dr = st.selectbox("Dr (의사명) 선택", ["선택 안 함"] + all_doctors)
            input_dr = st.text_input("Dr (의사명) 직접입력")
            final_dr = input_dr if input_dr else (sel_dr if sel_dr != "선택 안 함" else "")
            
            auto_clinic = ""
            if final_dr in ref_data["Dr"].values:
                auto_clinic = ref_data[ref_data["Dr"] == final_dr]["Clinic"].iloc[0]
            sel_cln = st.selectbox("Clinic (병원명)", ["선택 안 함"] + all_clinics, 
                                   index=all_clinics.index(auto_clinic)+1 if auto_clinic in all_clinics else 0)

        with c2:
            # 접수 형태 로직 (3D 디지털 스캔 기본)
            model_type = st.radio("접수 형태", ["3D 디지털 스캔", "일반 모델"], index=0, horizontal=True)
            
            model_date = "-"
            if model_type == "일반 모델":
                model_date_input = st.date_input("접수 날짜", value=date.today())
                model_date = model_date_input.strftime('%Y-%m-%d')
            
            mat = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
            arc = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)
            inv_date = st.date_input("Invoice Date", value=date.today())

        if st.form_submit_button("💾 정보 저장 및 초기화"):
            if case_no and (sel_cln != "선택 안 함"):
                c_info = ref_data[ref_data["Clinic"] == sel_cln].iloc[0] if sel_cln in ref_data["Clinic"].values else {"Address": "", "City": "", "Phone": ""}
                st.session_state.db.append({
                    "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient,
                    "Clinic": sel_cln, "Dr": final_dr, 
                    "Address": c_info.get("Address", ""), "City": c_info.get("City", ""), "Phone": c_info.get("Phone", ""),
                    "Material": mat, "Arch": arc, "Date": inv_date.strftime('%m/%d/%Y'),
                    "ModelInfo": f"{model_type} ({model_date})"
                })
                st.session_state.inv_counter += 1
                st.success("저장 완료! 입력창이 초기화되었습니다.")
                st.rerun() # 저장 후 새로고침하여 커서를 Case No로 이동

with tab2:
    for i, row in enumerate(st.session_state.db):
        if st.button(f"📄 No. {row.get('Inv_No')} - {row.get('Patient')} ({row.get('Clinic')})", key=f"inv_btn_{i}"):
            st.session_state.active_invoice = row
            st.rerun()

# [5. 인보이스 출력 영역]
if st.session_state.active_invoice:
    st.markdown("---")
    if st.button("❌ 닫기"):
        st.session_state.active_invoice = None
        st.rerun()
    
    inv = st.session_state.active_invoice
    
    inv_html = f"""
    <div class="inv-container">
        <div class="inv-paper">
            <div style="display: flex; justify-content: space-between;">
                <div>
                    <div style="line-height:1;">
                        <span style="font-size:8px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:38px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px;">skycad</span>
                    </div>
                    <div style="font-size:11px; margin-top:15px; line-height:1.4;">
                        <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                    </div>
                </div>
                <div style="text-align: right;">
                    <h1 style="font-size:32px; font-weight:400; margin:0;">INVOICE</h1>
                    <p style="font-size:12px; margin:8px 0;">No. {inv.get('Inv_No', '')}<br>{inv.get('Date', '')}</p>
                    <div style="text-align:left; font-size:11px; margin-top:20px;">
                        <b>Ship To:</b><br>{inv.get('Clinic', '')}<br>{inv.get('Dr', '')}<br>{inv.get('Address', '')}<br>{inv.get('City', '')}<br>{inv.get('Phone', '')}
                    </div>
                </div>
            </div>
            <div style="margin-top: 45px; padding: 12px 0; border-top: 1.8px solid black; border-bottom: 1.8px solid black; font-size: 14px;">
                <b>Patient:</b> {str(inv.get('Patient', '')).upper()}
            </div>
            <div style="flex: 1; margin-top: 30px;">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead>
                        <tr style="border-bottom: 1px solid black;">
                            <th style="text-align:left; padding-bottom: 5px; font-size:12px; text-decoration:underline;">Description</th>
                            <th style="text-align:right; padding-bottom: 5px; font-size:12px; text-decoration:underline;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td style="padding:25px 0; font-size:14px;">Nightguard ({inv.get('Material', '')}) {inv.get('Arch', '')}</td>
                            <td style="text-align:right; font-size:14px; font-weight:bold;">$180.00</td>
                        </tr>
                    </tbody>
                </table>
            </div>
            <div style="border-top: 1.8px solid black; padding-top: 15px;">
                <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:bold;">
                    <div>ET12</div><div>Total: $180.00</div>
                </div>
                <div class="notice-box">
                    <u style="font-weight:bold; font-size:13px;">All dental products we offer are custom made in Canada.</u><br><br>
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </div>
            </div>
        </div>
    </div>
    """
    st.markdown(inv_html, unsafe_allow_html=True)
