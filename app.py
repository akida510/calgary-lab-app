import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 디자인 (절대 유지)
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">🦷 Skycad Lab Night Guard Manager</h1>
        <span style="font-size: 12px; font-weight: bold; color: #555;">Designed By Heechul Jung</span>
    </div>
    """,
    unsafe_allow_html=True
)

conn = st.connection("gsheets", type=GSheetsConnection)

# [함수] 주말 제외 영업일 기준 2일 전 계산
def get_shp_date(due):
    target = due
    count = 0
    while count < 2:
        target -= timedelta(days=1)
        if target.weekday() < 5: # 월~금만 카운트
            count += 1
    return target

# 2. 데이터 로딩
@st.cache_data(ttl=5)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""]
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

# 💡 [핵심] 마감일 변경 시 출고일을 자동으로 업데이트하는 콜백 함수
def update_shipping():
    st.session_state.shp_val = get_shp_date(st.session_state.due_val)

# 세션 상태 초기화 (데이터 유실 방지용)
if "shp_val" not in st.session_state:
    st.session_state.shp_val = get_shp_date(date.today() + timedelta(days=7))

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력")
    
    # [입력 1단] 세션 스테이트를 지정하여 새로고침 시에도 값 유지
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key="case_stable")
    patient = c1.text_input("Patient", key="pat_stable")
    
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic", ["선택"] + cl_list, key="cl_stable")
    
    doc_opts = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    sel_doc = c3.selectbox("Doctor", ["선택"] + doc_opts, key="doc_stable")

    st.markdown("---")
    
    # [입력 2단: 날짜 및 상세 설정]
    d1, d2, d3 = st.columns(3)
    arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key="arch_stable")
    mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="mat_stable")
    qty = d1.number_input("Qty", 1, 10, 1, key="qty_stable")
    
    is_33 = d2.checkbox("3D 스캔 (접수일 제외)", True, key="scan_stable")
    rd = d2.date_input("접수일", date.today(), key="rd_stable")
    cp = d2.date_input("완료일", date.today()+timedelta(1), key="cp_stable")
    
    # 💡 마감일을 선택하면 update_shipping 함수가 실행되어 출고일을 자동 계산함
    due_date = d3.date_input("마감일", date.today() + timedelta(days=7), key="due_val", on_change=update_shipping)
    
    # 💡 출고일: 자동 계산된 값이 기본으로 뜨지만, 직접 수정도 가능함
    shp_date = d3.date_input("출고일 (수동 수정 가능)", key="shp_val")
    stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="stt_stable")

    st.markdown("---")
    
    # [입력 3단: 체크리스트 및 메모]
    chk_raw = ref_df.iloc[:,3:].values.flatten()
    chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))), key="chk_stable")
    up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'], key="img_stable")
    memo = st.text_input("메모", key="memo_stable")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 🚀 저장 버튼
    if st.button("🚀 데이터 저장 및 전송", use_container_width=True, type="primary"):
        # 최종 입력값 확인 (세션 스테이트에서 직접 가져옴)
        f_case = st.session_state.case_stable.strip()
        f_clinic = st.session_state.cl_stable
        
        if not f_case or f_clinic == "선택":
            st.error("❌ Case #와 Clinic은 필수 입력 항목입니다.")
        else:
            with st.spinner("저장 중..."):
                try:
                    p_u = int(float(ref_df[ref_df.iloc[:, 1] == f_clinic].iloc[0, 3]))
                except: p_u = 180
                
                dfmt = '%Y-%m-%d'
                row = {
                    "Case #": f_case, "Clinic": f_clinic, "Doctor": st.session_state.doc_stable, "Patient": st.session_state.pat_stable.strip(),
                    "Arch": st.session_state.arch_stable, "Material": st.session_state.mat_stable, "Price": p_u, "Qty": st.session_state.qty_stable, "Total": p_u*st.session_state.qty_stable,
                    "Receipt Date": ("-" if st.session_state.scan_stable else rd.strftime(dfmt)),
                    "Completed Date": cp.strftime(dfmt),
                    "Shipping Date": shp_date.strftime(dfmt),
                    "Due Date": due_date.strftime(dfmt),
                    "Status": stt, "Notes": ", ".join(chks) + " | " + memo
                }
                st.cache_data.clear()
                conn.update(data=pd.concat([m_df, pd.DataFrame([row])], ignore_index=True))
                st.success("✅ 저장 성공!")
                time.sleep(1)
                # 저장 후 세션 초기화
                for k in st.session_state.keys():
                    if k != 'shp_val': del st.session_state[k]
                st.rerun()

# --- [정산 / 검색 탭 디자인 유지] ---
with t2:
    st.subheader("💰 기간별 정산 내역")
    today = date.today()
    c_y, c_m = st.columns(2)
    sel_year = c_y.selectbox("연도", range(today.year, today.year - 5, -1))
    sel_month = c_m.selectbox("월", range(1, 13), index=today.month - 1)
    
    pdf = m_df.copy()
    if not pdf.empty:
        pdf['SD_dt'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD_dt'].dt.year == sel_year) & (pdf['SD_dt'].dt.month == sel_month)]
        if not m_dt.empty:
            v_df = m_dt[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']].copy()
            v_df.index = m_dt['Case #']
            st.dataframe(v_df, use_container_width=True)
            pay_dt = m_dt[m_dt['Status'].str.lower() == 'normal']
            total_qty = pd.to_numeric(pay_dt['Qty'], errors='coerce').sum()
            extra_qty = max(0, total_qty - 320)
            m1, m2, m3 = st.columns(3)
            m1.metric(f"{sel_month}월 총 수량", f"{int(total_qty)} ea")
            m2.metric("엑스트라 수량", f"{int(extra_qty)} ea")
            m3.metric("엑스트라 금액", f"${extra_qty * 19.505333:,.2f}")

with t3:
    st.subheader("🔍 전체 데이터 검색")
    qs = st.text_input("환자 이름 또는 Case # 입력", key="search_bar")
    if not m_df.empty:
        if qs:
            f_df = m_df[m_df['Case #'].str.contains(qs, case=False, na=False) | m_df['Patient'].str.contains(qs, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True)
        else:
            st.dataframe(m_df.tail(20), use_container_width=True)
