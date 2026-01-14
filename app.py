import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 페이지 설정 및 다크 네이비 테마 (디자인 절대 고정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #1a1c24;
        padding: 20px 30px;
        border-radius: 10px;
        margin-bottom: 25px;
        border: 1px solid #30363d;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, [data-testid="stExpander"] p, .stMetric p {
        color: #ffffff !important;
        font-weight: 600 !important;
    }
    div[data-testid="stRadio"] label, .stCheckbox label span, button[data-baseweb="tab"] div {
        color: #ffffff !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important;
        color: #ffffff !important;
        border: 1px solid #4a4a4a !important;
    }
    .stButton>button {
        width: 100%;
        height: 3.5em;
        background-color: #4c6ef5 !important;
        color: white !important;
        font-weight: bold !important;
        border-radius: 5px;
        border: none !important;
    }
    [data-testid="stMetricValue"] {
        color: #4c6ef5 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# AI 설정 (Secrets에 GOOGLE_API_KEY가 있어야 함)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

# 💡 고정 제목 및 제작자 정보
st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;">
            Skycad Dental Lab Night Guard Manager
        </div>
        <div style="text-align: right; color: #ffffff;">
            <span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)

if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 데이터 로드
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

# 💡 양방향 자동 매칭 콜백 함수
def on_doctor_change():
    sel_doc = st.session_state["sd" + iter_no]
    if sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty:
            st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

def on_clinic_change():
    sel_cl = st.session_state["sc_box" + iter_no]
    if sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty:
            st.session_state["sd" + iter_no] = match.iloc[0, 2]

# 세션 초기화 로직
if "sd" + iter_no not in st.session_state: st.session_state["sd" + iter_no] = "선택"
if "sc_box" + iter_no not in st.session_state: st.session_state["sc_box" + iter_no] = "선택"

def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

def sync_date():
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

if "due" + iter_no not in st.session_state:
    st.session_state["due" + iter_no] = date.today() + timedelta(days=7)
if "shp" + iter_no not in st.session_state:
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

def reset_all():
    st.session_state.it += 1
    st.cache_data.clear()

t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 및 정산 (Analytics)", "🔍 검색 (Search)"])

with t1:
    # --- 📸 AI 의뢰서 분석 섹션 (추가됨) ---
    st.markdown("### 📸 의뢰서 AI 스캔")
    with st.expander("의뢰서 사진을 업로드하여 자동 입력하기", expanded=False):
        c_scan, c_pre = st.columns([0.6, 0.4])
        scan_file = c_scan.file_uploader("의뢰서 이미지 (JPG, PNG)", type=["jpg", "png", "jpeg"], key="scan_up"+iter_no)
        
        if scan_file:
            c_pre.image(scan_file, use_container_width=True, caption="스캔 대상")
            if c_scan.button("✨ AI 분석 실행", use_container_width=True):
                with st.spinner("Gemini AI가 텍스트를 분석 중..."):
                    try:
                        model = genai.GenerativeModel('gemini-1.5-flash')
                        img = Image.open(scan_file)
                        prompt = "Extract 'Case Number', 'Patient Name', 'Doctor Name' from this dental lab form. Format: CASE:val, PATIENT:val, DOCTOR:val"
                        response = model.generate_content([prompt, img])
                        
                        # AI 결과 파싱 및 세션 주입
                        res_text = response.text
                        for line in res_text.split(','):
                            if ':' in line:
                                k, v = line.split(':', 1)
                                k, v = k.strip().upper(), v.strip()
                                if 'CASE' in k: st.session_state["c"+iter_no] = v
                                if 'PATIENT' in k: st.session_state["p"+iter_no] = v
                                if 'DOCTOR' in k: 
                                    st.session_state["sd"+iter_no] = v
                                    on_doctor_change() # 병원 연동 콜백 호출
                        st.success("분석 완료! 아래 입력란을 확인하세요.")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"AI 분석 오류: {e}")

    st.markdown("---")
    docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor']) if not ref.empty else []
    clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic']) if not ref.empty else []
    
    st.markdown("### 📋 정보 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명 (Patient)", key="p" + iter_no)
    
    # 병원 선택
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no, on_change=on_clinic_change)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else "")

    # 의사 선택
    sel_doc = c3.selectbox("의사 (Doctor)", ["선택"] + docs_list + ["➕ 직접"], key="sd" + iter_no, on_change=on_doctor_change)
    f_doc = c3.text_input("직접입력(의사)", key="td" + iter_no) if sel_doc=="➕ 직접" else (sel_doc if sel_doc != "선택" else "")

    with st.expander("생산 세부 설정 (Production Details)", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary","Mandibular"], horizontal=True, key="ar" + iter_no)
        mat = d1.selectbox("Material", ["Thermo","Dual","Soft","Hard"], key="ma" + iter_no)
        qty = d1.number_input("수량 (Qty)", 1, 10, 1, key="qy" + iter_no)
        is_33 = d2.checkbox("3D Digital Scan Mode", True, key="d3" + iter_no)
        rd = d2.date_input("접수일", date.today(), key="rd" + iter_no, disabled=is_33)
        cp = d2.date_input("완료예정일", date.today()+timedelta(1), key="cp" + iter_no)
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date (출고)", key="shp" + iter_no)
        stt = d3.selectbox("상태 (Status)", ["Normal","Hold","Canceled"], key="st" + iter_no)

    # 💡 특이사항 체크리스트 (사진 바로 윗 칸 고정)
    st.markdown("### ✅ 특이사항 (Checklist)")
    chks = []
    if not ref.empty and len(ref.columns) > 3:
        # Reference 시트 D열 이후의 값을 모두 체크리스트로 활용
        raw_options = ref.iloc[:, 3:].values.flatten()
        chks_list = sorted(list(set([str(x) for x in raw_options if x and str(x)!='nan' and str(x)!='Price'])))
        chks = st.multiselect("특이사항 선택", chks_list, key="ck" + iter_no)

    with st.expander("📂 사진 및 메모 (Photos & Memo)", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        uploaded_file = col_ex1.file_uploader("사진 첨부", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = col_ex2.text_area("기타 메모", key="me" + iter_no, height=125)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: 
            st.error("Case Number를 입력해주세요.")
        else:
            p_u = 180
            if f_cl and not ref.empty:
                p_m = ref[ref.iloc[:, 1] == f_cl]
                if not p_m.empty:
                    try: p_u = int(float(p_m.iloc[0, 3]))
                    except: p_u = 180
            
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
            st.success("데이터가 성공적으로 저장되었습니다.")
            time.sleep(1)
            reset_all()
            st.rerun()

with t2:
    st.markdown("### 💰 실적 및 부족 수량 확인")
    today = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("연도", range(today.year, today.year - 5, -1))
    s_m = sm.selectbox("월", range(1, 13), index=today.month - 1)
    
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['SD_DT'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD_DT'].dt.year == s_y) & (pdf['SD_DT'].dt.month == s_m)]
        
        if not m_dt.empty:
            st.dataframe(m_dt[['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Total', 'Status', 'Notes']], use_container_width=True, hide_index=True)
            
            norm_cases = m_dt[m_dt['Status'].str.lower() == 'normal']
            tot_qty = pd.to_numeric(norm_cases['Qty'], errors='coerce').sum()
            
            # 💡 [정산] 희철님 전용 로직 적용
            target_qty = 320
            unit_price = 19.505333
            diff_qty = target_qty - tot_qty
            
            # 초과 수량 및 수당 계산
            over_qty = max(0, tot_qty - target_qty)
            total_payroll = tot_qty * unit_price
            
            st.markdown("---")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("총 생산 수량", f"{int(tot_qty)} ea")
            
            if diff_qty > 0:
                m2.metric("320개 기준 부족분", f"{int(diff_qty)} ea")
            else:
                m2.metric("할당량 초과분", f"+{int(over_qty)} ea", delta="목표 달성!")
            
            m3.metric("총 정산 금액 (단가기준)", f"${total_payroll:,.2f}")
            
            # 진행률 표시
            progress = min(1.0, tot_qty / target_qty)
            st.progress(progress)
            st.write(f"📊 할당량 달성률: {progress*100:.1f}%")
            
        else: st.info("해당 월의 데이터가 없습니다.")

with t3:
    st.markdown("### 🔍 케이스 검색")
    q_s = st.text_input("검색어 입력 (번호/환자명)", key="search_box")
    if not main_df.empty and q_s:
        f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
        st.dataframe(f_df, use_container_width=True, hide_index=True)
