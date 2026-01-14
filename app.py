import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time
import io

# 1. 페이지 설정 및 다크 네이비 테마 (디자인 절대 고정)
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container {
        display: flex; justify-content: space-between; align-items: center;
        background-color: #1a1c24; padding: 20px 30px; border-radius: 10px;
        margin-bottom: 25px; border: 1px solid #30363d;
    }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p, [data-testid="stExpander"] p, .stMetric p {
        color: #ffffff !important; font-weight: 600 !important;
    }
    div[data-testid="stRadio"] label, .stCheckbox label span, button[data-baseweb="tab"] div {
        color: #ffffff !important;
    }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea {
        background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important;
    }
    .stButton>button {
        width: 100%; height: 3.5em; background-color: #4c6ef5 !important;
        color: white !important; font-weight: bold !important; border-radius: 5px; border: none !important;
    }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""
    <div class="header-container">
        <div style="font-size: 26px; font-weight: 800; color: #ffffff;"> Skycad Dental Lab Night Guard Manager </div>
        <div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div>
    </div>
    """, unsafe_allow_html=True)

# 2. 서비스 연결 및 AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("API Key가 설정되지 않았습니다.")

conn = st.connection("gsheets", type=GSheetsConnection)

# 세션 상태 초기화
if "it" not in st.session_state: st.session_state.it = 0
if "last_analyzed" not in st.session_state: st.session_state.last_analyzed = None
iter_no = str(st.session_state.it)

# 데이터 로드 함수
@st.cache_data(ttl=1)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

@st.cache_data(ttl=600)
def get_ref():
    try: return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()
clinics_list = sorted([c for c in ref.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic']) if not ref.empty else []
docs_list = sorted([d for d in ref.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor']) if not ref.empty else []

# --- 분석 멈춤 방지용 정밀 엔진 ---
def analyze_with_fallback(uploaded_file, clinics, doctors):
    try:
        # 1. 이미지 처리 (속도를 위해 적정 해상도 유지)
        img = Image.open(uploaded_file)
        img.thumbnail((1024, 1024))
        
        # 2. 모델 설정 (안정성이 높은 flash 우선 사용 후 실패시 재시도)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""Extract 4 items from this dental order sheet. Response format: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val. 
        List of Clinics: {", ".join(clinics)}. 
        List of Doctors: {", ".join(doctors)}. 
        If not clear, leave as empty. Only output the format."""
        
        # 3. 분석 실행 (타임아웃은 API 자체에서 처리됨)
        response = model.generate_content([prompt, img])
        
        # 4. 결과 파싱
        if not response or not response.text: return None
        
        res = {}
        for item in response.text.replace('\n', ',').split(','):
            if ':' in item:
                k, v = item.split(':', 1)
                res[k.strip().upper()] = v.strip()
        return res
    except Exception as e:
        print(f"Error during AI scan: {e}")
        return None

# --- 날짜 및 매칭 로직 ---
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

def sync_date():
    st.session_state["shp" + iter_no] = get_shp(st.session_state["due" + iter_no])

def on_doctor_change():
    sel_doc = st.session_state.get("sd" + iter_no)
    if sel_doc and sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty: st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

def on_clinic_change():
    sel_cl = st.session_state.get("sc_box" + iter_no)
    if sel_cl and sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty: st.session_state["sd" + iter_no] = match.iloc[0, 2]

# 탭 구성
t1, t2, t3 = st.tabs(["📝 등록 (Register)", "📊 통계 및 정산 (Analytics)", "🔍 검색 (Search)"])

with t1:
    st.markdown("### 📸 의뢰서 자동 스캔")
    # 파일 업로더 키를 동적으로 생성하여 초기화 가능하게 함
    ai_file = st.file_uploader("의뢰서를 찍으면 정보가 입력됩니다", type=["jpg", "jpeg", "png"], key=f"scanner_{st.session_state.it}")
    
    # 분석 프로세스
    if ai_file is not None and st.session_state.last_analyzed != ai_file.name:
        with st.status("🔍 AI 분석 프로세스 가동 중...") as status:
            res = analyze_with_fallback(ai_file, clinics_list, docs_list)
            if res:
                # 결과 적용
                st.session_state["c" + iter_no] = res.get('CASE', '')
                st.session_state["p" + iter_no] = res.get('PATIENT', '')
                
                c_val = res.get('CLINIC', '')
                d_val = res.get('DOCTOR', '')
                if c_val in clinics_list: st.session_state["sc_box" + iter_no] = c_val
                if d_val in docs_list: st.session_state["sd" + iter_no] = d_val
                
                st.session_state.last_analyzed = ai_file.name
                status.update(label="✅ 분석 완료! 즉시 입력창을 확인하세요.", state="complete", expanded=False)
                time.sleep(1)
                st.rerun()
            else:
                status.update(label="❌ 분석에 실패했습니다. 수동 입력을 권장합니다.", state="error", expanded=True)
                st.session_state.last_analyzed = ai_file.name # 실패해도 중복 실행 방지

    st.markdown("---")
    st.markdown("### 📋 정보 입력")
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + iter_no)
    patient = c1.text_input("환자명 (Patient)", key="p" + iter_no)
    sel_cl = c2.selectbox("병원 (Clinic)", ["선택"] + clinics_list + ["➕ 직접"], key="sc_box" + iter_no, on_change=on_clinic_change)
    f_cl = c2.text_input("직접입력(병원)", key="tc" + iter_no) if sel_cl=="➕ 직접" else (sel_cl if sel_cl != "선택" else "")
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
        
        if "due" + iter_no not in st.session_state: st.session_state["due" + iter_no] = date.today() + timedelta(days=7)
        due_val = d3.date_input("Due Date (마감)", key="due" + iter_no, on_change=sync_date)
        shp_val = d3.date_input("Shipping Date (출고)", key="shp" + iter_no)
        stt = d3.selectbox("상태 (Status)", ["Normal","Hold","Canceled"], key="st" + iter_no)

    with st.expander("📂 특이사항 및 사진 (Notes & Photos)", expanded=True):
        col_ex1, col_ex2 = st.columns([0.6, 0.4])
        chks = []
        if not ref.empty and len(ref.columns) > 3:
            chks_list = sorted(list(set([str(x) for x in ref.iloc[:,3:].values.flatten() if x and str(x)!='nan' and str(x)!='Price'])))
            chks = col_ex1.multiselect("특이사항 선택", chks_list, key="ck" + iter_no)
        uploaded_file = col_ex1.file_uploader("참고 사진 첨부", type=["jpg", "png", "jpeg"], key="img_up" + iter_no)
        memo = col_ex2.text_area("기타 메모", key="me" + iter_no, height=125)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.error("Case Number를 입력해주세요.")
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
            st.success("데이터 저장 완료!")
            time.sleep(1)
            st.session_state.it += 1
            st.session_state.last_analyzed = None
            st.cache_data.clear()
            st.rerun()

with t2:
    st.markdown("### 📊 실적 확인")
    today = date.today()
    sy, sm = st.columns(2)
    s_y = sy.selectbox("연도", range(today.year, today.year - 5, -1))
    s_m = sm.selectbox("월", range(1, 13), index=today.month - 1)
    if not main_df.empty:
        pdf = main_df.copy()
        pdf['Qty'] = pd.to_numeric(pdf['Qty'], errors='coerce').fillna(0)
        pdf['Total'] = pd.to_numeric(pdf['Total'], errors='coerce').fillna(0)
        pdf['SD_DT'] = pd.to_datetime(pdf['Shipping Date'].str[:10], errors='coerce')
        m_dt = pdf[(pdf['SD_DT'].dt.year == s_y) & (pdf['SD_DT'].dt.month == s_m)]
        if not m_dt.empty:
            st.dataframe(m_dt[['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Total', 'Status']], use_container_width=True, hide_index=True)
            norm_cases = m_dt[m_dt['Status'].str.lower() == 'normal']
            tot_qty, tot_amt = norm_cases['Qty'].sum(), norm_cases['Total'].sum()
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("총 생산 수량", f"{int(tot_qty)} ea")
            m2.metric("부족분 (320기준)", f"{int(320 - tot_qty)} ea" if 320-tot_qty>0 else "목표 달성!")
            m3.metric("총 매출", f"${int(tot_amt):,}")

with t3:
    st.markdown("### 🔍 케이스 검색")
    q_s = st.text_input("검색어 입력")
    if not main_df.empty and q_s:
        f_df = main_df[main_df['Case #'].str.contains(q_s, case=False, na=False) | main_df['Patient'].str.contains(q_s, case=False, na=False)]
        st.dataframe(f_df, use_container_width=True, hide_index=True)
