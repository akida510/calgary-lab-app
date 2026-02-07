# 인보이스 레이아웃 (중앙 깨짐 방지 보강판)
        st.markdown(f"""
        <div class="invoice-container">
            <div style="display: flex; justify-content: space-between; margin-bottom: 30px;">
                <div>
                    <span style="font-size:10px; font-weight:bold;">DENTAL TECHNOLOGY Ltd</span><br>
                    <span style="font-size:48px; font-weight:900; font-style:italic; color:#1a4e8a; letter-spacing:-2px; line-height:1;">skycad</span><br>
                    <div style="margin-top:15px; font-size:12px;">
                        <b>Skycad AB</b><br>205-7136 11 St NE<br>Calgary, AB T2E 4Y9<br>(403) 970-0600
                    </div>
                </div>
                <div style="text-align: right;">
                    <h1 style="font-size:35px; margin:0; font-weight:400; letter-spacing:3px;">INVOICE</h1>
                    <p style="font-size:14px; margin-top:5px;">No. {inv['Case No'].replace('ET','')}<br>{inv['Lab Done'].strftime('%d/%m/%Y')}</p>
                    <div style="text-align:left; margin-top:15px; font-size:13px; border:1px solid #ddd; padding:10px; width:220px; display: inline-block;">
                        <b>Ship To:</b><br>{inv['Clinic']}<br>{inv['Doctor']}<br>{inv['Addr']}<br>{inv['City']}
                    </div>
                </div>
            </div>

            <div style="margin-top:40px; font-size:16px; width:100%; display:block; clear:both;">
                <b>Patient:</b> {str(inv['Patient']).upper()}
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-top: 20px; border-top: 2px solid black; border-bottom: 2px solid black;">
                <thead>
                    <tr style="border-bottom: 1px solid black;">
                        <th style="padding: 10px 5px; text-align: left;">Description</th>
                        <th style="padding: 10px 5px; text-align: right;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td style="padding: 20px 5px; vertical-align: top; min-height: 350px; height: 350px;">
                            Nightguard ({inv['Material']}) {inv['Arch']}
                        </td>
                        <td style="padding: 20px 5px; vertical-align: top; text-align: right;">
                            $180.00
                        </td>
                    </tr>
                </tbody>
            </table>

            <div style="display: flex; justify-content: space-between; padding: 10px 5px; border-top: 2px solid black; font-weight: bold; font-size: 17px; margin-bottom: 40px;">
                <span>{inv['Case No']}</span>
                <span>Total: $180.00</span>
            </div>

            <div style="margin-top: 60px; text-align: center; clear: both;">
                <span style="font-size: 18px; font-weight: bold; text-decoration: underline; display: block; margin-bottom: 15px;">
                    All dental products we offer are custom made in Canada.
                </span>
                <p style="font-size: 12.5px; line-height: 1.6; color: black !important; padding: 0 30px;">
                    Please ensure your monthly payment is made within 30 days of receiving your statement. Any balances remaining after 30 days will be automatically charged to the credit card on file. Otherwise, any balances over 30 days will be subject to a finance charge of 1.5% per month. This has an equivalent rate of 19.562% APR. Thank you.
                </p>
            </div>
            
            <div style="margin-top:80px; clear: both;">
                <div style="border-top:1px solid black; width:200px; padding-top:5px; font-size:12px;">Authorized Signature</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
