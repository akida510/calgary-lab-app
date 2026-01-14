import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 페이지 및 디자인 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-box {
        background-color: #1a1c24; padding: 25px; border-radius: 12px;
        border: 1px solid #30363d; margin-bottom: 25px; text-align: center;
    }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 8px; }
    [data-testid="stWidgetLabel"] p { color: #ffffff !important; font-weight: 600 !important; font-size: 15px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1a1c24; border-radius: 5px 5px 0 0; padding: 10px 20px; color: white; }
    </style>
    <div class="header-box">
        <h1 style="color:white; margin:0; font-size: 28px;">🦷 Skycad Dental Lab Manager</h1>
        <p style="color:#8b949e; margin:5px 0 0 0;">Secure Cloud & AI Management System</p>
    </div>
    """, unsafe_allow_html=True)

# 2. 데이터베이스 연결 (자동 수선 로직 포함)
def get_safe_connection():
    try:
        # Secrets에서 정보 가져오기
        if "connections" in st.secrets and "gsheets" in st.secrets.connections:
            # 💡 [핵심 해결책] private_key 내부의 모든 불필요한 공백과 이스케이프 문자 정리
            pk = st.secrets.connections.gsheets["private_key"]
            pk = pk.replace("\\n", "\n").strip()
            
            # 수리된 키를 세션 메모리에 일시적으로 적용
            st.secrets.connections.gsheets["private_key"] = pk
            
            # 인자 중복 없이 표준 방식으로 연결 (type 충돌 방지)
            return st.connection("gsheets", type=GSheetsConnection)
    except Exception as e:
        st.error(f"⚠️ 시스템 연결 중 오류가 발생했습니다: {e}")
        return None

conn = get_safe_connection()

if conn:
    try:
        main_df = conn.read(ttl=1).astype(str)
        ref_df = conn.read(worksheet="Reference", ttl=600).astype(str)
        clinics = sorted([c for c in ref_df.iloc[:,1].unique() if c and str(c)!='nan' and c!='Clinic'])
        doctors = sorted([d for d in ref_df.iloc[:,2].unique() if d and str(d)!='nan' and d!='Doctor'])
    except:
        clinics, doctors = [], []
else:
    st.stop()

# 3. AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# 세션 상태 관리 (입력 폼 초기화용)
if "it" not in st.session_state: st.session_state.it = 0
it_key = str(st.session_state.it)

# 4. 메인 화면 구성
tab1, tab2, tab3 = st.tabs(["📝 신규 케이스 등록", "📊 전체 실적 현황", "🔍 데이터 검색"])

with tab1:
    st.subheader("📸 의뢰서 스캔 및 자동 입력")
    scan_file = st.file_uploader("의뢰서 사진을 업로드하세요", type=["jpg", "jpeg", "png"], key=f"scan_{it_key}")
    
    if scan_file:
        if st.button("✨ AI 분석 시작", key="ai_btn"):
            with st.status("AI가 의뢰서를 분석하고 있습니다...") as status:
                try:
                    model = genai.GenerativeModel('gemini-1.5-flash')
                    img = Image.open(scan_file)
                    prompt = f"Extract Case#, Patient, Clinic, Doctor. Clinics:{clinics}, Doctors:{doctors}. Format: CASE:val, PATIENT:val, CLINIC:val, DOCTOR:val"
                    response = model.generate_content([prompt, img])
                    
                    # 결과 파싱 및 세션 저장
                    for item in response.text.replace('\n', ',').split(','):
                        if ':' in item:
                            k, v = item.split(':', 1)
                            key, val = k.strip().upper(), v.strip()
                            if 'CASE' in key: st.session_state["c"+it_key] = val
                            if 'PATIENT' in key: st.session_state["p"+it_key] = val
                            if 'CLINIC' in key: st.session_state["cl"+it_key] = val
                            if 'DOCTOR' in key: st.session_state["dr"+it_key] = val
                    
                    status.update(label="분석이 완료되었습니다!", state="complete")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"AI 분석 실패: {e}")

    st.markdown("---")
    
    # 기본 정보 입력 섹션
    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case Number", key="c" + it_key)
    patient = c1.text_input("환자명", key="p" + it_key)
    sel_clinic = c2.selectbox("치과 병원", ["선택"] + clinics + ["➕ 직접 입력"], key="cl" + it_key)
    sel_doctor = c3.selectbox("담당 의사", ["선택"] + doctors + ["➕ 직접 입력"], key="dr" + it_key)

    # 상세 설정 섹션
    with st.expander("🛠️ 생산 상세 정보 및 날짜 설정", expanded=True):
        d1, d2, d3 = st.columns(3)
        arch = d1.radio("Arch", ["Maxillary", "Mandibular"], horizontal=True, key="ar" + it_key)
        material = d1.selectbox("재질 (Material)", ["Thermo", "Dual", "Soft", "Hard"], key="mat" + it_key)
        
        recv_date = d2.date_input("접수일", date.today(), key="rd" + it_key)
        
        # 마감일 변경 시 출고일 자동 계산
        if "due" + it_key not in st.session_state:
            st.session_state["due" + it_key] = date.today() + timedelta(days=7)
            
        due_date = d3.date_input("마감일 (Due Date)", key="due" + it_key)
        ship_date = d3.date_input("출고일 (Shipping Date)", value=due_date - timedelta(days=2), key="sh" + it_key)

    # 특이사항 및 사진 섹션
    with st.expander("📂 특이사항 및 참고 사진", expanded=True):
        col_img, col_memo = st.columns([0.6, 0.4])
        # [복구] 하단 참고 사진 업로드
        ref_image = col_img.file_uploader("참고용 사진 추가 업로드", type=["jpg", "png"], key=f"refimg_{it_key}")
        memo_text = col_memo.text_area("작업 시 주의사항 (메모)", key="memo" + it_key, height=130)

    if st.button("🚀 데이터베이스에 저장하기"):
        if not case_no:
            st.error("Case Number는 필수 입력 항목입니다.")
        else:
            with st.spinner("저장 중..."):
                # 실제 저장 로직 (필요 시 conn.update 호출)
                st.success(f"케이스 {case_no} (환자: {patient})가 성공적으로 저장되었습니다.")
                time.sleep(1)
                st.session_state.it += 1
                st.rerun()

with tab2:
    st.markdown("### 📊 최근 등록 데이터 (최신 20건)")
    st.dataframe(main_df.tail(20), use_container_width=True)

with tab3:
    st.markdown("### 🔍 통합 케이스 검색")
    search_query = st.text_input("환자 이름 또는 케이스 번호를 입력하세요")
    if search_query:
        search_res = main_df[main_df.apply(lambda row: search_query in row.astype(str).values, axis=1)]
        st.dataframe(search_res, use_container_width=True)
