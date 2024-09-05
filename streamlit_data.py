import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="US Economic Data Scraper and Analyzer", layout="wide")
st.title("US Economic Data Scraper and Analyzer")

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
                    cols_text = [col.text.strip() for col in cols]
                    data.append([title] + cols_text)
                    row_counter += 1
        except Exception as e:
            st.error(f"Error scraping {url}: {str(e)}")
    
    return pd.DataFrame(data, columns=['Title', 'Date', 'Time', 'Actual', 'Forecast', 'Previous', 'Importance'])

urls = [
    "https://www.investing.com/economic-calendar/unemployment-rate-300",
    "https://www.investing.com/economic-calendar/nonfarm-payrolls-227",
    "https://www.investing.com/economic-calendar/average-hourly-earnings-8",
    "https://www.investing.com/economic-calendar/average-hourly-earnings-1777",        
    "https://www.investing.com/economic-calendar/adp-nonfarm-employment-change-1",
    "https://www.investing.com/economic-calendar/jolts-job-openings-1057",
    "https://www.investing.com/economic-calendar/ism-manufacturing-pmi-173",
    "https://www.investing.com/economic-calendar/ism-non-manufacturing-pmi-176",    
    "https://www.investing.com/economic-calendar/core-pce-price-index-905",
    "https://www.investing.com/economic-calendar/core-pce-price-index-61",
    "https://www.investing.com/economic-calendar/pce-price-index-906",
    "https://www.investing.com/economic-calendar/core-cpi-69",
    "https://www.investing.com/economic-calendar/core-cpi-736",           
    "https://www.investing.com/economic-calendar/cpi-733",
    "https://www.investing.com/economic-calendar/core-ppi-62",
    "https://www.investing.com/economic-calendar/ppi-238",
    "https://www.investing.com/economic-calendar/gdp-price-index-343",
    "https://www.investing.com/economic-calendar/core-retail-sales-63",
    "https://www.investing.com/economic-calendar/retail-sales-256",
    "https://www.investing.com/economic-calendar/building-permits-25",
    "https://www.investing.com/economic-calendar/housing-starts-151",
    "https://www.investing.com/economic-calendar/existing-home-sales-99",
    "https://www.investing.com/economic-calendar/new-home-sales-222",
    "https://www.investing.com/economic-calendar/cb-consumer-confidence-48",
    "https://www.investing.com/economic-calendar/michigan-consumer-sentiment-320",
    "https://www.investing.com/economic-calendar/gdp-375",
    "https://www.investing.com/economic-calendar/durable-goods-orders-86",
    "https://www.investing.com/economic-calendar/core-durable-goods-orders-59",
    "https://www.investing.com/economic-calendar/industrial-production-161",
    "https://www.investing.com/economic-calendar/personal-income-234"
]

def process_data(df, current_date):
    processed_data = []
    for _, row in df.iterrows():
        indicator = row['Title'].split(' - ')[0]  # 提取指標名稱
        date_str = row['Date']
        try:
            date = datetime.strptime(date_str, "%b %d, %Y")
        except ValueError:
            continue
        
        forecast = row['Forecast']
        actual = row['Actual']
        previous = row['Previous']
        
        # 計算 Vs Forecast
        try:
            vs_forecast = "Better Off" if float(actual.rstrip('K%M')) > float(forecast.rstrip('K%M')) else "Worse Off"
        except ValueError:
            vs_forecast = "Par"
        
        # 創建歷史數據列表
        historical_data = [actual, previous, '', '', '']  # 只有兩個月的數據，其餘填充空字符串
        
        processed_row = [indicator, date.strftime("%b %d, %Y (%b)"), vs_forecast, forecast] + historical_data
        processed_data.append(processed_row)
    
    return processed_data

def main():
    if st.button("Analyze Data"):
        with st.spinner("Analyzing data... This may take a few minutes."):
            df = scrape_data(urls)  # 假設這個函數已經實現
            
            if not df.empty:
                st.success("Data analyzed successfully!")
                
                current_date = datetime.now()
                processed_data = process_data(df, current_date)
                
                # 創建 DataFrame
                columns = ["Indicator", "Data Update", "Vs Forecast", "Forecast", "0", "1", "2", "3", "4"]
                processed_df = pd.DataFrame(processed_data, columns=columns)
                
                # 顯示表格
                st.dataframe(processed_df.style.apply(lambda x: ['background: pink' if x['Vs Forecast'] == 'Worse Off' 
                                                                 else 'background: lightgreen' if x['Vs Forecast'] == 'Better Off' 
                                                                 else '' for i in x], axis=1))
                
                csv = processed_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download processed data as CSV",
                    data=csv,
                    file_name="processed_us_economic_data.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No data was analyzed. Please check the data source.")

    st.warning("Note: This analyzer is for educational purposes only.")

if __name__ == "__main__":
    main()
