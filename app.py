import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 제작자 정보 고정 (디자인 절대 유지)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">🦷 Skycad Lab Night Guard Manager</h1>
        <span style="font-size: 14px; font-weight: bold; color: #555;">Designed By Heechul Jung</span>
    </div>
    <hr style="margin-top: 0; margin-bottom: 20px;">
    """,
    unsafe_allow_html=True
)

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 관리
if "it" not in st.session_state:
    st.session_state.it = 0
iter_no = str(st.session_state.it)

# [함수] 주말 제외 2일 전 계산 (영업일 기준)
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

# 날짜 초기값 및 동기화 설정
if "due" + iter_no not in st.session_state:
    st.session_state["due" + iter_no] = date.today() + timedelta(days=7)
if "shp" + iter_no not in st.session_state:
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

def sync():
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

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key="c" + iter_no)
    patient = c1.text_input("Patient", key="p" + iter_no)
    
    # 의사 리스트 및 선택
    docs = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    sel_doc = c3.selectbox("Doctor (의사)", ["선택"] + docs + ["➕ 직접"], key="sd" + iter_no)
    f_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else sel_doc
    
    # 💡 의사 선택 시 해당 병원 자동 매칭 로직
    auto_cl = ""
    if sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty:
            auto_cl = match.iloc[0, 1]

    # 병원 선택창 (의사로 병원이 매칭되면 자동 선택)
    clinics = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    cl_idx = clinics.index(auto_cl) + 1 if auto_cl in clinics else 0
    sel_cl = c2.selectbox("Clinic (병원)", ["선택"] + clinics + ["➕ 직접"], index=cl_idx, key="sc" + iter_no)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else auto_cl)

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy" + iter_no)
        is_33 = d2.checkbox("3D Scan", True, key="d3" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no, disabled=is_33)
        cp = d2.date_input("완료일", date.today()+timedelta(1), key="cp" + iter_no)
        # 💡 출고일 자동계산 주말 제외 동기화
        due_val = d3.date_input("마감일", key="due" + iter_no, on_change=sync)
        shp_val = d3.date_input("출고일", key="shp" + iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("✅ 기타", expanded=True):
        col_ex1, col_ex2 = st.columns(2)
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            ch_r = ref.iloc[:,3:].values.flatten()
            chks_list = sorted(list(set([str(x) for x in ch_r if x and str(x)!='nan'])))
            chks = col_ex1.multiselect("체크리스트", chks_list, key="ck" + iter_no)
        
        # 💡 사진 입력창 복구
        img_link = col_ex1.text_input("사진/링크", key="img" + iter_no)
        memo = col_ex2.text_area("메모", key="me" + iter_no, height=100)

    if st.button("🚀 데이터 저장", use_container_width=True, type="primary"):
        if not case_no or f_doc in ["선택", ""]:
            st.error("❌ Case #와 Doctor는 필수입니다.")
        else:
            p_u = 180
            if f_cl and f_cl != "선택" and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == f_cl]
                if not p_m.empty:
                    try: p_u = int(float(p_m.iloc[0, 3]))
                    except: p_u = 180
            
            dt_fmt = '%Y-%m-%d'
            # 메모와 사진 링크 합치기
            final_notes = ", ".join(chks)
            if img_link: final_notes += f" | 사진: {img_link}"
            if memo: final_notes += f" | {memo}"

            new_row = {
                "Case #": case_no, "Clinic": f_cl if f_cl != "선택" else "",
                "Doctor": f_doc, "Patient": patient, "Arch": arch, "Material": mat,
                "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": "-" if is_33 else rd.strftime(dt_fmt),
                "Completed Date": cp.strftime(dt_fmt),
                "Shipping Date": shp_val.strftime(dt_fmt),
                "Due Date": due_val.strftime(dt_fmt),
                "Status": stt, "Notes": final_notes
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("✅ 저장 성공!")
            time.sleep(1)
            reset_all()
            st.rerun()

# --- [정산 및 검색 탭 - 디자인 유지] ---
with t2:
    st.subheader("💰 정산")
    today_dt = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("연도", range(today_dt.year, today_dt.year - 5, -1))
    s_m = sm.selectbox("월", range(1, 13), index=today_dt.month - 1)
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['SD'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD'].dt.year == s_y) & (pdf['SD'].dt.month == s_m)]
        if not m_dt.empty:
            cols = ['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']
            st.dataframe(m_dt[cols], use_container_width=True, hide_index=True)
            pay = m_dt[m_dt['Status'].str.lower() == 'normal']
            tot = pd.to_numeric(pay['Qty'], errors='coerce').sum()
            st.metric("총 수량", str(int(tot)) + " ea")

with t3:
    st.subheader("🔍 검색")
    q_s = st.text_input("검색어", key="search_box")
    if not main_df.empty:
        if q_s:
            f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True, hide_index=True)
        else: st.dataframe(main_df.tail(20), use_container_width=True, hide_index=True)
