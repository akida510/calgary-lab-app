import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 디자인 (제목 우측 제작자 표시 유지)
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

# 2. 세션 상태 관리 (입력 튕김 방지용 reset_key)
if "reset_key" not in st.session_state:
    st.session_state.reset_key = 0

# 3. 데이터 로딩 (에러 방지용 10초 캐시)
@st.cache_data(ttl=10)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""]
        df = df.apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key=f"case_{st.session_state.reset_key}")
    patient = c1.text_input("Patient", key=f"pat_{st.session_state.reset_key}")
    
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic", ["선택"]+cl_list+["➕ 직접"], key=f"cl_{st.session_state.reset_key}")
    f_cl = c2.text_input("클리닉명 (직접입력 시)", key=f"fcl_{st.session_state.reset_key}") if sel_cl=="➕ 직접" else sel_cl
    
    doc_opts = ["선택","➕ 직접"]
    if sel_cl not in ["선택","➕ 직접"]:
        docs = ref_df[ref_df.iloc[:,1]==sel_cl].iloc[:,2].unique()
        doc_opts += sorted([d for d in docs if d and str(d)!='nan'])
    sel_doc = c3.selectbox("Doctor", doc_opts, key=f"doc_{st.session_state.reset_key}")
    f_doc = c3.text_input("의사명 (직접입력 시)", key=f"fdoc_{st.session_state.reset_key}") if sel_doc=="➕ 직접" else sel_doc

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key=f"arch_{st.session_state.reset_key}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"mat_{st.session_state.reset_key}")
        qty = d1.number_input("Qty", 1, 10, 1, key=f"qty_{st.session_state.reset_key}")
        is_33 = d2.checkbox("3D 스캔", True, key=f"scan_{st.session_state.reset_key}")
        rd = d2.date_input("접수일", date.today(), disabled=is_33, key=f"rd_{st.session_state.reset_key}")
        cp = d2.date_input("완료일", date.today()+timedelta(1), key=f"cp_{st.session_state.reset_key}")
        
        if d2.checkbox("마감일/출고일 지정", True, key=f"h_d_{st.session_state.reset_key}"):
            due_date = d3.date_input("마감일", date.today() + timedelta(days=7), key=f"due_{st.session_state.reset_key}")
            shp_date = d3.date_input("출고일", due_date - timedelta(days=2), key=f"shp_{st.session_state.reset_key}")
            s_t = d3.selectbox("⚠️ 시간", ["Noon","EOD","ASAP"], key=f"st_{st.session_state.reset_key}") if due_date == shp_date else ""
        else: due_date = shp_date = s_t = None
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"stat_{st.session_state.reset_key}")

    with st.expander("✅ 기타 (체크리스트 & 사진)", expanded=True):
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))), key=f"chk_{st.session_state.reset_key}")
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'], key=f"img_{st.session_state.reset_key}")
        memo = st.text_input("메모", key=f"memo_{st.session_state.reset_key}")

    # 💡 SyntaxError 수정: st.button의 괄호를 정확히 닫음
    if st.button("🚀 데이터 저장", use_container_width=True):
        if not case_no or f_cl in ["선택", ""]:
            st.error("Case #와 Clinic은 필수 입력 항목입니다.")
        else:
            with st.spinner("저장 중..."):
                p_u = 180
                try:
                    if sel_cl not in ["선택", "➕ 직접"]:
                        p_u = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
                except: p_u = 180
                dfmt = '%Y-%m-%d'
                row = {
                    "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient,
                    "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u*qty,
                    "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                    "Completed Date": cp.strftime(dfmt),
                    "Shipping Date": (shp_date.strftime(dfmt) if shp_date else "-"),
                    "Due Date": (due_date.strftime(dfmt) if due_date else "-"),
                    "Status": stt, "Notes": ", ".join(chks) + " | " + memo
                }
                st.cache_data.clear()
                conn.update(data=pd.concat([m_df, pd.DataFrame([row])], ignore_index=True))
                st.session_state.reset_key += 1
                st.success("저장 성공!"); time.sleep(1); st.rerun()

# --- [TAB 2: 정산] ---
with t2:
    st.subheader("💰 기간별 정산 내역")
    today = date.today()
    c_y, c_m = st.columns(2)
    sel_year = c_y.selectbox("연도", range(today.year, today.year - 5, -1))
    sel_month = c_m.selectbox("월", range(1, 13), index=today.month - 1)
    
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
            m1.metric(f"{sel_month}월 총 수량", f"{int(total_qty)} ea")
            m2.metric("엑스트라 수량", f"{int(extra_qty)} ea")
            m3.metric("엑스트라 금액", f"${extra_qty * 19.505333:,.2f}")

# --- [TAB 3: 검색] ---
with t3:
    st.subheader("🔍 전체 데이터 검색")
    qs = st.text_input("환자 이름 또는 Case # 입력", key="search_bar")
    if not m_df.empty:
        if qs:
            f_df = m_df[m_df['Case #'].str.contains(qs, case=False, na=False) | m_df['Patient'].str.contains(qs, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True)
        else:
            st.dataframe(m_df.tail(20), use_container_width=True)
