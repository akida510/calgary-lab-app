import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 디자인 설정 - 제목 확대, 섹션 강조, 다크 테마]
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    
    /* 입력창 디자인 */
    input, select, textarea, div[data-baseweb="select"] {
        background-color: #1a1c24 !important; color: #ffffff !important;
        border: 1px solid #30363d !important;
    }
    input:disabled { background-color: #21262d !important; color: #8b949e !important; }

    /* 헤더 및 제작자 정보 */
    .header-box {
        display: flex; justify-content: space-between; align-items: flex-end;
        padding-bottom: 15px; border-bottom: 2px solid #30363d; margin-bottom: 25px;
    }
    .main-title { font-size: 38px !important; font-weight: 800 !important; color: #ffffff !important; }
    .creator-info { font-size: 14px !important; color: #8b949e !important; font-style: italic; }

    /* 섹션 타이틀 */
    .section-header {
        font-size: 24px !important; font-weight: 700 !important; color: #4c6ef5 !important;
        margin-top: 35px !important; margin-bottom: 15px !important; display: block;
    }

    /* 버튼 스타일 (콤팩트 다크톤) */
    .stButton>button { 
        width: auto !important; min-width: 100px !important; height: 2.5em !important; 
        background-color: #21262d !important; color: #c9d1d9 !important; 
        border: 1px solid #30363d !important; font-size: 14px !important;
        font-weight: 600 !important; border-radius: 6px !important; 
    }
    .stButton>button:hover { background-color: #30363d !important; border-color: #8b949e !important; color: #fff !important; }

    .stat-card { background-color: #161b22; padding: 20px; border-radius: 8px; border: 1px solid #30363d; margin-top: 30px; }
    
    /* 인보이스 정밀 레이아웃 (사진 양식 기반) */
    .inv-outer-container { display: flex; justify-content: center; padding: 20px 0; background-color: #0d1117; }
    .invoice-letter { 
        background-color: white !important; color: black !important; 
        width: 8.5in; min-height: 11in; padding: 0.7in; 
        border: 1px solid #d0d7de; box-sizing: border-box; 
        font-family: 'Arial', sans-serif; 
    }
    .invoice-letter * { color: black !important; }
    .inv-table { width: 100%; border-collapse: collapse; margin-top: 30px; }
    .inv-table th { border-top: 2px solid black; border-bottom: 2px solid black; padding: 12px 5px; text-align: left; }
    .inv-table td { padding: 20px 5px; vertical-align: top; border-bottom: 0.5px solid #eee; }
    .inv-totals { float: right; width: 260px; margin-top: 40px; }
    .inv-totals div { display: flex; justify-content: space-between; padding: 6px 0; font-size: 15px; }
    .total-row { border-top: 1.5px solid black; font-weight: bold; font-size: 18px !important; margin-top: 8px; padding-top: 10px !important; }
    
    @media print {
        .stButton, .stTabs, [data-testid="stSidebar"], .stMarkdown, .stDivider, .stat-card, .header-box { display: none !important; }
        .inv-outer-container { padding: 0; background: white; }
        .invoice-letter { border: none; width: 100%; padding: 0; margin: 0; }
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 및 세션 관리]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084

# 마스터 데이터
ref_data = pd.DataFrame([
    {"Clinic": "Calgary Central", "Doctor": "Lana Huynh", "Region": "Local", "Address": "205-7136 11 St NE", "City": "Calgary, AB T2E 4Y9"},
    {"Clinic": "Edmonton North", "Doctor": "Joseph M.", "Region": "Courier", "Address": "13510 127 St NW", "City": "Edmonton, AB T5L 1B9"},
])

if 'cur_cln' not in st.session_state: st.session_state.cur_cln = "선택"
if 'cur_doc' not in st.session_state: st.session_state.cur_doc = "선택"

# 양방향 연동 함수
def sync_cln():
    val = st.session_state.cln_select
    if val != "선택":
        st.session_state.cur_cln = val
        st.session_state.cur_doc = ref_data[ref_data['Clinic'] == val]['Doctor'].iloc[0]
    else: st.session_state.cur_cln = "선택"; st.session_state.cur_doc = "선택"

def sync_doc():
    val = st.session_state.doc_select
    if val != "선택":
        st.session_state.cur_doc = val
        st.session_state.cur_cln = ref_data[ref_data['Doctor'] == val]['Clinic'].iloc[0]
    else: st.session_state.cur_cln = "선택"; st.session_state.cur_doc = "선택"

def get_business_day(start_date, days_to_subtract):
    curr = start_date
    while days_to_subtract > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days_to_subtract -= 1
    return curr

# [3. 메인 화면 구성]
st.markdown('<div class="header-box"><div class="main-title">🦷 Skycad Lab Manager</div><div class="creator-info">Created by Heechul Jung</div></div>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 케이스 등록", "📊 리스트 및 완료", "🔍 검색"])

with tab1:
    st.markdown('<span class="section-header">📋 기본정보입력</span>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No (팬번호)")
        patient = st.text_input("Patient (환자명)")
        
        clns = ["선택"] + sorted(ref_data['Clinic'].tolist())
        st.selectbox("Clinic (병원명)", clns, key="cln_select", index=clns.index(st.session_state.cur_cln), on_change=sync_cln)
        
        docs = ["선택"] + sorted(ref_data['Doctor'].tolist())
        st.selectbox("Doctor (의사명)", docs, key="doc_select", index=docs.index(st.session_state.cur_doc), on_change=sync_doc)
                     
    with c2:
        is_3d = st.checkbox("3D Model", value=True)
        today = date.today()
        # 3D모델 체크 여부에 따라 날짜 입력창 활성화/비활성화
        rec_date = st.date_input("접수일", value=today, disabled=is_3d)
        material = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arch = st.radio("Arch", ["Max", "Mand", "Both"], horizontal=True)

    st.markdown('<span class="section-header">📅 일정 관리</span>', unsafe_allow_html=True)
    col3, col4, col5 = st.columns(3)
    with col5: due_date = st.date_input("Due Date (요청일)", today + timedelta(days=7))
    with col3: lab_done_date = st.date_input("Lab Done (완료일)", today + timedelta(days=1))
    with col4:
        reg = ref_data[ref_data['Clinic']==st.session_state.cur_cln]['Region'].iloc[0] if st.session_state.cur_cln != "선택" else "Local"
        ship_date = get_business_day(due_date, 1 if reg=="Local" else 2)
        st.date_input("Shipping Date (출고일)", ship_date)

    st.write("---")
    if st.button("💾 케이스 저장하기"):
        if st.session_state.cur_cln == "선택" or not case_no: st.error("필수 입력 항목(Case No, Clinic)을 확인하세요.")
        else:
            c_info = ref_data[ref_data['Clinic'] == st.session_state.cur_cln].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, 
                "Clinic": st.session_state.cur_cln, "Doctor": st.session_state.cur_doc, 
                "Material": material, "Arch": arch, "Status": "Pending",
                "Address": c_info.get("Address", ""), "City": c_info.get("City", ""),
                "Inv_Date": today.strftime('%m/%d/%Y'), "Due": due_date, "Month": today.strftime('%Y-%m')
            })
            st.session_state.inv_counter += 1
            st.success(f"{case_no}번 케이스가 성공적으로 저장되었습니다.")
            st.rerun()

with tab2:
    st.markdown('<span class="section-header">📊 작업 진행 리스트</span>', unsafe_allow_html=True)
    this_month = date.today().strftime('%Y-%m')
    monthly_cases = [r for r in st.session_state.db if r.get('Month') == this_month]
    
    for i, row in enumerate(st.session_state.db):
        c_info, c_btn = st.columns([6, 1])
        with c_info:
            icon = "🟢" if row['Status']=="Completed" else "🟡"
            st.markdown(f"**{icon} {row['Case No']}** | {row['Patient']} | {row['Clinic']} | Due: {row['Due']}")
        with c_btn:
            lbl = "완료" if row['Status'] == "Pending" else "재출력"
            if st.button(lbl, key=f"btn_{i}"):
                st.session_state.db[i]['Status'] = "Completed"
                st.session_state.selected_invoice = st.session_state.db[i]
                st.rerun()

    if st.session_state.selected_invoice:
        inv = st.session_state.selected_invoice
        st.divider()
        c_c, c_p = st.columns([0.1, 1])
        with c_c: 
            if st.button("닫기"): st.session_state.selected_invoice = None; st.rerun()
        with c_p:
            if st.button("🖨️ 인쇄하기"): st.markdown('<script>window.print();</script>', unsafe_allow_html=True)
        
        # 인보이스 하단 정밀 계산 ($180 고정)
        price = 180.00
        gst = price * 0.05
        total = price + gst
        
        st.markdown(f"""
        <div class="inv-outer-container">
            <div class="invoice-letter">
                <div style="display: flex; justify-content: space-between;">
                    <div>
                        <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                        <span style="font-size:48px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px; line-height:1;">skycad</span>
                        <div style="font-size:12px; margin-top:25px;"><b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9</div>
                    </div>
                    <div style="text-align: right;">
                        <h1 style="font-size:38px; font-weight:400; margin:0; letter-spacing:4px;">INVOICE</h1>
                        <p style="font-size:14px; margin-top:10px;"><b>Date:</b> {inv.get('Inv_Date','')}<br><b>Invoice No:</b> {inv.get('Inv_No','')}</p>
                        <div style="text-align:left; font-size:13px; margin-top:35px; border:1px solid #eee; padding:15px; width:220px; float:right;">
                            <b>Ship To:</b><br>{inv.get('Clinic','')}<br>{inv.get('Address','')}<br>{inv.get('City','')}
                        </div>
                    </div>
                </div>
                <div style="clear:both; margin-top:40px; font-size:16px;"><b>Patient:</b> {str(inv.get('Patient','')).upper()}</div>
                <table class="inv-table">
                    <thead><tr><th>Description</th><th style="text-align:right;">Amount</th></tr></thead>
                    <tbody>
                        <tr>
                            <td style="height:380px;">Nightguard ({inv.get('Material','')}) {inv.get('Arch','')}<br>
                                <span style="font-size:13px; color:#555;">Case No: {inv.get('Case No','')}</span></td>
                            <td style="text-align:right;">${price:,.2f}</td>
                        </tr>
                    </tbody>
                </table>
                <div class="inv-footer">
                    <div class="inv-totals">
                        <div><span>Subtotal:</span><span>${price:,.2f}</span></div>
                        <div><span>GST (5.0%):</span><span>${gst:,.2f}</span></div>
                        <div class="total-row"><span>Total:</span><span>${total:,.2f}</span></div>
                    </div>
                    <div style="clear:both;"></div>
                </div>
                <div style="margin-top:100px;">
                    <div style="border-top:1px solid black; width:220px; padding-top:5px; font-size:13px;">Authorized Signature</div>
                    <p style="text-align:center; margin-top:50px; font-size:12px; color:#777;">Thank you for your business!</p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # 하단 현황판
    st.markdown(f"""
    <div class="stat-card">
        <div style="display:flex; gap:60px;">
            <div><p style="margin:0; font-size:13px; color:#8b949e;">총 수량</p><p style="font-size:24px; font-weight:bold;">{len(monthly_cases)} / 320</p></div>
            <div><p style="margin:0; font-size:13px; color:#8b949e;">인센티브 ($19.5)</p><p style="font-size:24px; font-weight:bold; color:#3fb950;">${max(0, len(monthly_cases)-320)*19.5:,.1f}</p></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

with tab3: st.info("🔍 검색 기능은 데이터 축적 후 활성화됩니다.")
