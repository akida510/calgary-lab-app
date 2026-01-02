import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 초기 설정
st.set_page_config(page_title="Skycad Lab", layout="wide")
st.markdown("### 🦷 Skycad Lab Manager <span style='font-size:0.8rem;color:grey;'>by Heechul Jung</span>", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0

# 💡 날짜 계산 함수 보완 (데이터가 날짜 타입일 때만 계산)
def upd_s():
    if 'd_k' in st.session_state:
        d_val = st.session_state.d_k
        if isinstance(d_val, str):
            try: d_val = datetime.strptime(d_val, '%Y-%m-%d').date()
            except: return
        st.session_state.s_k = d_val - timedelta(days=2)

if 'd_k' not in st.session_state: st.session_state.d_k = date.today() + timedelta(days=7)
if 's_k' not in st.session_state: st.session_state.s_k = st.session_state.d_k - timedelta(days=2)

@st.cache_data(ttl=5)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str).apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        df = df[(df['Case #']!="")&(df['Case #']!="nan")&(~df['Case #'].str.contains("Deliver|Remake|작업량",na=False))]
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    i = st.session_state.it
    st.subheader("📋 케이스 입력")
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no, patient = st.text_input("Case #", key=f"c{i}"), st.text_input("Patient", key=f"p{i}")
    with c2:
        cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
        sel_cl = st.selectbox("Clinic", ["선택"]+cl_list+["➕ 직접"], key=f"cl{i}")
        f_cl = st.text_input("클리닉명", key=f"fcl{i}") if sel_cl=="➕ 직접" else sel_cl
    with c3:
        doc_opts = ["선택","➕ 직접"]
        if sel_cl not in ["선택","➕ 직접"]:
            docs = ref_df[ref_df.iloc[:,1]==sel_cl].iloc[:,2].unique()
            doc_opts += sorted([d for d in docs if d and str(d)!='nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key=f"d{i}")
        f_doc = st.text_input("의사명", key=f"fd{i}") if sel_doc=="➕ 직접" else sel_doc

    with st.expander("⚙️ 세부설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        with d1:
            arch = st.radio("Arch", ["Max","Mand"], horizontal=True, key=f"a{i}")
            mat = st.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"m{i}")
            qty = st.number_input("Qty", 1, 10, 1, key=f"q{i}")
        with d2:
            is_33 = st.checkbox("3D 스캔 (접수일 제외)", True, key=f"3d{i}")
            rd, cp = st.date_input("접수일", date.today(), key=f"rd{i}", disabled=is_33), st.date_input("완료일", date.today()+timedelta(1), key=f"cd{i}")
        with d3:
            # 💡 마감일 사용 여부 선택 기능 추가
            has_due = st.checkbox("마감일/출고일 지정", True, key=f"h_due{i}")
            if has_due:
                due = st.date_input("마감일", key="d_k", on_change=upd_s)
                shp = st.date_input("출고일", key="s_k")
                ship_time = ""
                if due == shp:
                    ship_time = st.selectbox("⚠️ 출고 시간", ["Noon", "EOD", "ASAP"], key=f"st_time{i}")
                stt = st.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st{i}")
            else:
                due = shp = ship_time = None
                stt = st.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st_no_due{i}")

    with st.expander("✅ 기타 (사진 및 메모)", expanded=True):
        chks = st.multiselect("체크리스트", sorted(list(set([str(x) for x in ref_df.iloc[:,3:].values.flatten() if x and str(x)!='nan']))), key=f"ck{i}")
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg','png','jpeg'], key=f"img{i}")
        memo = st.text_input("메모", key=f"me{i}")

    if st.button("🚀 데이터 저장하기", use_container_width=True):
        if not case_no or f_cl in ["선택",""]: st.error("정보 부족")
        else:
            p_u = 180
            if sel_cl not in ["선택","➕ 직접"]:
                try: p_u = int(float(ref_df[ref_df.iloc[:,1] == sel_cl].iloc[0, 3]))
                except: p_u = 180
            
            # 마감일 정보가 있을 때와 없을 때 구분
            f_due = due.strftime('%Y-%m-%d') if has_due else "-"
            f_ship = shp.strftime('%Y-%m-%d') if has_due else "-"
            if has_due and ship_time: f_ship = f"{f_ship} {ship_time}"
                
            row = {"Case #":case_no,"Clinic":f_cl,"Doctor":f_doc,"Patient":patient,"Arch":arch,"Material":mat,"Price":p_u,"Qty":qty,"Total":p_u*qty,"Receipt Date":"-" if is_33 else rd.strftime('%Y-%m-%d'),"Completed Date":cp.strftime('%Y-%m-%d'),"Shipping Date":f_ship,"Due Date":f_due,"Status":stt,"Notes":", ".join(chks)+" | "+memo}
            try:
                conn.update(data=pd.concat([m_df, pd.DataFrame([row])], ignore_index=True))
                st.success("저장 완료!")
                time.sleep(1)
                st.session_state.it += 1; st.cache_data.clear(); st.rerun()
            except Exception as e: st.error(f"Error: {e}")

# --- [TAB 2: 정산] ---
with t2:
    st.subheader(f"📊 {date.today().month}월 정산")
    if not m_df.empty:
        pdf = m_df.copy()
        pdf['S_D_Only'] = pd.to_datetime(pdf['Shipping Date'].str.split().str[0], errors='coerce')
        m_dt = pdf[(pdf['S_D_Only'].dt.month==date.today().month)&(pdf['Status'].str.lower()=='normal')]
        if not m_dt.empty:
            v_df = m_dt[['Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status']].copy()
            try: 
                v_df.index = m_dt[m_df.columns[12]]
                v_df.index.name = "Pan No."
            except: pass
            st.dataframe(v_df, use_container_width=True)
            st.metric("이번 달 합계", f"{int(m_dt['Qty'].sum())} ea / ${m_dt['Qty'].sum()*19.505333:,.2f}")

# --- [TAB 3: 검색] ---
with t3:
    st.subheader("🔍 검색")
    qs = st.text_input("환자/Case # 입력", key="sb")
    sh = ['Case #','Clinic','Doctor','Patient','Arch','Material','Shipping Date','Status','Notes']
    if not m_df.empty:
        vc = [c for c in sh if c in m_df.columns]
        res = m_df[m_df['Patient'].str.contains(qs,False,False)|m_df['Case #'].str.contains(qs,False,False)] if qs else m_df.tail(15)
        st.dataframe(res[vc], use_container_width=True)
