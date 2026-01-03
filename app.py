import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 상단 레이아웃
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

# 제목과 제작자 정보 (글씨 밝기를 #666으로 조정하여 선명하게 함)
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">🦷 Skycad Lab Night Guard Manager</h1>
        <b style="font-size: 15px; color: #666;">Designed By Heechul Jung</b>
    </div>
    """,
    unsafe_allow_html=True
)

conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 세션 상태 관리
if "it" not in st.session_state: 
    st.session_state.it = 0

i = st.session_state.it

# 날짜 초기값 설정
if f"due{i}" not in st.session_state:
    st.session_state[f"due{i}"] = date.today() + timedelta(days=7)
if f"shp{i}" not in st.session_state:
    st.session_state[f"shp{i}"] = st.session_state[f"due{i}"] - timedelta(days=2)

def sync_dates():
    st.session_state[f"shp{i}"] = st.session_state[f"due{i}"] - timedelta(days=2)

def reset_fields():
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=1)
def get_d():
    cols = ["Case #", "Clinic", "Doctor", "Patient", "Arch", "Material", "Price", "Qty", "Total", "Receipt Date", "Completed Date", "Shipping Date", "Due Date", "Status", "Notes"]
    try:
        df = conn.read(ttl=0).astype(str)
        if df.empty or "Case #" not in df.columns:
            return pd.DataFrame(columns=cols)
        df = df[df['Case #'].str.strip() != ""]
        df = df.apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        return df.reset_index(drop=True)
    except: 
        return pd.DataFrame(columns=cols)

m_df = get_d()
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 데이터 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case # (팬번호)", key=f"c{i}")
    patient = c1.text_input("Patient", key=f"p{i}")
    
    cl_list = sorted([str(c) for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic 검색/선택", ["선택 안함", "➕ 직접 입력"] + cl_list, key=f"cl{i}")
    
    f_cl = ""
    if sel_cl == "➕ 직접 입력":
        f_cl = c2.text_input("클리닉명 직접입력", key=f"fcl{i}")
    elif sel_cl != "선택 안함":
        f_cl = sel_cl
    
    if sel_cl not in ["선택 안함", "➕ 직접 입력"]:
        doc_list = sorted([str(d) for d in ref_df[ref_df.iloc[:,1]==sel_cl].iloc[:,2].unique() if d and str(d)!='nan'])
    else:
        doc_list = sorted([str(d) for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])

    sel_doc = c3.selectbox("Doctor 검색/선택", ["선택 안함", "➕ 직접 입력"] + doc_list, key=f"d{i}")
    
    f_doc = ""
    if sel_doc == "➕ 직접 입력":
        f_doc = c3.text_input("의사명 직접입력", key=f"fd{i}")
    elif sel_doc != "선택 안함":
        f_doc = sel_doc

    with st.expander("⚙️ 세부 옵션 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Max","Mand"], horizontal=True, key=f"a{i}")
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key=f"m{i}")
        qty = d1.number_input("Qty", 1, 10, 1, key=f"q{i}")
        is_33 = d2.checkbox("3D 스캔 (접수일 제외)", True, key=f"3d{i}")
        rd = d2.date_input("접수일", date.today(), key=f"rd{i}", disabled=is_33)
        cp = d2.date_input("완료일", date.today()+timedelta(1), key=f"cd{i}")
        
        if d2.checkbox("마감일/출고일 사용", True, key=f"h_d{i}"):
            due = d3.date_input("마감일", key=f"due{i}", on_change=sync_dates)
            shp = d3.date_input("출고일", key=f"shp{i}")
            s_t = d3.selectbox("배송 시간", ["Noon","EOD","ASAP"], key=f"st_time{i}") if due==shp else ""
        else:
            due = shp = s_t = None
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st_stat{i}")

    with st.expander("✅ 체크리스트 & 메모", expanded=True):
        chk_raw = ref_df.iloc[:, 3:].values.flatten()
        chk_opts = sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan'])))
        chks = st.multiselect("체크리스트 선택", chk_opts, key=f"ck{i}")
        memo = st.text_input("추가 메모", key=f"me{i}")
        up_img = st.file_uploader("📸 사진 업로드", type=['jpg', 'png', 'jpeg'], key=f"img{i}")
        if up_img: st.image(up_img, width=300)

    if st.button("🚀 시트에 저장하기", use_container_width=True):
        if not case_no:
            st.error("Case #를 입력해 주세요.")
        elif not f_cl and not f_doc:
            st.error("Clinic 또는 Doctor 중 하나는 입력해야 합니다.")
        else:
            p_u = 180
            if f_cl:
                try:
                    p_u_val = ref_df[ref_df.iloc[:, 1] == f_cl].iloc[0, 3]
                    p_u = int(float(p_u_val))
                except: p_u = 180
            
            dfmt = '%Y-%m-%d'
            # [수정된 부분] 괄호와 조건문 구문 오류 해결
            final_notes = ", ".join(chks) + (f" | {memo}" if memo else "")
            
            row = {
                "Case #": case_no, "Clinic": f_cl if f_cl else "-", "Doctor": f_doc if f_doc else "-", "Patient": patient if patient else "-",
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u*qty,
                "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                "Completed Date": cp.strftime(dfmt),
                "Shipping Date": (shp.strftime(dfmt) if shp else "-"),
                "Due Date": (due.strftime(dfmt) if due else "-"),
                "Status": stt, "Notes": final_notes
            }
            try:
                new_data = pd.concat([m_df, pd.DataFrame([row])], ignore_index=True)
                conn.update(data=new_data)
                st.success(f"{case_no} 저장 성공!")
                time.sleep(1); reset_fields(); st.rerun()
            except Exception as e: st.error(f"저장 오류: {e}")

# --- [TAB 2: 정산] ---
with t2:
    st.subheader("💰 월별 정산 현황")
    c_y, c_m = st.columns(2)
    sel_year = c_y.selectbox("연도", range(date.today().year, date.today().year - 5, -1))
    sel_month = c_m.selectbox("월", range(1, 13), index=date.today().month - 1)
    
    if not m_df.empty:
        pdf = m_df.copy()
        pdf['Qty'] = pd.to_numeric(pdf['Qty'], errors='coerce').fillna(0)
        pdf['SD_dt'] = pd.to_datetime(pdf['Shipping Date'], errors='coerce')
        m_dt = pdf[(pdf['SD_dt'].dt.year == sel_year) & (pdf['SD_dt'].dt.month == sel_month)]
        
        if not m_dt.empty:
            disp_cols = ['Case #', 'Shipping Date', 'Clinic', 'Doctor', 'Patient', 'Qty', 'Status']
            st.dataframe(m_dt[disp_cols], use_container_width=True, hide_index=True)
            
            pay_dt = m_dt[m_dt['Status'].str.lower() == 'normal']
            total_qty = pay_dt['Qty'].sum()
            extra_qty = max(0, total_qty - 320)
            
            m1, m2, m3 = st.columns(3)
            m1.metric("총 수량", f"{int(total_qty)} ea")
            m2.metric("Extra", f"{int(extra_qty)} ea")
            m3.metric("정산 금액", f"${extra_qty * 19.505333:,.2f}")
        else: st.info("데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    st.subheader("🔍 검색")
    qs = st.text_input("검색어 입력 (환자, Case #, 병원 등)", key="search_bar")
    if not m_df.empty:
        if qs:
            mask = m_df.apply(lambda row: row.astype(str).str.contains(qs, case=False).any(), axis=1)
            f_df = m_df[mask]
            st.dataframe(f_df, use_container_width=True, hide_index=True)
        else:
            st.dataframe(m_df.tail(20), use_container_width=True, hide_index=True)
