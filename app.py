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

# 2. 데이터 로딩 (안정적인 30초 캐시)
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

# --- [TAB 1: 등록 (중복 체크 및 하위 메뉴 로직)] ---
with t1:
    st.subheader("📋 입력")
    
    with st.form("input_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        case_no = c1.text_input("Case #")
        patient = c1.text_input("Patient")
        
        # 클리닉 선택 및 직접 입력 하위 메뉴
        cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
        sel_cl = c2.selectbox("Clinic", ["선택"] + cl_list + ["➕ 직접"])
        f_cl_input = ""
        if sel_cl == "➕ 직접":
            f_cl_input = c2.text_input("👉 클리닉 이름 입력")
        
        # 의사 선택 및 직접 입력 하위 메뉴
        doc_opts = ["선택", "➕ 직접"]
        if sel_cl not in ["선택", "➕ 직접"]:
            docs = ref_df[ref_df.iloc[:,1] == sel_cl].iloc[:,2].unique()
            doc_opts += sorted([d for d in docs if d and str(d)!='nan'])
        sel_doc = c3.selectbox("Doctor", doc_opts)
        f_doc_input = ""
        if sel_doc == "➕ 직접":
            f_doc_input = c3.text_input("👉 의사 이름 입력")

        st.markdown("---")
        
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"])
        qty = d1.number_input("Qty", 1, 10, 1)
        
        is_33 = d2.checkbox("3D 스캔 (접수일 제외)", True)
        rd = d2.date_input("접수일", date.today())
        cp = d2.date_input("완료일", date.today()+timedelta(1))
        
        due_date = d3.date_input("마감일", date.today() + timedelta(days=7))
        shp_date = d3.date_input("출고일", due_date - timedelta(days=2))
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"])

        st.markdown("---")
        
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))))
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'])
        memo = st.text_input("메모")

        submit = st.form_submit_button("🚀 데이터 저장 및 전송", use_container_width=True)

    if submit:
        final_cl = f_cl_input if sel_cl == "➕ 직접" else sel_cl
        final_doc = f_doc_input if sel_doc == "➕ 직접" else sel_doc
        
        if not case_no or final_cl in ["선택", ""]:
            st.error("Case #와 Clinic은 필수 입력 항목입니다.")
        else:
            # 중복 체크 로직
            duplicate = m_df[(m_df['Case #'] == case_no.strip()) & (m_df['Patient'] == patient.strip())]
            if not duplicate.empty:
                st.warning(f"⚠️ 중복 데이터 발견! Case #{case_no}, 환자명 {patient} 데이터가 이미 존재합니다.")
            else:
                with st.spinner("저장 중..."):
                    p_u = 180
                    try:
                        if sel_cl not in ["선택", "➕ 직접"]:
                            p_u = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
                    except: p_u = 180
                    
                    dfmt = '%Y-%m-%d'
                    row = {
                        "Case #": case_no.strip(), "Clinic": final_cl, "Doctor": final_doc, "Patient": patient.strip(),
                        "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u*qty,
                        "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                        "Completed Date": cp.strftime(dfmt),
                        "Shipping Date": shp_date.strftime(dfmt),
                        "Due Date": due_date.strftime(dfmt),
                        "Status": stt, "Notes": ", ".join(ch
