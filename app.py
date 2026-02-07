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
    .main-title { color: #ffffff; font-size: 1.8rem; font-weight: 800; margin: 0; text-transform: uppercase; }
    .author-info { color: #94a3b8; font-size: 0.85rem; margin-top: 5px; }
    .slim-dashboard {
        background: #1e212b; padding: 12px 20px; border-radius: 12px;
        border: 1px solid #3d414d; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 25px;
    }
    .stat-group { display: flex; align-items: baseline; gap: 8px; }
    .stat-label { color: #94a3b8; font-size: 0.8rem; }
    .stat-value { color: #ffffff; font-size: 1.2rem; font-weight: 700; }
    .money-badge {
        background: #2d323e; padding: 4px 12px; border-radius: 6px;
        border: 1px solid #4ade80; margin-left: 10px; display: flex;
        flex-direction: column; align-items: center;
    }
    .money-text { color: #4ade80; font-weight: 600; font-size: 0.95rem; }
    
    /* 인보이스 박스 디자인 */
    .invoice-overlay { background-color: rgba(0,0,0,0.95); padding: 30px; display: flex; justify-content: center; }
    .invoice-paper {
        background-color: #ffffff !important; width: 100%; max-width: 780px; 
        min-height: 1050px; padding: 50px; border: 2px solid #000; margin: 0 auto;
        display: flex; flex-direction: column; color: #000 !important; box-sizing: border-box;
    }
    .invoice-paper * { color: #000000 !important; -webkit-text-fill-color: #000000 !important; font-family: 'Arial', sans-serif !important; }
    .notice-box { border: 1px solid black; padding: 12px; text-align: center; font-size: 10px; line-height: 1.4; margin-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 및 참조 정보]
if 'db' not in st.session_state: st.session_state.db = []
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084
if 'active_invoice' not in st.session_state: st.session_state.active_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Dr": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Region": "Courier"},
    {"Clinic": "Calgary Central Dental", "Dr": "Dr. Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Region": "Local"}
])
all_clinics = sorted(ref_data["Clinic"].unique().tolist())
all_doctors = sorted(ref_data["Dr"].unique().tolist())

# [3. 상단 타이틀 및 실적]
st.markdown(f"""
    <div class="main-header">
        <h1 class="main-title">🦷 skycad lab night gaurd manager</h1>
        <p class="author-info">Designed by <b>Heechul</b> | Calgary, AB</p>
    </div>
    <div class="slim-dashboard">
        <div class="stat-group">
            <span class="stat-label">{current_month} 실적</span>
            <span class="stat-value">{len(st.session_state.db)} / 320</span>
        </div>
        <div style="display: flex;">
            <div class="money-badge" style="border-color: #555;"><span style="font-size:0.6rem; color:#94a3b8;">PRE-TAX</span><span class="money-text" style="color:#eee;">${len(st.session_state.db)*PRE_TAX_UNIT:,.2f}</span></div>
            <div class="money-badge"><span style="font-size:0.6rem; color:#4ade80;">AFTER-TAX</span><span class="money-text">${len(st.session_state.db)*POST_TAX_UNIT:,.2f}</span></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# [4. 메인 탭 기능]
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 등록")
    
    # st.form을 사용하여 저장 후 자동 지우기 구현
    with st.form("input_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            case_no = st.text_input("Case No (팬번호)")
            patient = st.text_input("Patient (환자명)")
            
            # 의사명/병원명 연동 로직
            sel_dr = st.selectbox("Dr (의사명) 선택", ["선택 안 함"] + all_doctors)
            input_dr = st.text_input("Dr (의사명) 직접입력")
            final_dr = input_dr if input_dr else (sel_dr if sel_dr != "선택 안 함" else "")
            
            auto_clinic = ""
            if final_dr in ref_data["Dr"].values:
                auto_clinic = ref_data[ref_data["Dr"] == final_dr]["Clinic"].iloc[0]
            
            sel_cln = st.selectbox("Clinic (병원명)", ["선택 안 함"] + all_clinics, 
                                   index=all_clinics.index(auto_clinic)+1 if auto_clinic in all_clinics else 0)
            
        with c2:
            model_type = st.radio("접수 형태", ["3D 디지털 스캔", "일반 모델"], index=0, horizontal=True)
            
            # 일반 모델일 때만 날짜 선택 (기본 '-' 표시 로직 처리)
            model_date = "-"
            if model_type == "일반 모델":
                model_date_input = st.date_input("접수 날짜", value=date.today())
                model_date = model_date_input.strftime('%Y-%m-%d')
            
            mat = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
            arc = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)
            due = st.date_input("Due Date (요청일)", date.today() + timedelta(days=7))

        submit = st.form_submit_button("💾 모든 정보 저장")
        
        if submit:
            if case_no and sel_cln != "선택 안 함":
                clinic_info = ref_data[ref_data["Clinic"] == sel_cln].iloc[0] if sel_cln in ref_data["Clinic"].values else {"Address": "", "Region": "Local"}
                
                st.session_state.db.append({
                    "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient,
                    "Clinic": sel_cln, "Dr": final_dr, "Address": clinic_info.get("Address", ""),
                    "Material": mat, "Arch": arc, "Model": model_type, "ModelDate": model_date,
                    "Due": due.strftime('%Y-%m-%d'), "Date": date.today().strftime('%Y-%m-%d')
                })
                st.session_state.inv_counter += 1
                st.success(f"저장 완료! Case {case_no}")
                st.rerun() # 저장 후 상태 갱신 및 커서 이동(초기화) 효과

with tab2:
    for i, row in enumerate(st.session_state.db):
        col1, col2, col3 = st.columns([3, 1.5, 1])
        col1.write(f"**{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
        col2.write(f"📅 {row.get('Model', '')}: {row.get('ModelDate', '-')}")
        if col3.button("🔍 Invoice", key=f"v_{i}"): st.session_state.active_invoice = row

with tab3:
    sq = st.text_input("검색 (환자, 병원, 의사명)")
    if sq:
        res = [r for r in st.session_state.db if sq.lower() in str(r).lower()]
        for r in res: st.write(f"✅ {r['Case No']} | {r['Patient']} | {r.get('Dr', 'N/A')} | {r.get('Due', '')}")

# [5. 인보이스 미리보기]
if st.session_state.active_invoice:
    st.markdown('---')
    if st.button("❌ 닫기"): st.session_state.active_invoice = None; st.rerun()
    inv = st.session_state.active_invoice
    
    # KeyError 방지를 위한 .get() 사용
    inv_dr = inv.get('Dr', 'N/A')
    inv_cln = inv.get('Clinic', 'N/A')
    inv_addr = inv.get('Address', '')
    
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
                        <p style="margin:5px 0; font-size:12px;">No. {inv['Inv_No']} | {inv.get('Date', '')}</p>
                        <div style="text-align:left; font-size:11px; border-top:1px solid #000; padding-top:5px; margin-top:10px;">
                            <b>Ship To:</b><br>{inv_cln}<br>{inv_dr}<br>{inv_addr}
                        </div>
                    </div>
                </div>
                <div style="margin-top: 25px; padding: 10px 0; border-top: 1.5px solid black; border-bottom: 1.5px solid black; font-size: 15px; font-weight: bold;">
                    Patient: &nbsp; {inv['Patient'].upper()}
                </div>
            </div>
            <div class="invoice-body">
                <table style="width: 100%; border-collapse: collapse;">
                    <thead><tr><th style="text-align:left; border-bottom: 1px solid black; padding-bottom: 5px;">Description</th><th style="text-align:right; border-bottom: 1px solid black; padding-bottom: 5px;">Amount</th></tr></thead>
                    <tbody><tr><td style="padding:40px 0;">Nightguard ({inv['Material']}) {inv['Arch']}<br>
                    <small style="color:#666;">Type: {inv.get('Model', '')} ({inv.get('ModelDate', '-')})</small></td><td style="text-align:right;">$180.00</td></tr></tbody>
                </table>
            </div>
            <div class="invoice-footer">
                <div style="display:flex; justify-content:space-between; font-size:14px; border-top:1px solid #ddd; padding-top:10px; margin-bottom:10px;">
                    <div>Case: {inv['Case No']} | Due: {inv.get('Due', '')}</div><div style="font-weight:bold;">Total: $180.00</div>
                </div>
                <div class="notice-box">
                    <b>All dental products are custom made in Canada.</b><br>
                    Payment is due within 30 days. Overdue balances are subject to 1.5% monthly finance charge. Thank you.
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
