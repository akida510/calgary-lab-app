import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 디자인
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

# [함수] 주말(토,일) 제외 영업일 기준 2일 전 계산
def get_auto_shp_date(due):
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
    
    # 💡 [중요] st.form을 사용하여 입력 도중 새로고침과 에러 메시지 발생을 원천 차단합니다.
    with st.form("input_form", clear_on_submit=True):
        # [1단 배열]
        c1, c2, c3 = st.columns(3)
        case_no = c1.text_input("Case # (필수)")
        patient = c1.text_input("Patient")
        
        cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
        sel_cl = c2.selectbox("Clinic (필수)", ["선택"] + cl_list)
        
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
        
        due_date = d3.date_input("마감일", date.today() + timedelta(days=7))
        # 💡 출고일: 비워두면 자동 -2일(평일기준) 계산, 직접 고르면 그 날짜로 저장됩니다.
        shp_manual = d3.date_input("출고일 직접 수정 (필요할 때만 선택)", value=None)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"])

        st.markdown("---")
        
        # [3단 배열]
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))))
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'])
        memo = st.text_input("메모")

        st.markdown("<br>", unsafe_allow_html=True)
        # 🚀 폼 전송 버튼 (이걸 누를 때만 딱 한 번 검사합니다)
        submit = st.form_submit_button("🚀 데이터 저장 및 전송", use_container_width=True)

    # 저장 로직 (버튼 클릭 시에만 실행)
    if submit:
        if not case_no or sel_cl == "선택":
            st.error("❌ Case #와 Clinic은 필수 입력 항목입니다. 확인 후 다시 눌러주세요.")
        else:
            with st.spinner("저장 중..."):
                try:
                    p_u = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
                except: p_u = 180
                
                # 출고일 결정: 직접 수정한 게 있으면 그 값, 없으면 자동 -2일 계산
                final_shp = shp_manual if shp_manual is not None else get_auto_shp_date(due_date)
                
                dfmt = '%Y-%m-%d'
                row = {
                    "Case #": case_no.strip(), "Clinic": sel_cl, "Doctor": sel_doc, "Patient": patient.strip(),
                    "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u*qty,
                    "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                    "Completed Date": cp.strftime(dfmt),
                    "Shipping Date": final_shp.strftime(dfmt),
                    "Due Date": due_date.strftime(dfmt),
                    "Status": stt, "Notes": ", ".join(chks) + " | " + memo
                }
                st.cache_data.clear()
                conn.update(data=pd.concat([m_df, pd.DataFrame([row])], ignore_index=True))
                st.success("✅ 저장 성공! 목록을 새로고침합니다.")
                time.sleep(1)
                st.rerun()

# --- [정산/검색 탭 동일 유지] ---
with t2:
    st.subheader("💰 기간별 정산 내역")
    # (기존 정산 코드와 동일)
with t3:
    st.subheader("🔍 전체 데이터 검색")
    # (기존 검색 코드와 동일)
