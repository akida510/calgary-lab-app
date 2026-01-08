import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 제목 디자인
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">🦷 Skycad Lab Night Guard Manager</h1>
        <span style="font-size: 13px; font-weight: bold; color: #333;">Designed By Heechul Jung</span>
    </div>
    """,
    unsafe_allow_html=True
)

conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 세션 상태 관리 (새로고침 시 데이터 유지용)
if "it" not in st.session_state: 
    st.session_state.it = 0

i = st.session_state.it

# [함수] 주말 제외 영업일 기준 2일 전 계산
def get_working_day_minus_2(due_date):
    target = due_date
    count = 0
    while count < 2:
        target -= timedelta(days=1)
        if target.weekday() < 5:  # 월~금(0~4)
            count += 1
    return target

# 날짜 초기값 설정
if f"due{i}" not in st.session_state:
    st.session_state[f"due{i}"] = date.today() + timedelta(days=7)
if f"shp{i}" not in st.session_state:
    st.session_state[f"shp{i}"] = get_working_day_minus_2(st.session_state[f"due{i}"])

# 마감일 변경 시 출고일 자동 갱신 콜백
def sync_dates():
    st.session_state[f"shp{i}"] = get_working_day_minus_2(st.session_state[f"due{i}"])

def reset_fields():
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=1)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""]
        df = df.apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
# Reference 시트 로드 (Clinic별 Doctor 리스트용)
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key=f"c{i}")
    patient = c1.text_input("Patient", key=f"p{i}")
    
    # [Clinic 선택]
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic (병원명)", ["선택"] + cl_list + ["➕ 직접"], key=f"cl{i}")
    f_cl = c2.text_input("직접 입력 (Clinic)", key=f"fcl{i}") if sel_cl=="➕ 직접" else sel_cl
    
    # 💡 [핵심: 의사 필터링 로직]
    doc_opts = ["선택", "➕ 직접"]
    if sel_cl not in ["선택", "➕ 직접"]:
        # 선택된 Clinic에 해당하는 Doctor들만 가져오기 (Reference 시트 2번째 열 기준)
        filtered_docs = ref_df[ref_df.iloc[:,1] == sel_cl].iloc[:,2].unique()
        doc_opts += sorted([d for d in filtered_docs if d and str(d)!='nan'])
    
    sel_doc = c3.selectbox("Doctor (의사명)", doc_opts, key=f"d{i}")
    f_doc = c3.text_input("직접 입력 (Doctor)", key=f"fd{i}") if sel_doc=="➕ 직접" else sel_doc

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key=f"a{i}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"m{i}")
        qty = d1.number_input("Qty", 1, 10, 1, key=f"q{i}")
        
        is_33 = d2.checkbox("3D 스캔", True, key=f"3d{i}")
        rd = d2.date_input("접수일", date.today(), key=f"rd{i}", disabled=is_33)
        cp = d2.date_input("완료일", date.today()+timedelta(1), key=f"cd{i}")
        
        has_d = d2.checkbox("마감일/출고일 지정", True, key=f"h_d{i}")
        if has_d:
            # 마감일 변경 시 sync_dates 함수가 호출되어 출고일을 즉시 바꿈
            due = d3.date_input("마감일", key=f"due{i}", on_change=sync_dates)
            shp = d3.date_input("출고일 (자동계산됨)", key=f"shp{i}")
            s_t = d3.selectbox("⚠️ 시간", ["Noon","EOD","ASAP"], key=f"st_time{i}") if due==shp else ""
        else: due = shp = s_t = None
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st_stat{i}")

    with st.expander("✅ 기타 (체크리스트 & 사진)", expanded=True):
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))), key=f"ck{i}")
        up_img = st.file_uploader("📸 사진 업로드 (옵션)", type=['jpg', 'png', 'jpeg'], key=f"img{i}")
        memo = st.text_input("메모", key=f"me{i}")

    if st.button("🚀 데이터 저장", use_container_width=True, type="primary"):
        if not case_no or f_cl in ["선택", ""]:
            st.error("❌ Case #와 Clinic은 필수 항목입니다.")
        else:
            p_u = 180
            try:
                if sel_cl not in ["선택", "➕ 직접"]:
                    p_u = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
            except: p_u = 180
            
            dfmt = '%Y-%m-%d'
            notes_str = ", ".join(chks) + (f" | {memo}" if memo else "")
            row = {
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient,
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u*qty,
                "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                "Completed Date": cp.strftime(dfmt),
                "Shipping Date": (shp.strftime(dfmt) if shp else "-"),
                "Due Date": (due.strftime(dfmt) if due else "-"),
                "Status": stt, "Notes": notes_str
            }
            
            st.cache_data.clear()
            conn.update(data=pd.concat([m_df, pd.DataFrame([row])], ignore_index=True))
            st.success("✅ 저장 성공!"); time.sleep(1); reset_fields(); st.rerun()

# --- [TAB 2: 정산] ---
with t2:
    st.subheader("💰 기간별 정산 내역")
    today = date.today()
    c1, c2 = st.columns(2)
    sel_year = c1.selectbox("연도", range(today.year, today.year - 5, -1))
    sel_month = c2.selectbox("월", range(1, 13), index=today.month - 1)
    
    if not m_df.empty:
        pdf = m_df.copy()
        pdf['SD_dt'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD_dt'].dt.year == sel_year) & (pdf['SD_dt'].dt.month == sel_month)]
        if not m_dt.empty:
            v_df = m_dt[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']].copy()
            v_df.index = m_dt['Case #']; v_df.index.name = "Case #"
            st.dataframe(v_df, use_container_width=True)
            pay_dt = m_dt[m_dt['Status'].str.lower() == 'normal']
            total_qty = pd.to_numeric(pay_dt['Qty'], errors='coerce').sum()
            extra_qty = max(0, total_qty - 320)
            m1, m2, m3 = st.columns(3)
            m1.metric(f
