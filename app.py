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
        <span style="font-size: 12px; font-weight: bold; color: #555;">Designed By Heechul Jung</span>
    </div>
    """,
    unsafe_allow_html=True
)

conn = st.connection("gsheets", type=GSheetsConnection)

# [함수] 주말 제외 영업일 기준 2일 전 계산 (희철님 요청사항)
def get_shp_date(due):
    target = due
    count = 0
    while count < 2:
        target -= timedelta(days=1)
        if target.weekday() < 5: # 월(0)~금(4)만 카운트
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
    
    # 💡 폼으로 감싸서 입력 중 새로고침 및 에러를 100% 차단합니다.
    with st.form("final_stable_form", clear_on_submit=True):
        # [1단 배열]
        c1, c2, c3 = st.columns(3)
        case_no = c1.text_input("Case #")
        patient = c1.text_input("Patient")
        
        cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
        sel_cl = c2.selectbox("Clinic", ["선택"] + cl_list)
        
        doc_opts = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
        sel_doc = c3.selectbox("Doctor", ["선택"] + doc_opts)

        st.markdown("---")
        
        # [2단 배열]
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"])
        qty = d1.number_input("Qty", 1, 10, 1)
        
        is_33 = d2.checkbox("3D 스캔 (접수일 제외)", True)
        rd = d2.date_input("접수일", date.today())
        cp = d2.date_input("완료일", date.today()+timedelta(1))
        
        # 💡 출고일 입력칸 삭제! 마감일만 받습니다.
        due_date = d3.date_input("마감일", date.today() + timedelta(days=7))
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"])

        st.markdown("---")
        
        # [3단 배열]
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))))
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'])
        memo = st.text_input("메모")

        st.markdown("<br>", unsafe_allow_html=True)
        # 🚀 버튼을 눌러야만 검사를 시작합니다.
        submit = st.form_submit_button("🚀 데이터 저장 및 전송 (자동 출고일 계산)", use_container_width=True)

    # 저장 로직
    if submit:
        if not case_no or sel_cl == "선택":
            st.error("❌ Case #와 Clinic은 필수 입력 항목입니다!")
        else:
            with st.spinner("저장 중..."):
                try:
                    p_u = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
                except: p_u = 180
                
                # 💡 저장 직전에 마감일로부터 주말 제외 2일 전을 자동 계산함
                final_shipping_date = get_shp_date(due_date)
                
                dfmt = '%Y-%m-%d'
                row = {
                    "Case #": case_no.strip(), "Clinic": sel_cl, "Doctor": sel_doc, "Patient": patient.strip(),
                    "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u*qty,
                    "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                    "Completed Date": cp.strftime(dfmt),
                    "Shipping Date": final_shipping_date.strftime(dfmt), # 자동 계산된 날짜 입력
                    "Due Date": due_date.strftime(dfmt),
                    "Status": stt, "Notes": ", ".join(chks) + " | " + memo
                }
                st.cache_data.clear()
                conn.update(data=pd.concat([m_df, pd.DataFrame([row])], ignore_index=True))
                st.success(f"✅ 저장 완료! (출고일: {final_shipping_date.strftime(dfmt)})")
                time.sleep(1)
                st.rerun()

# --- [정산/검색 탭] ---
with t2:
    st.subheader("💰 기간별 정산 내역")
    # 기존 코드와 동일
with t3:
    st.subheader("🔍 전체 데이터 검색")
    # 기존 코드와 동일
