import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

st.set_page_config(page_title="Skycad Lab", layout="wide")
st.write("### 🦷 Skycad Lab Manager")

conn = st.connection("gsheets", type=GSheetsConnection)

# 1. 초기화 로직: 입력창을 비우기 위한 세션 상태 관리
if "it" not in st.session_state: 
    st.session_state.it = 0

def reset_fields():
    """입력창 위젯의 키값들을 초기화하기 위해 인덱스를 증가시킴"""
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=2)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""]
        df = df[df['Case #'].str.lower() != "nan"]
        df = df.apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    # it 번호가 바뀌면 모든 위젯이 새롭게 생성되어 빈 칸이 됩니다.
    i = st.session_state.it
    st.subheader("📋 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key=f"c{i}")
    patient = c1.text_input("Patient", key=f"p{i}")
    
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic", ["선택"]+cl_list+["➕ 직접"], key=f"cl{i}")
    f_cl = c2.text_input("클리닉명", key=f"fcl{i}") if sel_cl=="➕ 직접" else sel_cl
    
    doc_opts = ["선택","➕ 직접"]
    if sel_cl not in ["선택","➕ 직접"]:
        docs = ref_df[ref_df.iloc[:,1]==sel_cl].iloc[:,2].unique()
        doc_opts += sorted([d for d in docs if d and str(d)!='nan'])
    sel_doc = c3.selectbox("Doctor", doc_opts, key=f"d{i}")
    f_doc = c3.text_input("의사명", key=f"fd{i}") if sel_doc=="➕ 직접" else sel_doc

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
            due = d3.date_input("마감일", key=f"due{i}")
            shp = d3.date_input("출고일", key=f"shp{i}")
            s_t = d3.selectbox("⚠️ 시간", ["Noon","EOD","ASAP"], key=f"st_time{i}") if due==shp else ""
        else: due = shp = s_t = None
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st_stat{i}")

    with st.expander("✅ 기타", expanded=True):
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))), key=f"ck{i}")
        memo = st.text_input("메모", key=f"me{i}")

    if st.button("🚀 데이터 저장", use_container_width=True):
        if not case_no or f_cl in ["선택", ""]: st.error("정보 부족")
        else:
            try:
                p_u = 180
                if sel_cl not in ["선택", "➕ 직접"]:
                    p_u = int(float(ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[0, 3]))
            except: p_u = 180
            dfmt = '%Y-%m-%d'
            frd, fcp = ("-" if is_33 else rd.strftime(dfmt)), cp.strftime(dfmt)
            fdue = due.strftime(dfmt) if has_d else "-"
            fshp = shp.strftime(dfmt) if has_d else "-"
            if has_d and s_t: fshp = f"{fshp} {s_t}"
            row = {"Case #":case_no,"Clinic":f_cl,"Doctor":f_doc,"Patient":patient,"Arch":arch,"Material":mat,"Price":p_u,"Qty":qty,"Total":p_u*qty,"Receipt Date":frd,"Completed Date":fcp,"Shipping Date":fshp,"Due Date":fdue,"Status":stt,"Notes":", ".join(chks)+" | "+memo}
            try:
                # 데이터 업데이트
                new_df = pd.concat([m_df, pd.DataFrame([row])], ignore_index=True)
                conn.update(data=new_df)
                
                # 저장 성공 메시지 후 리셋 함수 호출
                st.success("저장 성공! 입력창을 초기화합니다.")
                time.sleep(1)
                reset_fields() # 여기서 it 값을 올려 모든 위젯을 새로고침함
                st.rerun()
            except Exception as e: st.error(f"저장 오류: {e}")

# --- [TAB 2: 정산] ---
with t2:
    st.subheader(f"📊 {date.today().month}월 정산 (Case # 열 기준)")
    if not m_df.empty:
        pdf = m_df.copy()
        pdf['SD_dt'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[pdf['SD_dt'].dt.month == date.today().month]
        
        if not m_dt.empty:
            v_cols = ['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']
            v_df = m_dt[v_cols].copy()
            v_df.index = m_dt['Case #']
            v_df.index.name = "Case #"
            st.dataframe(v_df, use_container_width=True)
            
            pay_dt = m_dt[m_dt['Status'].str.lower() == 'normal']
            t_qty = pd.to_numeric(pay_dt['Qty'], errors='coerce').sum()
            st.metric("합계 (Normal)", f"{int(t_qty)} ea / ${t_qty*19.505333:,.2f}")
        else: st.info("이번 달 데이터 없음")

# --- [TAB 3: 검색] ---
with t3:
    qs = st.text_input("검색", key="sb")
    if not m_df.empty:
        res = m_df[m_df['Patient'].str.contains(qs, case=False, na=False) | m_df['Case #'].str.contains(qs, case=False, na=False)] if qs else m_df.tail(20)
        st.dataframe(res, use_container_width=True)
