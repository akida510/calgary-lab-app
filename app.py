import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Calgary Lab Manager", layout="centered")

# --- 보안 키 줄바꿈 강제 교정 로직 ---
if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
    # 폰 복사 시 발생하는 \n 문자 깨짐 방지
    raw_key = st.secrets["connections"]["gsheets"]["private_key"]
    if "\\n" in raw_key:
        st.secrets["connections"]["gsheets"]["private_key"] = raw_key.replace("\\n", "\n")

# 구글 시트 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(ttl=0)
    ref_df = conn.read(worksheet="Reference", ttl=0)
    st.success("✅ 시스템 연결 성공!")
except Exception as e:
    st.error("🔑 연결 실패: Secrets 설정을 확인해 주세요.")
    st.stop() # 에러 시 실행 중단

# ... (이후 탭 구성 로직은 동일) ...
