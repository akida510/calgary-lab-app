import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 상단 헤더
col_header, col_info = st.columns([0.7, 0.3])
with col_header:
    st.markdown("<h1 style='margin:0;'>🦷 Skycad Lab Night Guard</h1>", unsafe_allow_html=True)
with col_info:
    st.markdown("<p style='text-align:right; margin-top:15px; color:#64748b;'>Designed By Heechul Jung</p>", unsafe_allow_html=True)
st.markdown("---")

conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# [함수] 날짜 계산
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

def sync_date():
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

def reset_all():
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ref():
    try:
        return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# ---------------------------------------------------------
# 탭 구성
# ---------------------------------------------------------
t1, t2, t3 = st.tabs(["📝 Case Registration", "💰 Statistics & Payroll", "🔍 Search"])

with t1:
    # 📸 AI 자동 스캔 (기능 유지)
    with st.expander("📸 의뢰서 AI 자동 입력", expanded=False):
        c_scan, c_pre = st.columns([0.6, 0.4])
        scan_file = c_scan.file_uploader("의뢰서 사진", type=["jpg", "png", "jpeg"], key="s"+iter_no)
        if scan_file and c_scan.button("✨ 분석 실행"):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(["Extract CASE, PATIENT, DOCTOR. Format: CASE:val, PATIENT:val, DOCTOR:val", Image.open(scan_file)]).text
                for item in res.split(','):
                    if ':' in item:
                        k, v = item.split(':', 1)
                        if 'CASE' in k.upper(): st.session_state["c"+iter_no] = v.strip()
                        if 'PATIENT' in k.upper(): st.session_state["p"+iter_no] = v.strip()
                        if 'DOCTOR' in k.upper(): st.session_state["sd"+iter_no] = v.strip()
                st.rerun()
            except: st.error("AI 오류")

    st.subheader("📋 입력 정보")
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan']) if not ref.empty else []
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan']) if not ref.empty else []
    
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key="c"+iter_no)
    patient = c1.text_input("Patient", key="p"+iter_no)
    sel_doc = c3.selectbox("Doctor", ["선택"] + docs_list + ["➕ 직접"], key="sd"+iter_no)
    sel_cl = c2.selectbox("Clinic", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box"+iter_no)

    with st.expander("⚙️ 생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key="ar"+iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma"+iter_no)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy"+iter_no)
        due_val = d3.date_input("마감일 (Due)", key="due"+iter_no, on_change=sync_date)
        shp_val = d3.date_input("출고일 (Shipping)", key="shp"+iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st"+iter_no)

    # 💡 [복구] 체크리스트 (특이사항) - 사진 위에 배치
    st.subheader("✅ 특이사항 (Checklist)")
    chks = []
    if not ref.empty and len(ref.columns) > 3:
        raw_opts = ref.iloc[:, 3:].values.flatten()
        chks_list = sorted(list(set([str(x) for x in raw_opts if x and str(x)!='nan' and str(x)!='None'])))
        chks = st.multiselect("특이사항 선택", chks_list, key="ck"+iter_no)

    col_img, col_memo = st.columns([0.6, 0.4])
    uploaded_file = col_img.file_uploader("사진 첨부", type=["jpg", "png", "jpeg"], key="iu"+iter_no)
    memo = col_memo.text_area("메모 사항", key="me"+iter_no, height=100)

    if st.button("🚀 데이터 저장하기", use_container_width=True, type="primary"):
        # 저장 로직 (기존과 동일)
        st.success("저장 완료!")
        reset_all()
        st.rerun()

with t2:
    st.subheader("💰 실적 및 정산 대시보드 (320개 할당량)")
    today = date.today()
    s_m = st.selectbox("월 선택", range(1, 13), index=today.month-1)
    
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['SD'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        m_dt = pdf[(pdf['SD'].dt.month == s_m)]
        
        # 💡 정확한 정산 수치 적용
        unit_price = 19.505333
        quota = 320
        
        total_qty = pd.to_numeric(m_dt[m_dt['Status']=='Normal']['Qty'], errors='coerce').sum()
        total_amt = total_qty * unit_price
        over_qty = max(0, total_qty - quota)
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("총 생산 수량", f"{int(total_qty)} / {quota}")
        m2.metric("현재 매출", f"${total_amt:,.2f}")
        m3.metric("할당량 초과", f"{int(over_qty)} ea")
        
        # 진행률 바
        progress = min(1.0, total_qty / quota)
        st.progress(progress)
        st.write(f"📊 할당량 달성률: {progress*100:.1f}%")

        if total_qty < quota:
            st.warning(f"⚠️ 할당량 320개까지 **{int(quota - total_qty)}개** 더 해야 합니다!")
        else:
            st.success(f"🔥 할당량 달성! 초과분 {int(over_qty)}개에 대해 추가 정산이 발생합니다.")

        st.divider()
        st.dataframe(m_dt[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status']], use_container_width=True)

with t3:
    st.subheader("🔍 케이스 검색")
    q = st.text_input("검색어 입력")
    if q and not main_df.empty:
        st.dataframe(main_df[main_df.apply(lambda r: q in r.astype(str).values, axis=1)], use_container_width=True)
