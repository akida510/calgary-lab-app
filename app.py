import streamlit as st
import pandas as pd
from datetime import datetime, date

# [1. 기본 설정 및 디자인]
st.set_page_config(page_title="skycad lab night gaurd manager", layout="wide")

now = datetime.now()
current_month = now.strftime('%m월')
POST_TAX_UNIT = 19.505333

st.markdown("""
<style>
    .stApp { background-color: #0e1117 !important; }
    .main-header { padding: 10px 0 20px 0; border-bottom: 1px solid #333; margin-bottom: 20px; }
    .main-title { color: #ffffff !important; font-size: 1.8rem; font-weight: 800; margin: 0; }
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

# [3. 대시보드]
st.markdown(f"""
    <div class="main-header"><h1 class="main-title">🦷 skycad lab night gaurd manager</h1></div>
    <div style="margin-bottom:20px; color:#4ade80; font-weight:bold; font-size:1.1rem;">
        {current_month} 실적: {len(st.session_state.db)}건 | 예상 수익: ${len(st.session_state.db)*POST_TAX_UNIT:,.2f}
    </div>
    """, unsafe_allow_html=True)

# [4. 메인 기능]
tab1, tab2 = st.tabs(["📝 케이스 등록 및 일정", "📊 리스트 및 인보이스"])

with tab1:
    st.session_state.active_invoice = None  # 등록창에서는 인보이스 안 뜨게 초기화
    
    # 레이아웃 구성
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📌 기본 정보")
        case_no = st.text_input("Case No (팬번호)")
        patient = st.text_input("Patient (환자명)")
        
        # 병원명 선택/입력
        sel_cln = st.selectbox("Clinic (병원명) 선택", ["선택하세요", "직접 입력"] + all_clinics)
        final_cln = st.text_input("병원명 직접 입력") if sel_cln == "직접 입력" else (sel_cln if sel_cln != "선택하세요" else "")

        # 의사명 선택/입력
        auto_dr = ""
        if final_cln in ref_data["Clinic"].values:
            auto_dr = ref_data[ref_data["Clinic"] == final_cln]["Dr"].iloc[0]
        
        sel_dr = st.selectbox("Dr (의사명) 선택", ["선택하세요", "직접 입력"] + all_doctors, 
                              index=all_doctors.index(auto_dr)+2 if auto_dr in all_doctors else 0)
        final_dr = st.text_input("의사명 직접 입력") if sel_dr == "직접 입력" else (sel_dr if sel_dr != "선택하세요" else "")

        st.markdown("---")
        st.subheader("⚒️ 제작 사양")
        mat = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arc = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)

    with c2:
        st.subheader("📅 일정 관리 (필수)")
        # 접수 형태
        model_type = st.radio("접수 형태", ["3D 디지털 스캔", "일반 모델(석고)"], horizontal=True)
        
        # 날짜들 (처음 기획하신 대로 모두 복구)
        col_date1, col_date2 = st.columns(2)
        with col_date1:
            receive_date = st.date_input("접수일(Received)", value=date.today())
            request_date = st.date_input("요청일(Requested)", value=date.today() + timedelta(days=7))
        with col_date2:
            complete_date = st.date_input("완료일(Completed)", value=date.today() + timedelta(days=6))
            ship_date = st.date_input("출고일(Shipped)", value=date.today() + timedelta(days=7))
            
        inv_date = st.date_input("Invoice Date (인보이스 발행일)", value=date.today())

    # 저장 버튼
    if st.button("💾 모든 정보 저장 및 창 초기화", use_container_width=True):
        if case_no and final_cln:
            c_info = ref_data[ref_data["Clinic"] == final_cln].iloc[0] if final_cln in ref_data["Clinic"].values else {"Address": "", "City": "", "Phone": ""}
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter,
                "Case No": case_no,
                "Patient": patient,
                "Clinic": final_cln,
                "Dr": final_dr,
                "Address": c_info.get("Address", ""),
                "City": c_info.get("City", ""),
                "Phone": c_info.get("Phone", ""),
                "Material": mat,
                "Arch": arc,
                "Date": inv_date.strftime('%m/%d/%Y'),
                "Schedule": {
                    "Type": model_type,
                    "Received": receive_date.strftime('%Y-%m-%d'),
                    "Requested": request_date.strftime('%Y-%m-%d'),
                    "Completed": complete_date.strftime('%Y-%m-%d'),
                    "Shipped": ship_date.strftime('%Y-%m-%d')
                }
            })
            st.session_state.inv_counter += 1
            st.success(f"케이스 {case_no}번 저장 완료!")
            st.rerun()
        else:
            st.error("Case No와 병원명은 필수입니다.")

with tab2:
    st.markdown("### 📊 케이스 관리 리스트")
    for i, row in enumerate(st.session_state.db):
        col_info, col_btn = st.columns([5, 1])
        with col_info:
            sched = row.get('Schedule', {})
            # 리스트에 일정 요약 표시
            st.write(f"**No. {row['Inv_No']}** | {row['Patient']} ({row['Clinic']})")
            st.caption(f"📅 접수: {sched.get('Received','-')} | 완료: {sched.get('Completed','-')} | 출고: {sched.get('Shipped','-')} ({sched.get('Type','-')})")
        with col_btn:
            if st.button("🔍 Invoice", key=f"btn_inv_{i}"):
                st.session_state.active_invoice = row

    # 리스트 하단에 인보이스 출력
    if st.session_state.active_invoice:
        st.markdown("---")
        inv = st.session_state.active_invoice
        if st.button("❌ 인보이스 닫기"):
            st.session_state.active_invoice = None
            st.rerun()
            
        inv_html = f"""
        <div class="inv-container">
            <div class="inv-paper">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <div style="line-height:1;">
                            <span style="font-size:8px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                            <span style="font-size:38px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px;">skycad</span>
                        </div>
                        <div style="font-size:11px; margin-top:15px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</div>
                    </div>
                    <div style="text-align: right;">
                        <h1 style="font-size:32px; font-weight:400; margin:0;">INVOICE</h1>
                        <p style="font-size:12px; margin:8px 0;">No. {inv.get('Inv_No','')}<br>{inv.get('Date','')}</p>
                        <div style="text-align:left; font-size:11px; margin-top:20px;">
                            <b>Ship To:</b><br>{inv.get('Clinic','')}<br>{inv.get('Dr','')}<br>{inv.get('Address','')}<br>{inv.get('City','')}<br>{inv.get('Phone','')}
                        </div>
                    </div>
                </div>
                <div style="margin-top: 45px; padding: 12px 0; border-top: 1.8px solid black; border-bottom: 1.8px solid black; font-size: 14px;">
                    <b>Patient:</b> {str(inv.get('Patient','')).upper()}
                </div>
                <div style="flex: 1; margin-top: 30px;">
                    <table style="width: 100%; border-collapse: collapse;">
                        <thead><tr style="border-bottom: 1px solid black;"><th style="text-align:left; padding-bottom: 5px; text-decoration:underline;">Description</th><th style="text-align:right; padding-bottom: 5px; text-decoration:underline;">Amount</th></tr></thead>
                        <tbody><tr><td style="padding:25px 0; font-size:14px;">Nightguard ({inv.get('Material','')}) {inv.get('Arch','')}</td><td style="text-align:right; font-size:14px; font-weight:bold;">$180.00</td></tr></tbody>
                    </table>
                </div>
                <div style="border-top: 1.8px solid black; padding-top: 15px;">
                    <div style="display:flex; justify-content:space-between; font-size:13px; font-weight:bold;"><div>ET12</div><div>Total: $180.00</div></div>
                    <div class="notice-box"><b>All dental products we offer are custom made in Canada.</b><br><br>Please ensure payment is made within 30 days. Thank you.</div>
                </div>
            </div>
        </div>
        """
        st.markdown(inv_html, unsafe_allow_html=True)
