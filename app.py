import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정
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

# 2. 세션 상태 관리
if "it" not in st.session_state: 
    st.session_state.it = 0

i = st.session_state.it

# [함수] 주말 제외 영업일 기준 2일 전 계산
def get_working_day_minus_2(due_date):
    target = due_date
    count = 0
    while count < 2:
        target -= timedelta(days=1)
        if target.weekday() < 5: 
            count += 1
    return target

# 날짜 초기값 설정
if f"due{i}" not in st.session_state:
    st.session_state[f"due{i}"] = date.today() + timedelta(days=7)
if f"shp{i}" not in st.session_state:
    st.session_state[f"shp{i}"] = get_working_day_minus_2(st.session_state[f"due{i}"])

# 마감일 변경 시 출고일 자동 갱신
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
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    
    case_no = c1.text_input("Case # (필수)", key=f"c{i}")
    patient = c1.text_input("Patient", key=f"p{i}")
    
    # 💡 의사 선택 (이것만 선택해도 저장 가능하게!)
    all_docs = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    sel_doc = c3.selectbox("Doctor (의사 선택)", ["선택"] + all_docs + ["➕ 직접"], key=f"d{i}")
    f_doc = c3.text_input("직접 입력 (Doctor)", key=f"fd{i}") if sel_doc=="➕ 직접" else sel_doc
    
    # 의사 선택 시 병원 자동 찾기
    auto_clinic = ""
    if sel_doc not in ["선택", "➕ 직접"]:
        match = ref_df[ref_df.iloc[:, 2] == sel_doc]
        if not match.empty:
            auto_clinic = match.iloc[0, 1]

    # 병원 선택 (의사 선택 시 자동 매칭되지만, 몰라도 됨)
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    default_cl_idx = 0
    if auto_clinic in cl_list:
        default_cl_idx = cl_list.index(auto_clinic) + 1

    sel_cl = c2.selectbox("Clinic (모르면 건너뛰기 가능)", ["선택"] + cl_list + ["➕ 직접"], index=default_cl_idx, key=f"cl{i}")
    f_cl = c2.text_input("직접 입력 (Clinic)", key=f"fcl{i}") if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else auto_clinic)

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key=f"a{i}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"m{i}")
        qty = d1.number_input("Qty", 1, 10, 1, key=f"q{i}")
        is_33 = d2.checkbox("3D 스캔", True, key=f"3d{i}")
        rd = d2.date_input("접수일", date.today(), key=f"rd{i}", disabled=is_33)
        cp = d2.date_input("완료일", date.today()+timedelta(1), key=f"cd{i}")
        due = d3.date_input("마감일", key=f"due{i}", on_change=sync_dates)
        shp = d3.date_input("출고일", key=f"shp{i}")
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st_stat{i}")

    with st.expander("✅ 기타", expanded=True):
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))), key=f"ck{i}")
        memo = st.text_input("메모", key=f"me{i}")

    if st.button("🚀 데이터 저장", use_container_width=True, type="primary"):
        # 💡 [핵심 변경] Clinic(f_cl)이 없어도 의사(f_doc)만 있으면 통과!
        if not case_no:
            st.error("❌ Case #는 반드시 입력해야 합니다.")
        elif not f_doc or f_doc == "선택":
            st.error("❌ 의사 이름을 선택하거나 직접 입력해주세요.")
        else:
            p_u = 180
            # 병원명을 알면 단가 연동, 모르면 기본값 180
            try:
                if f_cl and f_cl != "선택":
                    p_match = ref_df[ref_df.iloc[:, 1] == f_cl]
                    if not p_match.empty:
                        p_u = int(float(p_match.iloc[0, 3]))
            except: p_u = 180
            
            dfmt = '%Y-%m-%d'
            row = {
                "Case #": case_no, 
                "Clinic": f_cl if f_cl != "선택" else "", # 병원명 모르면 빈칸으로 저장
                "Doctor": f_doc, 
                "Patient": patient,
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u*qty,
                "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                "Completed Date": cp.strftime(dfmt),
                "Shipping Date": shp.strftime(dfmt),
                "Due Date": due.strftime(
