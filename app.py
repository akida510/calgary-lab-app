import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container { display: flex; justify-content: space-between; align-items: center; background-color: #1a1c24; padding: 20px 30px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #30363d; }
    [data-testid="stWidgetLabel"] p, label p { color: #ffffff !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; font-size: 32px !important; }
    </style>
    """, unsafe_allow_html=True)

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;">Skycad Dental Lab Night Guard Manager</div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# [데이터 로드]
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
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# [로직] 콜백 및 날짜 계산
def on_doctor_change():
    sel_doc = st.session_state.get(f"sd{iter_no}")
    if sel_doc and sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty: st.session_state[f"sc_box{iter_no}"] = match.iloc[0, 1]

def on_clinic_change():
    sel_cl = st.session_state.get(f"sc_box{iter_no}")
    if sel_cl and sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty: st.session_state[f"sd{iter_no}"] = match.iloc[0, 2]

def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

def sync_date():
    st.session_state[f"shp{iter_no}"] = get_shp(st.session_state[f"due{iter_no}"])

if f"due{iter_no}" not in st.session_state:
    st.session_state[f"due{iter_no}"] = date.today() + timedelta(days=7)
    st.session_state[f"shp{iter_no}"] = get_shp(st.session_state[f"due{iter_no}"])

# ---------------------------------------------------------
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 정산 및 실적", "🔍 검색 (Search)"])

with t1:
    # 📸 AI 자동 스캔
    with st.expander("📸 의뢰서 AI 자동 입력", expanded=False):
        scan_f = st.file_uploader("의뢰서 사진 스캔", type=["jpg", "png", "jpeg"], key="s"+iter_no)
        if scan_f and st.button("✨ 분석 시작"):
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(["CASE:val, PATIENT:val, DOCTOR:val", Image.open(scan_f)]).text
                for item in res.split(','):
                    if ':' in item:
                        k, v = item.split(':', 1)
                        if 'CASE' in k.upper(): st.session_state["c"+iter_no] = v.strip()
                        if 'PATIENT' in k.upper(): st.session_state["p"+iter_no] = v.strip()
                        if 'DOCTOR' in k.upper(): 
                            st.session_state["sd"+iter_no] = v.strip()
                            on_doctor_change()
                st.rerun()
            except: st.error("AI 오류")

    st.markdown("### 📋 정보 입력")
    clinics_list = sorted(list(ref.iloc[:, 1].unique())) if not ref.empty else []
    docs_list = sorted(list(ref.iloc[:, 2].unique())) if not ref.empty else []

    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+iter_no)
    patient = c1.text_input("Patient", key="p"+iter_no)
    sel_cl = c2.selectbox("Clinic", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box"+iter_no, on_change=on_clinic_change)
    f_cl = c2.text_input("직접입력(병원)", key="tc"+iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else "")
    sel_doc = c3.selectbox("Doctor", ["선택"] + docs_list + ["➕ 직접"], key="sd"+iter_no, on_change=on_doctor_change)
    f_doc = c3.text_input("직접입력(의사)", key="td"+iter_no) if sel_doc=="➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("⚙️ 생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar"+iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma"+iter_no)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy"+iter_no)
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3"+iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd"+iter_no, disabled=is_33)
        cp = d2.date_input("완료예정일", date.today()+timedelta(1), key="cp"+iter_no)
        due_val = d3.date_input("Due Date", key="due"+iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date", key="shp"+iter_no)
        stt = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st"+iter_no)

    st.markdown("### 📂 특이사항 및 사진 (Notes & Photos)")
    with st.expander("상세 내용 입력", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        # 1. 체크리스트
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            raw_opts = ref.iloc[:, 3:].values.flatten()
            chks_list = sorted(list(set([str(x) for x in raw_opts if x and str(x)!='nan' and str(x)!='Price'])))
            chks = col_ex1.multiselect("특이사항 선택", chks_list, key="ck"+iter_no)
        # 2. 참고 사진 (복구 완료)
        uploaded_file = col_ex1.file_uploader("참고 사진 첨부", type=["jpg", "png", "jpeg"], key="img_up"+iter_no)
        # 3. 메모
        memo = col_ex2.text_area("기타 메모", key="me"+iter_no, height=150)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number 입력 필수")
        else:
            p_u = 180
            if f_cl and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == f_cl]; p_u = int(float(p_m.iloc[0, 3])) if not p_m.empty else 180
            
            final_notes = ", ".join(chks)
            if uploaded_file: final_notes += f" | 사진:{uploaded_file.name}"
            if memo: final_notes += f" | 메모:{memo}"

            new_row = {
                "Case #": case_no, "Clinic": f_cl, "Doctor": f_doc, "Patient": patient, 
                "Arch": arch, "Material": mat, "Price": p_u, "Qty": qty, "Total": p_u * qty,
                "Receipt Date": "-" if is_33 else rd.strftime('%Y-%m-%d'),
                "Completed Date": cp.strftime('%Y-%m-%d'),
                "Shipping Date": shp_val.strftime('%Y-%m-%d'),
                "Due Date": due_val.strftime('%Y-%m-%d'),
                "Status": stt, "Notes": final_notes
            }
            conn.update(data=pd.concat([main_df, pd.DataFrame([new_row])], ignore_index=True))
            st.success("저장 완료!")
            st.session_state.it += 1
            st.cache_data.clear()
            st.rerun()

with t2:
    st.markdown("### 💰 정산 실적 현황")
    if not main_df.empty:
        # [수정] 날짜 필터링 강화: 현재 연도와 월이 포함된 모든 데이터를 가져옴
        today = date.today()
        # 연도와 월을 따로 체크하여 2026-1-13과 2026-01-13 모두 잡도록 함
        main_df['SD_DT'] = pd.to_datetime(main_df['Shipping Date'], errors='coerce')
        m_df = main_df[(main_df['SD_DT'].dt.year == today.year) & (main_df['SD_DT'].dt.month == today.month)]
        
        # 정산 수치
        unit_p = 19.505333; quota = 320
        v_df = m_df[m_df['Status'].str.upper() == 'NORMAL']
        t_qty = pd.to_numeric(v_df['Qty'], errors='coerce').sum()
        t_pay = t_qty * unit_p
        diff = quota - t_qty

        m1, m2, m3 = st.columns(3)
        m1.metric("이번 달 총 생산량", f"{int(t_qty)} ea")
        m2.metric("320개 부족분", f"{int(diff)} ea" if diff > 0 else "목표 달성!")
        m3.metric("총 정산 예상액", f"${t_pay:,.2f}")
        
        st.markdown("---")
        st.write(f"📋 **{today.year}년 {today.month}월 세부 리스트**")
        if not m_df.empty:
            st.dataframe(m_df[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status', 'Notes']], use_container_width=True, hide_index=True)
        else:
            st.info("이번 달 데이터가 없습니다. 마감일/출고일 날짜를 확인해주세요.")

with t3:
    q = st.text_input("검색 (번호/성함)")
    if q and not main_df.empty:
        st.dataframe(main_df[main_df.apply(lambda r: q in r.astype(str).values, axis=1)], use_container_width=True)
