import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import time

# 1. 페이지 설정 및 상단 레이아웃
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

# 제목과 제작자 정보를 상단에 배치
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
        <h1 style="margin: 0;">🦷 Skycad Lab Night Guard Manager</h1>
        <b style="font-size: 14px; color: #333;">Designed By Heechul Jung</b>
    </div>
    """,
    unsafe_allow_html=True
)

# 구글 시트 연결
conn = st.connection("gsheets", type=GSheetsConnection)

# 2. 세션 상태 관리 (입력창 초기화 및 날짜 연동용)
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
    curr_i = st.session_state.it
    # 날짜 세션 키 삭제
    for key in [f"due{curr_i}", f"shp{curr_i}"]:
        if key in st.session_state: del st.session_state[key]
    st.session_state.it += 1
    st.cache_data.clear()

@st.cache_data(ttl=1)
def get_d():
    try:
        df = conn.read(ttl=0).astype(str)
        # 빈 행 제외
        df = df[df['Case #'].str.strip() != ""]
        # 날짜 뒤의 시간 문자열 제거 및 공백 제거
        df = df.apply(lambda x: x.str.replace(' 00:00:00','',regex=False).str.strip())
        return df.reset_index(drop=True)
    except: return pd.DataFrame()

# 데이터 로드
m_df = get_d()
# Reference 시트 로드 (클리닉/의사 리스트 및 단가 정보)
ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)

# 탭 구성
t1, t2, t3 = st.tabs(["📝 등록", "💰 정산", "🔍 검색"])

# --- [TAB 1: 등록] ---
with t1:
    st.subheader("📋 데이터 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key=f"c{i}")
    patient = c1.text_input("Patient", key=f"p{i}")
    
    # Clinic 선택
    cl_list = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
    sel_cl = c2.selectbox("Clinic", ["선택"]+cl_list+["➕ 직접"], key=f"cl{i}")
    f_cl = c2.text_input("클리닉명 직접입력", key=f"fcl{i}") if sel_cl=="➕ 직접" else sel_cl
    
    # Doctor 선택 (클리닉에 종속됨)
    doc_opts = ["선택","➕ 직접"]
    if sel_cl not in ["선택", "➕ 직접"]:
        docs = ref_df[ref_df.iloc[:,1]==sel_cl].iloc[:,2].unique()
        doc_opts += sorted([d for d in docs if d and str(d)!='nan'])
    sel_doc = c3.selectbox("Doctor", doc_opts, key=f"d{i}")
    f_doc = c3.text_input("의사명 직접입력", key=f"fd{i}") if sel_doc=="➕ 직접" else sel_doc

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
        else: due = shp = s_t = None
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key=f"st_stat{i}")

    with st.expander("✅ 체크리스트 & 메모", expanded=True):
        chk_raw = ref_df.iloc[:,3:].values.flatten()
        chks = st.multiselect("체크리스트 선택", sorted(list(set([str(x) for x in chk_raw if x and str(x)!='nan']))), key=f"ck{i}")
        memo = st.text_input("추가 메모", key=f"me{i}")
        up_img = st.file_uploader("📸 사진 업로드(미리보기)", type=['jpg', 'png', 'jpeg'], key=f"img{i}")
        if up_img:
            st.image(up_img, width=300)

    # --- [저장 실행 버튼] ---
    if st.button("🚀 시트에 저장하기", use_container_width=True):
        # 유효성 검사: Case #는 필수이며, Clinic 또는 Doctor 중 하나는 있어야 함
        if not case_no:
            st.error("Case #를 입력해 주세요.")
        elif (f_cl in ["선택", ""]) and (f_doc in ["선택", ""]):
            st.error("Clinic(클리닉) 또는 Doctor(의사명) 중 최소 하나는 입력해야 합니다.")
        else:
            # 단가(Price) 계산: 클리닉이 없거나 정보가 없으면 기본값 180 적용
            p_u = 180
            try:
                if f_cl not in ["선택", "", "➕ 직접"]:
                    # Reference 시트에서 해당 클리닉의 단가 컬럼(4번째) 가져오기
                    p_u_val = ref_df[ref_df.iloc[:, 1] == f_cl].iloc[0, 3]
                    p_u = int(float(p_u_val))
            except:
                p_u = 180
            
            dfmt = '%Y-%m-%d'
            # "선택" 문자열이 시트에 저장되지 않도록 빈 칸 처리
            final_cl = "" if f_cl == "선택" else f_cl
            final_doc = "" if f_doc == "선택" else f_doc
            
            row = {
                "Case #": case_no, 
                "Clinic": final_cl, 
                "Doctor": final_doc, 
                "Patient": patient,
                "Arch": arch, 
                "Material": mat, 
                "Price": p_u, 
                "Qty": qty, 
                "Total": p_u * qty,
                "Receipt Date": ("-" if is_33 else rd.strftime(dfmt)),
                "Completed Date": cp.strftime(dfmt),
                "Shipping Date": (shp.strftime(dfmt) if shp else "-"),
                "Due Date": (due.strftime(dfmt) if due else "-"),
                "Status": stt, 
                "Notes": ", ".join(chks) + (f" | {memo}" if memo else "")
            }
            
            try:
                # 기존 데이터에 새 행 추가 후 구글 시트 업데이트
                new_data = pd.concat([m_df, pd.DataFrame([row])], ignore_index=True)
                conn.update(data=new_data)
                st.success(f"성공: {case_no} 케이스가 저장되었습니다!")
                time.sleep(1)
                reset_fields()
                st.rerun()
            except Exception as e:
                st.error(f"저장 중 오류가 발생했습니다: {e}")

# --- [TAB 2: 정산] ---
with t2:
    st.subheader("💰 월별 정산 현황")
    today = date.today()
    c_y, c_m = st.columns(2)
    sel_year = c_y.selectbox("연도", range(today.year, today.year - 5, -1))
    sel_month = c_m.selectbox("월", range(1, 13), index=today.month - 1)
    
    if not m_df.empty:
        pdf = m_df.copy()
        # Shipping Date 기준으로 월별 필터링
        pdf['SD_dt'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD_dt'].dt.year == sel_year) & (pdf['SD_dt'].dt.month == sel_month)]
        
        if not m_dt.empty:
            # 화면에 보여줄 컬럼 설정 (Doctor 추가)
            v_df = m_dt[['Shipping Date', 'Clinic', 'Doctor', 'Patient', 'Qty', 'Status']].copy()
            v_df.index = m_dt['Case #']
            v_df.index.name = "Case #"
            st.dataframe(v_df, use_container_width=True)
            
            # 수량 및 금액 계산 (Status가 Normal인 것만)
            pay_dt = m_dt[m_dt['Status'].str.lower() == 'normal'].copy()
            pay_dt['Qty'] = pd.to_numeric(pay_dt['Qty'], errors='coerce').fillna(0)
            
            total_qty = pay_dt['Qty'].sum()
            extra_qty = max(0, total_qty - 320)
            extra_pay = extra_qty * 19.505333
            
            m1, m2, m3 = st.columns(3)
            m1.metric(f"{sel_month}월 총 수량", f"{int(total_qty)} ea")
            m2.metric("엑스트라(320개 초과)", f"{int(extra_qty)} ea")
            m3.metric("엑스트라 정산금액", f"${extra_pay:,.2f}")
        else:
            st.info(f"{sel_year}년 {sel_month}월에 해당하는 출고 데이터가 없습니다.")

# --- [TAB 3: 검색] ---
with t3:
    st.subheader("🔍 검색")
    qs = st.text_input("환자명 또는 Case # 입력", key="search_bar")
    if not m_df.empty:
        if qs:
            f_df = m_df[m_df['Case #'].str.contains(qs, case=False, na=False) | 
                        m_df['Patient'].str.contains(qs, case=False, na=False)]
            st.dataframe(f_df, use_container_width=True)
        else:
            # 검색어 없을 시 최근 20개 데이터 표시
            st.dataframe(m_df.tail(20), use_container_width=True)
