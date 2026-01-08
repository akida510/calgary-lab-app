import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 디자인 (절대 변경 없음)
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

# 2. 데이터 로딩 (정산/검색용 캐시 30초로 넉넉히 설정)
@st.cache_data(ttl=30)
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

# --- [TAB 1: 등록 (st.form 도입으로 새로고침 차단)] ---
with t1:
    st.subheader("📋 입력")
    
    # 💡 핵심 수정: 양식(form)으로 감싸서 저장 버튼 전까지 새로고침을 막음
    with st.form("input_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        case_no = c1.text_input("Case #")
        patient = c1.text_input("Patient")
        
        cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
        sel_cl = c2.selectbox("Clinic", ["선택"]+cl_list+["➕ 직접"])
        # 직접 입력 칸은 양식 내부의 일관성을 위해 아래 expander 등으로 옮기지 않고 유지
        f_cl_extra = c2.text_input("클리닉명 (직접입력 시)")
        
        doc_opts = ["선택","➕ 직접"]
        # 의사 목록은 클리닉 선택에 따라 바뀌어야 하므로 여기서는 전체 목록 혹은 직접 입력으로 유도
        sel_doc = c3.selectbox("Doctor", doc_opts)
        f_doc_extra = c3.text_input("의사명 (직접입력 시)")

        st.markdown("---")
        
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"])
        qty = d1.number_input("Qty", 1, 10, 1)
        
        is_33 = d2.checkbox("3D 스캔 (접수일 제외)", True)
        rd = d2.date_input("접수일", date.today())
        cp = d2.date_input("완료일", date.today()+timedelta(1))
        
        due_date = d3.date_input("마감일", date.today() + timedelta(days=7))
        shp_date = d3.date_input("출고일", date.today() + timedelta(days=5))
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"])

        st.markdown("---")
        
        # 체크리스트 및 기타
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))))
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'])
        memo = st.text_input("메모")

        # 폼 내부의 제출 버튼
        submit = st.form_submit_button("🚀 데이터 저장 및 전송", use_container_width=True)

    if submit:
        f_cl = f_cl_extra if sel_cl == "➕ 직접" else sel_cl
        f_doc = f_doc_extra if sel_doc == "➕ 직접" else sel_doc
        
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
                    "Shipping Date": shp_date.strftime(dfmt),
                    "Due Date": due_date.strftime(dfmt),
                    "Status": stt, "Notes": ", ".join(chks) + " | " + memo
                }
                st.cache_data.clear()
                conn.update(data=pd.concat([m_df, pd.DataFrame([row])], ignore_index=True))
                st.success("저장 성공!"); time.sleep(1); st.rerun()

# --- [TAB 2: 정산] (디자인 유지) ---
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
            v_df.index = m_dt['Case #']; v_df.index.name = "Case #"
            st.dataframe(v_df, use_container_width=True)
            pay_dt = m_dt[m_dt['Status'].str.lower() == 'normal']
            total_qty = pd.to_numeric(pay_dt['Qty'], errors='coerce').sum()
            extra_qty = max(0, total_qty - 320)
            m1, m2, m3 = st.columns(3)
            m1.metric(f"{sel_month}월 총 수량", f"{int(total_qty)} ea")
            m2.metric("엑스트라 수량", f"{int(extra_qty)} ea")
            m3.metric("엑스트라 금액", f"${extra_qty * 19.505333:,.2f}")

# --- [TAB 3: 검색] (디자인 유지) ---
with t3:
    st.subheader("🔍 전체 데이터 검색")
    qs = st.text_input("환자 이름 또는 Case # 입력", key="search_bar")
    if not m_df.empty:
        if qs:
            f_df = m_df[m_df['Case #'].str.contains(qs, case=False, na=False) | m_df['Patient'].str.contains(qs, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True)
        else:
            st.dataframe(m_df.tail(20), use_container_width=True)
