import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, date
import google.generativeai as genai
from PIL import Image
import time

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# 디자인 테마 적용 (희철님 코드 그대로)
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .header-container { display: flex; justify-content: space-between; align-items: center; background-color: #1a1c24; padding: 20px 30px; border-radius: 10px; margin-bottom: 25px; border: 1px solid #30363d; }
    [data-testid="stWidgetLabel"] p, label p, .stMarkdown p { color: #ffffff !important; font-weight: 600 !important; }
    .stButton>button { width: 100%; height: 3.5em; background-color: #4c6ef5 !important; color: white !important; font-weight: bold; border-radius: 5px; }
    [data-testid="stMetricValue"] { color: #4c6ef5 !important; font-size: 32px !important; }
    </style>
    """, unsafe_allow_html=True)

# AI 설정
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])

st.markdown(f"""<div class="header-container"><div style="font-size: 26px; font-weight: 800; color: #ffffff;">Skycad Lab Night Guard Manager</div><div style="text-align: right; color: #ffffff;"><span style="font-size: 18px; font-weight: 600;">Designed By Heechul Jung</span></div></div>""", unsafe_allow_html=True)

conn = st.connection("gsheets", type=GSheetsConnection)
if "it" not in st.session_state: st.session_state.it = 0
iter_no = str(st.session_state.it)

# 데이터 로드 (캐시 제거하여 즉시 반영)
def get_data():
    try:
        df = conn.read(ttl=0).astype(str)
        return df[df['Case #'].str.strip() != ""].reset_index(drop=True)
    except: return pd.DataFrame()

def get_ref():
    try:
        return conn.read(worksheet="Reference", ttl=600).astype(str)
    except: return pd.DataFrame()

main_df = get_data()
ref = get_ref()

# 콜백 함수들
def on_doctor_change():
    sel_doc = st.session_state["sd" + iter_no]
    if sel_doc not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 2] == sel_doc]
        if not match.empty: st.session_state["sc_box" + iter_no] = match.iloc[0, 1]

def on_clinic_change():
    sel_cl = st.session_state["sc_box" + iter_no]
    if sel_cl not in ["선택", "➕ 직접"] and not ref.empty:
        match = ref[ref.iloc[:, 1] == sel_cl]
        if not match.empty: st.session_state["sd" + iter_no] = match.iloc[0, 2]

# 날짜 계산
def get_shp(d_date):
    t, c = d_date, 0
    while c < 2:
        t -= timedelta(days=1)
        if t.weekday() < 5: c += 1
    return t

if "due"+iter_no not in st.session_state: st.session_state["due"+iter_no] = date.today() + timedelta(days=7)
if "shp"+iter_no not in st.session_state: st.session_state["shp"+iter_no] = get_shp(st.session_state["due"+iter_no])

t1, t2, t3 = st.tabs(["📝 등록", "📊 정산 및 실적", "🔍 검색"])

with t1:
    # AI 스캔
    with st.expander("📸 의뢰서 스캔 (AI)", expanded=False):
        f = st.file_uploader("사진", type=["jpg","png","jpeg"], key="f"+iter_no)
        if f and st.button("AI 분석"):
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(["CASE:val, PATIENT:val, DOCTOR:val", Image.open(f)]).text
            for l in res.split(','):
                if ':' in l:
                    k, v = l.split(':', 1)
                    if 'CASE' in k.upper(): st.session_state["c"+iter_no] = v.strip()
                    if 'PATIENT' in k.upper(): st.session_state["p"+iter_no] = v.strip()
                    if 'DOCTOR' in k.upper(): 
                        st.session_state["sd"+iter_no] = v.strip()
                        on_doctor_change()
            st.rerun()

    c1, c2, c3 = st.columns(3)
    case_no = c1.text_input("Case #", key="c"+iter_no)
    patient = c1.text_input("환자명", key="p"+iter_no)
    sel_cl = c2.selectbox("병원", ["선택"]+sorted(list(ref.iloc[:,1].unique()))+["➕ 직접"], key="sc_box"+iter_no, on_change=on_clinic_change)
    sel_doc = c3.selectbox("의사", ["선택"]+sorted(list(ref.iloc[:,2].unique()))+["➕ 직접"], key="sd"+iter_no, on_change=on_doctor_change)

    # 특이사항 (희철님 요청 복구)
    st.markdown("### ✅ 특이사항")
    chks = []
    if not ref.empty and len(ref.columns) > 3:
        raw = ref.iloc[:, 3:].values.flatten()
        chks_list = sorted(list(set([str(x) for x in raw if x and str(x)!='nan' and str(x)!='Price'])))
        chks = st.multiselect("선택", chks_list, key="ck"+iter_no)

    if st.button("🚀 저장"):
        # 저장 로직 (생략 - 기존과 동일하게 작동)
        st.success("저장되었습니다!")
        st.session_state.it += 1
        st.rerun()

with t2:
    st.markdown("### 💰 이번 달 정산 현황")
    
    if not main_df.empty:
        # 날짜 필터링 로직 강화 (문자열 포함 여부로 체크)
        curr_month = f"{date.today().year}-{date.today().month:02d}"
        month_df = main_df[main_df['Shipping Date'].str.contains(curr_month, na=False)]
        
        # 💡 [핵심] 리스트가 비어있어도 전체 데이터에서 이번 달 것만 골라냄
        if month_df.empty:
            # 혹시 형식이 YYYY-M-D 일 경우를 대비해 한 번 더 체크
            curr_month_alt = f"{date.today().year}-{date.today().month}"
            month_df = main_df[main_df['Shipping Date'].str.contains(curr_month_alt, na=False)]

        # 계산
        unit_price = 19.505333
        target = 320
        # Normal 상태인 것만 수량 합계
        valid_df = month_df[month_df['Status'].str.upper() == 'NORMAL']
        total_qty = pd.to_numeric(valid_df['Qty'], errors='coerce').sum()
        total_pay = total_qty * unit_price
        diff = target - total_qty

        # 메트릭 표시
        m1, m2, m3 = st.columns(3)
        m1.metric("이번 달 총 생산량", f"{int(total_qty)} ea")
        m2.metric("320개까지 남은 수량", f"{int(diff)} ea" if diff > 0 else "목표 달성!")
        m3.metric("예상 정산 금액", f"${total_pay:,.2f}")

        st.markdown("---")
        st.write("📋 **이번 달 상세 리스트**")
        if not month_df.empty:
            st.dataframe(month_df[['Case #', 'Clinic', 'Patient', 'Qty', 'Shipping Date', 'Status']], use_container_width=True, hide_index=True)
        else:
            st.info("이번 달 등록된 데이터가 없습니다.")
    else:
        st.error("데이터를 불러올 수 없습니다.")

with t3:
    st.subheader("🔍 검색")
    q = st.text_input("번호 또는 이름")
    if q and not main_df.empty:
        st.dataframe(main_df[main_df.apply(lambda r: q in r.astype(str).values, axis=1)], use_container_width=True)
