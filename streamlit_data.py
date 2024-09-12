import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="美國經濟數據分析 (Jason Chan)", layout="wide")

def safe_strip(value):
    """安全地對值進行 strip 操作"""
    return value.strip() if isinstance(value, str) else value

def scrape_data(urls):
    data = []
    for url in urls:
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else "No title"
            rows = soup.find_all('tr')
            row_counter = 0
            
            for row in rows:
                if row_counter >= 6:
                    break
                cols = row.find_all('td')
                if len(cols) == 6:
                    cols_text = [safe_strip(col.text) for col in cols]
                    # 如果預測列為空，將其設置為 None
                    if cols_text[3] == '':
                        cols_text[3] = None
                    data.append([title] + cols_text)
                    row_counter += 1
        except Exception as e:
            logger.error(f"爬取 {url} 時出錯: {str(e)}")
    
    return pd.DataFrame(data, columns=['Title', 'Date', 'Time', 'Actual', 'Forecast', 'Previous', 'Importance'])

def process_data(df):
    indicators = {
        "United States Unemployment Rate": [],
        "United States Nonfarm Payrolls": [],
        "United States Average Hourly Earnings MoM": [],
        "United States Average Hourly Earnings YoY": [],
        "United States ADP Nonfarm Employment Change": [],
        "United States Core PCE Price Index YoY": [],
        "United States Core PCE Price Index MoM": [],
        "United States Consumer Price Index (CPI) YoY": [],
        "United States Consumer Price Index (CPI) MoM": [],
        "United States Core Consumer Price Index (CPI) YoY": [],
        "United States Core Consumer Price Index (CPI) MoM": [],
        "United States Core Producer Price Index (PPI) MoM": [],
        "United States Producer Price Index (PPI) MoM": [],
        "United States ISM Manufacturing PMI": [],
        "United States ISM Non-Manufacturing PMI": [],
        "United States Core Retail Sales MoM": [],
        "United States Retail Sales MoM": [],
        "United States Housing Starts": [],
        "United States Existing Home Sales": [],
        "United States New Home Sales": [],
        "United States CB Consumer Confidence": [],
        "United States Gross Domestic Product (GDP) QoQ": [],
        "United States Durable Goods Orders MoM": [],
        "United States Core Durable Goods Orders MoM": []
    }

    lower_is_better = [
        "United States Unemployment Rate",
        "United States Core PCE Price Index YoY",
        "United States Core PCE Price Index MoM",
        "United States Core Consumer Price Index (CPI) YoY",
        "United States Core Consumer Price Index (CPI) MoM",
        "United States Consumer Price Index (CPI) YoY",
        "United States Consumer Price Index (CPI) MoM",
        "United States Core Producer Price Index (PPI) MoM",
        "United States Producer Price Index (PPI) MoM"
    ]

    def parse_date(date_str):
        patterns = [
            r'(\w+ \d{2}, \d{4}) \((\w+)\)',
            r'(\w+ \d{2}, \d{4})',
            r'(\w+ \d{2}, \d{4}) \(Q\d\)'
        ]
        for pattern in patterns:
            match = re.match(pattern, date_str)
            if match:
                return datetime.strptime(match.group(1), '%b %d, %Y')
        return None

    for _, row in df.iterrows():
        indicator = row['Title'].split(' - ')[0]
        if indicator in indicators:
            date = parse_date(row['Date'])
            if date is None:
                logger.warning(f"無法解析日期: {row['Date']} 對於指標: {indicator}")
                continue

            forecast = safe_strip(row.get('Forecast', ''))
            actual = safe_strip(row.get('Actual', ''))
            
            vs_forecast = ''
            if actual and forecast and forecast != '-':
                try:
                    actual_value = float(actual.rstrip('K%M'))
                    forecast_value = float(forecast.rstrip('K%M'))
                    if indicator in lower_is_better:
                        vs_forecast = "較好" if actual_value < forecast_value else "較差" if actual_value > forecast_value else "持平"
                    else:
                        vs_forecast = "較好" if actual_value > forecast_value else "較差" if actual_value < forecast_value else "持平"
                except ValueError:
                    vs_forecast = ''
            
            indicators[indicator].append({
                "Date": date,
                "Vs Forecast": vs_forecast,
                "Forecast": forecast if forecast and forecast != '-' else None,
                "Actual": actual if actual else None
            })

    processed_data = []
    for indicator, data in indicators.items():
        if data:
            sorted_data = sorted(data, key=lambda x: x['Date'], reverse=True)
            latest = sorted_data[0]
            row = [
                indicator,
                latest['Date'].strftime("%b %d, %Y (%b)"),
                latest['Vs Forecast'],
                latest['Forecast'] if latest['Forecast'] else 'None'
            ]
            actuals = []
            for i in range(5):
                if i < len(sorted_data):
                    actuals.append(sorted_data[i].get('Actual') or 'None')
                else:
                    actuals.append('None')
            row.extend(actuals)
            processed_data.append(row)
        else:
            logging.warning(f"沒有數據用於指標: {indicator}")

    return processed_data, indicators

def create_chart(data, indicator):
    dates = [d['Date'] for d in data]
    actuals = [float(safe_strip(d['Actual']).rstrip('K%M')) if d['Actual'] and d['Actual'] not in ['', 'None'] else None for d in data]
    forecasts = [float(safe_strip(d['Forecast']).rstrip('K%M')) if d['Forecast'] and d['Forecast'] not in ['', 'None'] else None for d in data]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=dates, y=actuals, name="實際值", mode="lines+markers"),
        secondary_y=False,
    )

    # 只獲取最新的預測值
    latest_forecast = next((f for f in forecasts if f is not None), None)
    latest_date = dates[0]

    if latest_forecast is not None:
        # 只從最新日期開始繪製預測線
        forecast_dates = [d for d in dates if d <= latest_date]
        forecast_values = [latest_forecast] * len(forecast_dates)
        
        fig.add_trace(
            go.Scatter(x=forecast_dates, y=forecast_values, name="預測值(本/前月)", 
                       mode="lines", line=dict(dash="dash", color="gray")),
            secondary_y=False,
        )
        logging.info(f"繪製預測線，值為: {latest_forecast}")
    else:
        logging.info("沒有有效的預測值，不繪製預測線")

    fig.update_layout(
        title=indicator,
        xaxis_title="日期",
        yaxis_title="值",
        legend_title="圖例",
        height=400,
        width=600
    )

    return fig
    
def main():
    st.title("美國經濟數據分析(Jason Chan)")

    urls = [
        "https://www.investing.com/economic-calendar/unemployment-rate-300",
        "https://www.investing.com/economic-calendar/nonfarm-payrolls-227",
        "https://www.investing.com/economic-calendar/average-hourly-earnings-8",
        "https://www.investing.com/economic-calendar/average-hourly-earnings-1777",        
        "https://www.investing.com/economic-calendar/adp-nonfarm-employment-change-1",
        "https://www.investing.com/economic-calendar/core-pce-price-index-905",
        "https://www.investing.com/economic-calendar/core-pce-price-index-61",
        "https://www.investing.com/economic-calendar/cpi-733",
        "https://www.investing.com/economic-calendar/cpi-69",
        "https://www.investing.com/economic-calendar/core-cpi-736", 
        "https://www.investing.com/economic-calendar/core-cpi-56",        
        "https://www.investing.com/economic-calendar/core-ppi-62",
        "https://www.investing.com/economic-calendar/ppi-238",
        "https://www.investing.com/economic-calendar/ism-manufacturing-pmi-173",
        "https://www.investing.com/economic-calendar/ism-non-manufacturing-pmi-176",    
        "https://www.investing.com/economic-calendar/core-retail-sales-63",
        "https://www.investing.com/economic-calendar/retail-sales-256",
        "https://www.investing.com/economic-calendar/housing-starts-151",
        "https://www.investing.com/economic-calendar/existing-home-sales-99",
        "https://www.investing.com/economic-calendar/new-home-sales-222",
        "https://www.investing.com/economic-calendar/cb-consumer-confidence-48",
        "https://www.investing.com/economic-calendar/gdp-375",
        "https://www.investing.com/economic-calendar/durable-goods-orders-86",
        "https://www.investing.com/economic-calendar/core-durable-goods-orders-59",
    ]

    # 將爬取數據的按鈕放在主頁面
    if 'indicators' not in st.session_state:
        st.session_state.indicators = {}

    if 'processed_df' not in st.session_state:
        st.session_state.processed_df = None

    if 'raw_df' not in st.session_state:
        st.session_state.raw_df = None

    if st.button("爬取並分析數據"):
        with st.spinner("正在爬取和分析數據... 這可能需要幾分鐘。"):
            try:
                df = scrape_data(urls)
                
                if not df.empty:
                    st.success("數據爬取成功！")
                    
                    # 保存原始數據
                    st.session_state.raw_df = df
                    
                    processed_data, indicators = process_data(df)
                    
                    if processed_data:
                        st.success("數據分析成功！")
                        st.session_state.processed_df = pd.DataFrame(processed_data, columns=["指標", "數據更新", "與預測比較", "預測", "本月", "1月前", "2月前", "3月前", "4月前"])
                        st.session_state.indicators = indicators
                    else:
                        st.warning("沒有處理任何數據。請檢查數據結構。")
                else:
                    st.warning("沒有爬取到任何數據。請檢查URL並重試。")
            except Exception as e:
                st.error(f"處理過程中發生錯誤: {str(e)}")
                logger.exception("處理過程中發生錯誤")

    if st.session_state.raw_df is not None:
        with st.expander("點擊查看原始數據"):
            st.subheader("原始數據")
            st.dataframe(st.session_state.raw_df)
        
        # 添加下載原始數據的按鈕
        csv_raw = st.session_state.raw_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="下載原始數據為CSV",
            data=csv_raw,
            file_name="raw_us_economic_data.csv",
            mime="text/csv",
        )

    if st.session_state.processed_df is not None:
        st.subheader("數據總結")
        
        def color_rows(row):
            if row.name < 5:  # 就業數據
                return ['background-color: #FFFFE0'] * len(row)
            elif 5 <= row.name < 12:  # 通貨膨脹數據
                return ['background-color: #E6E6FA'] * len(row)
            else:  # 其他經濟指標
                return ['background-color: #E6F3FF'] * len(row)
        
        def color_rows(row):
            if row.name < 5:  # 就業數據
                return ['background-color: #FFFFE0; text-align: center; vertical-align: middle'] * len(row)
            elif 5 <= row.name < 13:  # 通貨膨脹數據
                return ['background-color: #E6E6FA; text-align: center; vertical-align: middle'] * len(row)
            else:  # 其他經濟指標
                return ['background-color: #E6F3FF; text-align: center; vertical-align: middle'] * len(row)
        
        def color_text(val):
            if val == '較差':
                return 'color: red'
            elif val == '較好':
                return 'color: green'
            return ''

        styled_df = st.session_state.processed_df.style.apply(color_rows, axis=1)
        styled_df = styled_df.applymap(color_text, subset=['與預測比較'])
        styled_df = styled_df.set_properties(**{
            'text-align': 'center',
            'vertical-align': 'middle',
            'height': '50px'  # 調整單元格高度
        })
        
        # 創建兩列佈局
        col1, col2 = st.columns([3, 2])
        
        with col1:
            # 顯示數據表格
            st.dataframe(styled_df)
        
        with col2:
            # 創建一個空的佔位符來顯示圖表
            chart_placeholder = st.empty()
        
        # 為每個指標創建一個按鈕在側邊欄
        st.sidebar.header("選擇指標")
        for index, row in st.session_state.processed_df.iterrows():
            if st.sidebar.button(row['指標']):
                # 獲取該指標的所有數據
                indicator_data = st.session_state.indicators.get(row['指標'], [])
                indicator_data = [d for d in indicator_data if d.get('Actual')]
                if indicator_data:
                    # 創建並顯示圖表
                    fig = create_chart(indicator_data, row['指標'])
                    chart_placeholder.plotly_chart(fig)
                else:
                    chart_placeholder.warning(f"沒有找到 {row['指標']} 的有效數據")
        
        csv = st.session_state.processed_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="下載處理後的數據為CSV",
            data=csv,
            file_name="processed_us_economic_data.csv",
            mime="text/csv",
        )

    st.warning("注意：此爬蟲和分析器僅用於教育目的丶不保證資料準確性。請尊重網站的服務條款和robots.txt文件。數據來源: investing.com")

if __name__ == "__main__":
    main()
