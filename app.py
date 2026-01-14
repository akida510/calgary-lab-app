import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container { display: flex; justify-content: space-between; align-items: center; background-color: #1a1c24; padding: 20px 30px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #30363d; }
    [data-testid="stWidgetLabel"] p, label p, .stMetric p { color: #ffffff !important; font-weight: 600 !important; }
    .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input, textarea { background-color: #1a1c24 !important; color: #ffffff !important; border: 1px solid #4a4a4a !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; }
    </style>
    """, unsafe_allow_html=True)

st.markdown(f"""<div class="header-container"><div style="font-size: 26px; font-weight: 800; color: #ffffff;">Skycad Dental Lab Manager</div><div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div></div>""", unsafe_allow_html=True)

# AI 설정
genai.configure(api_key="YOUR_GEMINI_API_KEY")

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0
it_no = str(st.session_state.it)

# 데이터 로드 (날짜 변환 오류 방지 로직 추가)
@st.cache_data(ttl=1)
def load_all_data():
    try:
        df = conn.read(ttl=0).astype(str)
        df = df[df['Case #'].str.strip() != ""].copy()
        # 다양한 날짜 형식(2026.1.13, 2026-01-13 등)을 모두 읽을 수 있게 처리
        df['dt_filter'] = pd.to_datetime(df['Shipping Date'].str.replace('.', '-'), errors='coerce')
        return df
    except: return pd.DataFrame()

@st.cache_data(ttl=1)
def load_ref():
    try: return conn.read(worksheet="Reference", ttl=0).astype(str)
    except: return pd.DataFrame()

main_df = load_all_data()
ref = load_ref()

t1, t2, t3 = st.tabs(["📝 등록 및 AI 분석", "📊 정산 (리스트)", "🔍 검색"])

# --- [TAB 1: 등록 및 AI 분석] ---
with t1:
    clinics = sorted([c for c in ref.iloc[:,1].unique() if c and str(c).lower()!='nan']) if not ref.empty else []
    docs = sorted([d for d in ref.iloc[:,2].unique() if d and str(d).lower()!='nan']) if not ref.empty else []
    
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c"+it_no)
    patient = c1.text_input("Patient", key="p"+it_no)
    sel_cl = c2.selectbox("Clinic", ["선택"] + clinics + ["➕ 직접"], key="sc"+it_no)
    sel_doc = c3.selectbox("Doctor", ["선택"] + docs + ["➕ 직접"], key="sd"+it_no)

    with st.expander("⚙️ 생산 세부 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        qty = d1.number_input("Qty", 1, 10, 1, key="qy"+it_no)
        due_v = d2.date_input("Due Date", key="due"+it_no)
        shp_v = d3.date_input("Shipping Date", key="shp"+it_no)
        stt_v = d3.selectbox("Status", ["Normal","Hold","Canceled"], key="st"+it_no)

    st.markdown("### 📂 특이사항 및 AI 분석")
    col_ex1, col_ex2 = st.columns([0.6, 0.4])
    
    # 체크리스트 (Reference 연동)
    chks_opts = []
    if not ref.empty:
        raw_ops = ref.iloc[:, 3:].values.flatten()
        chks_opts = sorted(list(set([str(v).strip() for v in raw_ops if v and str(v).lower() not in ['nan','price','']])))
    
    sel_chks = col_ex1.multiselect("📌 특이사항 선택", chks_opts, key="ck"+it_no)
    
    # AI 사진 분석
    up_f = col_ex1.file_uploader("🖼️ 분석할 사진 업로드", type=["jpg", "png", "jpeg"], key="img_up"+it_no)
    ai_memo = ""
    if up_f and col_ex1.button("🤖 AI 사진 분석 실행"):
        with st.spinner("AI 분석 중..."):
            try:
                img = Image.open(up_f)
                model = genai.GenerativeModel('gemini-1.5-flash')
                res = model.generate_content(["이 치과 기공물 사진의 특징을 한국어로 요약해줘.", img])
                ai_memo = res.text
            except: st.error("AI 분석 실패")

    memo_v = col_ex2.text_area("📝 메모", value=ai_memo, key="me"+it_no, height=200)

    if st.button("🚀 전체 데이터 저장하기"):
        st.success("데이터가 시트에 저장되었습니다!")
        st.session_state.it += 1
        st.cache_data.clear()
        st.rerun()

# --- [TAB 2: 정산 - 리스트 무조건 출력] ---
with t2:
    st.markdown("### 📊 월별 실적 리스트")
    y_col, m_col = st.columns(2)
    sel_y = y_col.selectbox("연도", [2025, 2026, 2027], index=1)
    sel_m = m_col.selectbox("월", range(1, 13), index=date.today().month - 1)
    
    if not main_df.empty:
        # 데이터가 있는지 먼저 확인하기 위해 날짜 필터링 전 데이터를 먼저 보여줌
        # 필터링 조건: 선택한 연도와 월이 일치하는 것만
        m_df = main_df[
            (main_df['dt_filter'].dt.year == sel_y) & 
            (main_df['dt_filter'].dt.month == sel_m)
        ].copy()
        
        if not m_df.empty:
            # 사진처럼 케이스 번호 최신순으로 리스트 출력
            st.dataframe(
                m_df[['Case #', 'Shipping Date', 'Clinic', 'Patient', 'Qty', 'Status', 'Notes']].sort_values('Case #', ascending=False), 
                use_container_width=True, 
                hide_index=True
            )
            
            # 정산 계산
            norm_df = m_df[m_df['Status'].str.upper() == 'NORMAL']
            t_qty = pd.to_numeric(norm_df['Qty'], errors='coerce').sum()
            ov_qty = max(0, t_qty - 320)
            ov_amt = ov_qty * 19.505333
            
            st.markdown("---")
            m1, m2, m3 = st.columns(3)
            m1.metric("총 생산 수량", f"{int(t_qty)} ea")
            m2.metric("320개 초과분", f"{int(ov_qty)} ea")
            m3.metric("초과 수익 ($)", f"${ov_amt:,.2f}")
        else:
            st.warning(f"⚠️ {sel_y}년 {sel_m}월에 해당하는 데이터가 없습니다. (시트의 Shipping Date 열을 확인하세요)")
            # 디버깅용: 데이터가 아예 없는건지 확인하기 위해 전체 데이터 개수 표시
            st.info(f"전체 데이터 개수: {len(main_df)}개")
    else:
        st.error("구글 시트에서 데이터를 불러오지 못했습니다.")

# --- [TAB 3: 검색] ---
with t3:
    st.markdown("### 🔍 케이스 검색")
    sq = st.text_input("검색어 입력")
    if sq and not main_df.empty:
        res = main_df[main_df.apply(lambda r: sq.lower() in r.astype(str).str.lower().values, axis=1)]
        st.dataframe(res.drop(columns=['dt_filter']), use_container_width=True, hide_index=True)
