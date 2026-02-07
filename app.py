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
    <div style="margin-bottom:20px; color:#4ade80; font-weight:bold;">
        {current_month} 실적: {len(st.session_state.db)}건 | 예상 수익: ${len(st.session_state.db)*POST_TAX_UNIT:,.2f}
    </div>
    """, unsafe_allow_html=True)

# [4. 메인 기능]
tab1, tab2 = st.tabs(["📝 케이스 등록", "📊 리스트"])

with tab1:
    st.session_state.active_invoice = None
    
    # 폼 밖에서 미리 입력을 받아야 실시간으로 작동함
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No (팬번호)")
        patient = st.text_input("Patient (환자명)")
        
        # 병원명 처리
        sel_cln = st.selectbox("Clinic (병원명) 선택", ["선택하세요", "직접 입력"] + all_clinics)
        final_cln = ""
        if sel_cln == "직접 입력":
            final_cln = st.text_input("병원명 직접 입력")
        else:
            final_cln = sel_cln

        # 의사명 처리
        auto_dr = ""
        if final_cln in ref_data["Clinic"].values:
            auto_dr = ref_data[ref_data["Clinic"] == final_cln]["Dr"].iloc[0]
        
        sel_dr = st.selectbox("Dr (의사명) 선택", ["선택하세요", "직접 입력"] + all_doctors, 
                              index=all_doctors.index(auto_dr)+2 if auto_dr in all_doctors else 0)
        final_dr = ""
        if sel_dr == "직접 입력":
            final_dr = st.text_input("의사명 직접 입력")
        else:
            final_dr = sel_dr

    with c2:
        # 일정 등록 (접수 형태)
        model_type = st.radio("접수 형태", ["3D 디지털 스캔", "일반 모델(석고)"], horizontal=True)
        model_date = "-"
        if model_type == "일반 모델(석고)":
            model_date = st.date_input("모델 접수 날짜", value=date.today()).strftime('%Y-%m-%d')
        
        mat = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arc = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)
        inv_date = st.date_input("Invoice Date", value=date.today())

    if st.button("💾 정보 저장 및 초기화", use_container_width=True):
        if case_no and final_cln and final_cln != "선택하세요":
            c_info = ref_data[ref_data["Clinic"] == final_cln].iloc[0] if final_cln in ref_data["Clinic"].values else {"Address": "", "City": "", "Phone": ""}
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient,
                "Clinic": final_cln, "Dr": final_dr, 
                "Address": c_info.get("Address", ""), "City": c_info.get("City", ""), "Phone": c_info.get("Phone", ""),
                "Material": mat, "Arch": arc, "Date": inv_date.strftime('%m/%d/%Y'),
                "ModelInfo": f"{model_type} ({model_date})"
            })
            st.session_state.inv_counter += 1
            st.success("저장 완료!")
            st.rerun()

with tab2:
    st.markdown("### 📊 저장된 케이스 리스트")
    for i, row in enumerate(st.session_state.db):
        col1, col2 = st.columns([5, 1])
        with col1:
            # .get()을 사용하여 예전 데이터에서 ModelInfo가 없어도 에러 안 나게 수정
            m_info = row.get('ModelInfo', '정보 없음')
            st.write(f"**No. {row['Inv_No']}** | {row['Patient']} ({row['Clinic']}) - {m_info}")
        with col2:
            if st.button("🔍 Invoice", key=f"inv_show_{i}"):
                st.session_state.active_invoice = row
    
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
