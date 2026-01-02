import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta
import time
from PIL import Image, ImageDraw, ImageFont
import io

# 1. 페이지 설정
st.set_page_config(page_title="Skycad Lab Night Guard Manager", layout="wide")

st.markdown(
    """
    <div style="display: flex; align-items: baseline;">
        <h1 style="margin-right: 15px;">🦷 Skycad Lab Night Guard Manager</h1>
        <span style="font-size: 0.9rem; color: #888;">Designed by Heechul Jung</span>
    </div>
    """, 
    unsafe_allow_html=True
)

# 2. 데이터 연결 및 초기화
conn = st.connection("gsheets", type=GSheetsConnection)

if "iter_count" not in st.session_state:
    st.session_state.iter_count = 0

# 마감일 -> 출고일 자동 연동 로직
def update_shipping_date():
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)

if 'due_key' not in st.session_state:
    st.session_state.due_key = datetime.now().date() + timedelta(days=7)
if 'ship_key' not in st.session_state:
    st.session_state.ship_key = st.session_state.due_key - timedelta(days=2)

def force_reset():
    st.session_state.iter_count += 1
    st.cache_data.clear()
    st.rerun()

# 데이터 로드 및 노이즈(시트 하단 계산식 등) 필터링
def get_full_data():
    try:
        df = conn.read(ttl=0)
        if df is None or df.empty:
            return pd.DataFrame()
        
        # 문자열 정리 및 00:00:00 제거
        df = df.astype(str).apply(lambda x: x.str.replace(' 00:00:00', '', regex=False).str.strip())
        
        # 노이즈 필터링: Case #가 유효하지 않은 행(통계, 계산식 등) 제거
        # "Deliver", "Remake", "작업량" 등 시트 하단에 적힌 텍스트들이 Case # 열에 있으면 제외
        df = df[
            (df['Case #'] != "") & 
            (df['Case #'] != "nan") &
            (~df['Case #'].str.contains("Deliver|Remake|작업량|세후|할당량|Month|Year|NAME", na=False))
        ]
        
        df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

m_df = get_full_data()
ref_df = conn.read(worksheet="Reference", ttl=300).astype(str)

t1, t2, t3 = st.tabs(["📝 케이스 등록", "💰 이번 달 정산", "🔍 케이스 검색"])

# --- [TAB 1: 케이스 등록] ---
with t1:
    it = st.session_state.iter_count
    st.subheader("📋 새 케이스 정보 입력")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        case_no = st.text_input("Case # *", key=f"c_{it}")
        patient = st.text_input("Patient Name *", key=f"p_{it}")
    with c2:
        cl_list = sorted([c for c in ref_df.iloc[:, 1].unique() if c and str(c).lower() not in ['nan', 'clinic']])
        sel_cl = st.selectbox("Clinic *", ["선택"] + cl_list + ["➕ 직접"], key=f"cl_sel_{it}")
        f_cl = st.text_input("클리닉명 입력", key=f"fcl_{it}") if sel_cl == "➕ 직접" else sel_cl
    with c3:
        doc_opts = ["선택", "➕ 직접"]
        if sel_cl not in ["선택", "➕ 직접"]:
            docs = ref_df[ref_df.iloc[:, 1] == sel_cl].iloc[:, 2].unique()
            doc_opts += sorted([d for d in docs if d and str(d).lower() != 'nan'])
        sel_doc = st.selectbox("Doctor", doc_opts, key=f"doc_sel_{it}")
        f_doc = st.text_input("의사명 입력", key=f"fdoc_{it}") if sel_doc == "➕ 직접" else sel_doc

    with st.expander("⚙️ 작업
