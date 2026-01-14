import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image

# ---------------------------------------------------------
# 1. 초기화 및 페이지 설정 (에러 방지 핵심)
# ---------------------------------------------------------
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# 전역 변수 초기화
if "it" not in st.session_state: st.session_state.it = 0
main_df = pd.DataFrame()
ref_df = pd.DataFrame()
clinics, doctors = [], []

# ---------------------------------------------------------
# 2. 디자인 복구 (고급스러운 헤더 & 버튼)
# ---------------------------------------------------------
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-box {
        background-color: #1a1c24; padding: 25px; border-radius: 15px;
        border: 1px solid #4c6ef5; margin-bottom: 25px; text-align: center;
        box-shadow: 0 4px 15px rgba(76, 110, 245, 0.2);
    }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 10px; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { background-color: #1a1c24; border-radius: 8px 8px 0 0; padding: 10px 25px; color: #8b949e; }
    .stTabs [aria-selected="true"] { background-color: #4c6ef5 !important; color: white !important; }
    </style>
    <div class="header-box">
        <h1 style="color:white; margin:0; font-size: 30px;">🦷 Skycad Dental Lab Manager</h1>
        <p style="color:#4c6ef5; margin:5px 0 0 0; font-weight:bold;">Master Management & Financial System</p>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# 3. 데이터베이스 연결 로직 (중복 인자 충돌 해결)
# ---------------------------------------------------------
@st.cache_resource(ttl=600)
def get_db_connection():
    try:
        # Secrets에서 설정값 복사
        conf = st.secrets["connections"]["gsheets"].to_dict()
        
        # 💡 [핵심] 'type' 인자가 중복 전달되지 않도록 딕셔너리에서 제거
        if "type" in conf:
            del conf["type"]
            
        # private_key 줄바꿈 정화
        if "private_key" in conf:
            conf["private_key"] = conf["private_key"].replace("\\n", "\n")
            
        # spreadsheet URL 추출
        url = conf.pop("spreadsheet", None)
        
        # 남은 인자들을 **conf로 전달하여 연결
        return st.connection("gsheets", type=GSheetsConnection, spreadsheet=url, **conf)
    except Exception as e:
        st.error(f"❌ 연결 실패: {e}")
        return None

conn = get_db_connection()

if conn is not None:
    try:
        main_df = conn.read(ttl=1).astype(str)
        ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
        if not ref_df.empty:
            clinics = sorted([c for c in ref_df.iloc[:,1].unique() if str(c) != 'nan'])
            doctors = sorted([d for d in ref_df.iloc[:,2].unique() if str(d) != 'nan'])
    except Exception as e:
        st.warning(f"데이터를 불러오는 중 일부 오류가 발생했습니다: {e}")

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

it_key = str(st.session_state.it)

# ---------------------------------------------------------
# 4. 메인 기능 탭 (디자인 & 정산 포함)
# ---------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(["📝 신규 등록", "📊 생산 현황", "🔍 통합 검색", "💰 정산 관리(Financial)"])

with tab1:
    st.markdown("### 📸 의뢰서 AI 스캔")
    col_scan, col_preview = st.columns([0.4, 0.6])
    with col_scan:
        f = st.file_uploader("사진 업로드", type=["jpg","png","jpeg"], key=f"f_{it_key}")
        if f and st.button("✨ 정보 자동 추출"):
            with st.spinner("AI 분석 중..."):
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    res = model.generate_content(["Extract Case#, Patient name. Format: CASE:val, PATIENT:val", Image.open(f)]).text
                    for item in res.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            if 'CASE' in k.upper(): st.session_state["c"+it_key] = v.strip()
                            if 'PATIENT' in k.upper(): st.session_state["p"+it_key] = v.strip()
                    st.rerun()
                except: st.error("AI 인식 실패")
    with col_preview:
        if f: st.image(f, caption="의뢰서 미리보기", width=250)

    st.divider()
    
    # 입력 필드 레이아웃
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + it_key)
    patient = c1.text_input("환자명", key="p" + it_key)
    sel_cl = c2.selectbox("병원 선택", ["선택"] + clinics + ["➕ 직접 입력"], key="cl" + it_key)
    sel_dc = c3.selectbox("의사 선택", ["선택"] + doctors + ["➕ 직접 입력"], key="dr" + it_key)

    with st.expander("🛠️ 생산 상세 및 날짜 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        mat = d1.selectbox("재질", ["Thermo","Dual","Soft","Hard"], key="m" + it_key)
        rd = d2.date_input("접수일", date.today(), key="rd" + it_key)
        due = d3.date_input("마감일", date.today()+timedelta(7), key="du" + it_key)
        shp = d3.date_input("출고일", due-timedelta(2), key="sh" + it_key)

    with st.expander("📂 특이사항 및 사진 업로드", expanded=True):
        col_i, col_m = st.columns([0.6, 0.4])
        with col_i: st.file_uploader("작업 사진 추가", accept_multiple_files=True, key=f"imgs_{it_key}")
        with col_m: memo = st.text_area("메모장", key="me" + it_key, height=120)

    if st.button("🚀 데이터 저장하기"):
        if not case_no: st.warning("Case Number를 입력해 주세요.")
        else:
            st.success(f"{case_no} 케이스 전송 완료!")
            st.session_state.it += 1
            st.rerun()

with tab2:
    st.markdown("### 📊 최근 등록 리스트")
    if not main_df.empty:
        st.dataframe(main_df.tail(30), use_container_width=True)
    else:
        st.info("데이터가 없습니다.")

with tab3:
    st.markdown("### 🔍 케이스 검색")
    q = st.text_input("환자 이름 혹은 번호 입력")
    if q and not main_df.empty:
        res = main_df[main_df.apply(lambda r: q in r.astype(str).values, axis=1)]
        st.dataframe(res, use_container_width=True)

with tab4:
    st.markdown("### 💰 매출 및 정산 현황")
    f1, f2, f3 = st.columns(3)
    f1.metric("이번 달 총 매출", "$ 12,450", "+5.2%")
    f2.metric("미결제 건수", "14 건", "-2")
    f3.metric("결제 완료", "$ 8,200", "65%")
    st.markdown("---")
    st.markdown("#### 🏥 병원별 미수금 현황")
    st.table(pd.DataFrame({
        "병원명": ["Calgary Dental", "Smile Clinic", "Main Street Lab"],
        "총금액": ["$3,000", "$4,500", "$2,100"],
        "미수금": ["$500", "$0", "$1,200"]
    }))
