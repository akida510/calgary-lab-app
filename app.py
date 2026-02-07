import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

# [1. 기본 설정 및 디자인]
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

now = datetime.now()
current_month = now.strftime('%m월')
PRE_TAX_UNIT = 30.0
POST_TAX_UNIT = 19.505333

st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    
    /* 세련된 대시보드 */
    .slim-dashboard {
        background: #1e212b; padding: 12px 20px; border-radius: 12px;
        border: 1px solid #3d414d; display: flex; justify-content: space-between;
        align-items: center; margin-bottom: 20px;
    }
    .stat-group { display: flex; align-items: baseline; gap: 8px; }
    .stat-label { color: #94a3b8; font-size: 0.8rem; font-weight: 500; }
    .stat-value { color: #ffffff; font-size: 1.2rem; font-weight: 700; }
    .money-badge {
        background: #2d323e; padding: 4px 10px; border-radius: 6px;
        border: 1px solid #4ade80; margin-left: 8px; display: flex;
        flex-direction: column; align-items: center;
    }
    .money-text { color: #4ade80; font-weight: 600; font-size: 0.9rem; }
    .money-label-sub { font-size: 0.65rem; color: #94a3b8; }

    /* 인보이스 박스 디자인 및 상하단 밀착 */
    .invoice-overlay { 
        background-color: rgba(0,0,0,0.9); padding: 20px; 
        display: flex; justify-content: center;
    }
    .invoice-paper {
        background-color: #ffffff !important; 
        width: 100%; max-width: 750px; 
        min-height: 1000px;
        padding: 45px; 
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
    .invoice-body { flex: 1; width: 100%; margin-top: 40px; }
    .invoice-footer { width: 100%; flex-shrink: 0; margin-top: auto; }
    
    .notice-box { 
        border: 1px solid black; padding: 10px; text-align: center; 
        font-size: 10px; line-height: 1.3; margin-top: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# [2. 데이터 초기화 및 로직]
if 'db' not in st.session_state: st.session_state.db = []
if 'inv_counter' not in st.session_state: st.session_state.inv_counter = 162084
if 'active_invoice' not in st.session_state: st.session_state.active_invoice = None

ref_data = pd.DataFrame([
    {"Clinic": "My Smile Family Dental", "Doctor": "Dr. Amhipreat Kaur", "Address": "13510 177 St NW, Edmonton, AB", "Phone": "(780) 455-6806", "Region": "Courier"},
    {"Clinic": "Calgary Central Dental", "Doctor": "Dr. Lana Huynh", "Address": "205-7136 11 St NE, Calgary, AB", "Phone": "(403) 970-0600", "Region": "Local"}
])

def get_business_day(start_date, days):
    curr = start_date
    while days > 0:
        curr -= timedelta(days=1)
        if curr.weekday() < 5: days -= 1
    return curr

# [3. 대시보드 실적 출력 (세전/세후 복구)]
total_count = len(st.session_state.db)
target = 320
total_pre_tax = total_count * PRE_TAX_UNIT
total_post_tax = total_count * POST_TAX_UNIT

st.markdown(f"""
    <div class="slim-dashboard">
        <div class="stat-group">
            <span class="stat-label">{current_month} 실적</span>
            <span class="stat-value">{total_count} / {target}</span>
            <span style="color: #ff4b4b; font-size: 0.9rem; font-weight: 600; margin-left:5px;">({total_count-target:+}개)</span>
        </div>
        <div style="display: flex;">
            <div class="money-badge" style="border-color: #555;">
                <span class="money-label-sub">PRE-TAX</span>
                <span class="money-text" style="color: #eee;">${total_pre_tax:,.2f}</span>
            </div>
            <div class="money-badge">
                <span class="money-label-sub" style="color: #4ade80;">AFTER-TAX</span>
                <span class="money-text">${total_post_tax:,.2f}</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# [4. 메인 탭 구성 (등록/리스트/검색)]
tab1, tab2, tab3 = st.tabs(["📝 등록", "📊 리스트", "🔍 검색"])

with tab1:
    st.markdown("### 📋 케이스 및 일정 등록")
    c1, c2 = st.columns(2)
    with c1:
        case_no = st.text_input("Case No")
        patient = st.text_input("Patient")
        cln = st.selectbox("Clinic", ["선택"] + sorted(ref_data["Clinic"].tolist()), key="sel_cln")
    with c2:
        mat = st.radio("Material", ["Thermo", "Dual", "Soft"], horizontal=True)
        arc = st.radio("Arch", ["UPPER", "LOWER", "BOTH"], horizontal=True)
        due = st.date_input("Due Date (요청일)", date.today() + timedelta(days=7))

    # 일정 자동 계산 로직
    ship_days = 1
    if cln != "선택":
        region = ref_data[ref_data["Clinic"] == cln]["Region"].iloc[0]
        ship_days = 1 if region == "Local" else 2
    
    ship_date = get_business_day(due, ship_days)
    done_date = get_business_day(ship_date, 1)

    col_a, col_b = st.columns(2)
    with col_a: st.date_input("Shipping Date (출고일)", value=ship_date)
    with col_b: st.date_input("Lab Done (완료일)", value=done_date)

    if st.button("💾 케이스 저장"):
        if cln != "선택" and case_no:
            info = ref_data[ref_data["Clinic"] == cln].iloc[0]
            st.session_state.db.append({
                "Inv_No": st.session_state.inv_counter, "Case No": case_no, "Patient": patient, 
                "Clinic": cln, "Doctor": info["Doctor"], "Address": info["Address"], 
                "Phone": info["Phone"], "Material": mat, "Arch": arc, 
                "Due": due, "Status": "진행중", "Date": date.today().strftime('%m/%d/%Y')
            })
            st.session_state.inv_counter += 1
            st.rerun()

with tab2:
    for i, row in enumerate(st.session_state.db):
        col_l, col_m, col_r = st.columns([3, 1, 1])
        col_l.write(f"**{row['Case No']}** | {row['Patient']} ({row['Clinic']})")
        col_m.write(f"Due: {row['Due']}")
        if col_r.button("🔍 Invoice", key=f"inv_{i}"): st.session_state.active_invoice = row

with tab3:
    st.markdown("### 🔍 케이스 검색")
    search_q = st.text_input("환자명 또는 케이스번호 입력")
    if search_q:
        filtered = [r for r in st.session_state.db if search_q.lower() in r['Patient'].lower() or search_q.lower() in r['Case No'].lower()]
        for f in filtered:
            st.write(f"✅ {f['Case No']} | {f['Patient']} | {f['Clinic']} (Due: {f['Due']})")

# [5. 인보이스 미리보기 영역]
if st.session_state.active_invoice:
    st.markdown('---')
    if st.button("❌ Close Preview"):
        st.session_state.active_invoice = None
        st.rerun()
    
    inv = st.session_state.active_invoice
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
                        <p style="margin:5px 0; font-size:12px;">No. {inv['Inv_No']} | {inv.get('Date', date.today().strftime('%m/%d/%Y'))}</p>
                        <div style="text-align:left; font-size:11px; border-top:1px solid #000; padding-top:5px; margin-top:10px;">
                            <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}
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
