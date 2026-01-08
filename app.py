import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 디자인 (절대 고정)
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
        if target.weekday() < 5: # 0:월 ~ 4:금
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
t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력")
    
    # [입력 1단] 세션 스테이트를 써서 새로고침 시 데이터 보존
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key="case_input")
    patient = c1.text_input("Patient", key="pat_input")
    
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic", ["선택"] + cl_list, key="cl_sel")
    
    doc_opts = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    sel_doc = c3.selectbox("Doctor", ["선택"] + doc_opts, key="doc_sel")

    st.markdown("---")
    
    # [입력 2단: 날짜 및 상세 설정]
    d1, d2, d3 = st.columns(3)
    arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key="arch_input")
    mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="mat_input")
    qty = d1.number_input("Qty", 1, 10, 1, key="qty_input")
    
    is_33 = d2.checkbox("3D 스캔 (접수일 제외)", True, key="33_input")
    rd = d2.date_input("접수일", date.today(), key="rd_input")
    cp = d2.date_input("완료일", date.today()+timedelta(1), key="cp_input")
    
    # 💡 마감일을 바꾸면 즉시 주말 제외 출고일을 계산해서 보여줌
    due_date = d3.date_input("마감일", date.today() + timedelta(days=7), key="due_input")
    
    # 마감일 기준으로 계산된 기본 출고일
    default_shp = get_shp_date(due_date)
    
    # 💡 출고일 입력창: 계산된 날짜가 기본으로 들어가지만, 직접 바꿀 수 있음!
    shp_date = d3.date_input("출고일 (자동계산됨 / 수정가능)", default_shp, key="shp_input")
    stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="stt_input")

    st.markdown("---")
    
    # [입력 3단: 디자인 유지]
    chk_raw = ref_df.iloc[:,3:].values.flatten()
    chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))), key="chk_input")
    up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'], key="img_input")
    memo = st.text_input("메모", key="memo_input")

    st.markdown("<br>", unsafe_allow_html=True)
    
    # 🚀 저장 버튼
    if st.button("🚀 데이터 저장 및 전송", use_container_width=True, type="primary"):
        # 최종 필수값 체크
        if not case_no or sel_cl == "선택":
            st.error("❌ Case #와 Clinic은 필수 입력 항목입니다.")
        else:
            with st.spinner("저장 중..."):
                try:
                    p_u = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
                except: p_u = 180
                
                dfmt = '%Y-%m-%d'
                row = {
                    "Case #": case_no.strip(), "Clinic": sel_cl, "Doctor": sel_doc, "Patient": patient.strip(),
                    "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u*qty,
                    "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                    "Completed Date": cp.strftime(dfmt),
                    "Shipping Date": shp_date.strftime(dfmt), # 계산됐거나 직접 수정한 날짜가 저장됨
                    "Due Date": due_date.strftime(dfmt),
                    "Status": stt, "Notes": ", ".join(chks) + " | " + memo
                }
                st.cache_data.clear()
                conn.update(data=pd.concat([m_df, pd.DataFrame([row])], ignore_index=True))
                st.success("✅ 저장 성공!")
                time.sleep(1)
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
