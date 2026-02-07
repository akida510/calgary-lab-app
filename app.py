import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date

st.set_page_config(page_title="Skycad Lab Manager", layout="wide")

# 다크모드 차단 및 글자색 강제 고정 스타일
st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    .invoice-wrapper { display: flex; justify-content: center; padding: 20px; background-color: #262730; }
    
    .invoice-paper {
        background-color: #ffffff !important;
        width: 100%; max-width: 800px; 
        aspect-ratio: 8.5 / 11; padding: 60px 50px; border: 1px solid #000;
        box-shadow: 0 10px 25px rgba(0,0,0,0.5); display: flex; flex-direction: column; box-sizing: border-box;
    }
    
    /* 코드 글자로 보이지 않도록 모든 요소에 대해 검정색 및 스타일 강제 */
    .invoice-paper * {
        color: #000000 !important; 
        -webkit-text-fill-color: #000000 !important;
        font-family: 'Arial', sans-serif !important;
        text-align: left;
    }
    
    .logo-main { 
        font-size: 58px !important; font-weight: 900 !important; font-style: italic !important; 
        color: #1a4e8a !important; -webkit-text-fill-color: #1a4e8a !important;
    }
    
    .patient-line { 
        margin: 25px 0 !important; padding: 15px 0 !important; 
        border-top: 2.5px solid black !important; border-bottom: 2.5px solid black !important; 
        font-size: 20px !important; font-weight: bold !important; 
    }
    
    .item-table { width: 100% !important; border-collapse: collapse !important; flex-grow: 1 !important; }
    .item-table th { border-bottom: 1.5px solid black !important; padding: 10px 0 !important; }
    .item-table td { padding: 25px 0 !important; font-size: 17px !important; }
    
    .bottom-box { margin-top: auto !important; }
    .notice-box { border: 1.5px solid black !important; padding: 20px !important; text-align: center !important; }
    .notice-box * { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# [데이터 및 세션 관리 생략 - 이전 버전과 동일]
if 'db' not in st.session_state: st.session_state.db = []
if 'selected_invoice' not in st.session_state: st.session_state.selected_invoice = None

# ... (등록/리스트 로직은 동일하게 유지) ...

# 인보이스 출력 부분 (이 부분이 f-string 오류 없이 렌더링되도록 확인)
if st.session_state.selected_invoice:
    inv = st.session_state.selected_invoice
    st.markdown('<div class="invoice-wrapper">', unsafe_allow_html=True)
    
    # HTML 구조를 변수에 담아 한 번에 출력
    full_html = f"""
    <div class="invoice-paper">
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 50px;">
            <div style="flex: 1;">
                <p style="font-size:10px; font-weight:bold; margin-bottom:5px;">DENTAL TECHNOLOGY LTD</p>
                <h1 class="logo-main">skycad</h1>
                <p style="font-size:14px; line-height:1.3;">Skycad AB<br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600</p>
            </div>
            <div style="flex: 1; text-align: right;">
                <h1 style="font-size:42px; font-weight:500; margin-bottom:15px;">INVOICE</h1>
                <p style="font-size:16px;">No. 162084</p>
                <p style="font-size:16px; margin-bottom:25px;">{date.today().strftime('%-m/%-d/%Y')}</p>
                <div style="text-align:left; display:inline-block; font-size:14px;">
                    <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Address']}<br>{inv['Phone']}
                </div>
            </div>
        </div>
        
        <div class="patient-line">Patient: &nbsp; {inv['Patient'].upper()}</div>
        
        <table class="item-table">
            <thead>
                <tr>
                    <th style="text-align:left;">Description</th>
                    <th style="text-align:right;">Amount</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="padding:25px 0;">Nightguard ({inv['Material']}) {inv['Arch']}</td>
                    <td style="text-align:right;">$180.00</td>
                </tr>
            </tbody>
        </table>
        
        <div class="bottom-box">
            <div style="display:flex; justify-content:space-between; font-weight:bold; font-size:20px; margin-bottom:15px; border-top:1px solid #eee; padding-top:10px;">
                <div>{inv['Case No']}</div>
                <div>Total: $180.00</div>
            </div>
            <div class="notice-box">
                <u style="font-weight:bold; display:block; margin-bottom:10px; font-size:15px; text-align:center;">All dental products we offer are custom made in Canada.</u>
                <p style="font-size:11.5px; line-height:1.5; text-align:center;">Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.552% APR, Thank you.</p>
            </div>
        </div>
    </div>
    """
    st.markdown(full_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
