import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 디자인 유지 (절대 유지)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .stHeader { background-color: #1e293b; color: white; padding: 1.5rem; border-radius: 10px; margin-bottom: 2rem; }
    .footer { text-align: right; font-size: 14px; font-weight: bold; color: #64748b; }
    </style>
    """, unsafe_allow_html=True)

# 제작자 정보 상단 고정
col_header, col_info = st.columns([0.7, 0.3])
with col_header:
    st.markdown("<h1 style='margin:0;'>🦷 Skycad Lab Night Guard</h1>", unsafe_allow_html=True)
with col_info:
    st.markdown("<p style='text-align:right; margin-top:15px; color:#64748b;'>Designed By Heechul Jung</p>", unsafe_allow_html=True)
st.markdown("---")

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 관리
if "it" not in st.session_state:
    st.session_state.it = 0
iter_no = str(st.session_state.it)

# [함수] 주말 제외 2일 전 계산
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

# 날짜 동기화
def sync_date():
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

if "due" + iter_no not in st.session_state:
    st.session_state["due" + iter_no] = date.today() + timedelta(days=7)
if "shp" + iter_no not in st.session_state:
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
    except Exception:
        return pd.DataFrame(columns=["Clinic", "Doctor", "Price"])

main_df = get_data()
ref = get_ref()

t1, t2, t3 = st.tabs(["📝 Case Registration", "💰 Statistics", "🔍 Search"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력 정보")
    
    # 레퍼런스 데이터 정리
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    
    # 💡 [핵심수정] 의사 선택을 먼저 배치하여 아래 병원 창이 참조할 수 있게 함
    top_c1, top_c2 = st.columns([0.66, 0.33])
    with top_c2:
        sel_doc = st.selectbox("Doctor", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no)
        f_doc = st.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else sel_doc

    # 매칭 로직 (의사 선택 즉시 실행)
    cl_idx = 0
    matched_cl_name = ""
    if sel_doc not in ["선택", "➕ 직접"]:
        match_row = ref[ref.iloc[:, 2] == sel_doc]
        if not match_row.empty:
            matched_cl_name = match_row.iloc[0, 1]
            if matched_cl_name in clinics_list:
                cl_idx = clinics_list.index(matched_cl_name) + 1

    # 나머지 입력 칸 배치
    with top_c1:
        c1_sub, c2_sub = st.columns(2)
        case_no = c1_sub.text_input("Case #", key="c" + iter_no)
        patient = c1_sub.text_input("Patient", key="p" + iter_no)
        
        # 병원 선택 (의사에 의해 cl_idx가 결정됨)
        sel_cl = c2_sub.selectbox("Clinic", ["선택"] + clinics_list + ["➕ 직접"], index=cl_idx, key="sc_box" + iter_no)
        f_cl = c2_sub.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else matched_cl_name)

    # --- 기존 설정 및 디자인 그대로 유지 ---
    with st.expander("⚙️ 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy" + iter_no)
        is_33 = d2.checkbox("3D Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no, disabled=is_33)
        cp = d2.date_input("완료예정일", date.today()+timedelta(1), key="cp" + iter_no)
        due_val = d3.date_input("마감일 (Due)", key="due" + iter_no, on_change=sync_date)
        shp_val = d3.date_input("출고일 (Shipping)", key="shp" + iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("✅ 기타 및 사진 첨부", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            ch_r = ref.iloc[:,3:].values.flatten()
            chks_list = sorted(list(set([str(x) for x in ch_r if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("특이사항 선택", chks_list, key="ck" + iter_no)
        
        uploaded_file = col_ex1.file_uploader("사진 첨부 (JPG, PNG)", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = col_ex2.text_area("메모 사항", key="me" + iter_no, height=130)

    if st.button("🚀 데이터 저장하기", use_container_width=True, type="primary"):
        if not case_no or f_doc in ["선택", ""]:
            st.error("❌ 필수 정보를 입력해주세요 (Case #, Doctor)")
        else:
            p_u = 180
            final_cl = f_cl if f_cl != "선택" else ""
            if final_cl and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == final_cl]
                if not p_m.empty:
                    try: p_u = int(float(p_m.iloc[0, 3]))
                    except: p_u = 180
            
            dt_fmt = '%Y-%m-%d'
            final_notes = ", ".join(chks)
            if uploaded_file: final_notes += f" | 사진: {uploaded_file.name}"
            if memo: final_notes += f" | {memo}"

            new_row = {
                "Case #": case_no, "Clinic": final_cl, "Doctor": f_doc, "Patient": patient, 
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": "-" if is_33 else rd.strftime(dt_fmt),
                "Completed Date": cp.strftime(dt_fmt),
                "Shipping Date": shp_val.strftime(dt_fmt),
                "Due Date": due_val.strftime(dt_fmt),
                "Status": stt, "Notes": final_notes
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("✅ 저장이 완료되었습니다!")
            time.sleep(1)
            reset_all()
            st.rerun()

# --- 정산 및 검색 (디자인 유지) ---
with t2:
    st.subheader("💰 월간 정산 내역")
    today_dt = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("연도", range(today_dt.year, today_dt.year - 5, -1))
    s_m = sm.selectbox("월", range(1, 13), index=today_dt.month - 1)
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['SD'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD'].dt.year == s_y) & (pdf['SD'].dt.month == s_m)]
        if not m_dt.empty:
            st.dataframe(m_dt[['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']], use_container_width=True, hide_index=True)
            pay = m_dt[m_dt['Status'].str.lower() == 'normal']
            tot = pd.to_numeric(pay['Qty'], errors='coerce').sum()
            st.metric("Total Quantity", f"{int(tot)} ea")

with t3:
    st.subheader("🔍 케이스 검색")
    q_s = st.text_input("케이스 번호 또는 환자명 입력", key="search_box")
    if not main_df.empty:
        if q_s:
            f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True, hide_index=True)
        else: st.dataframe(main_df.tail(20), use_container_width=True, hide_index=True)
