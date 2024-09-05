import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="US Economic Data Scraper", layout="wide")
st.title("US Economic Data Scraper")

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

if st.button("Scrape Data"):
    with st.spinner("Scraping data... This may take a few minutes."):
        df = scrape_data(urls)
    
    if not df.empty:
        st.success("Data scraped successfully!")
        st.dataframe(df)
        
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download data as CSV",
            data=csv,
            file_name="us_economic_data.csv",
            mime="text/csv",
        )
    else:
        st.warning("No data was scraped. Please check the URLs and try again.")

st.warning("Note: This scraper is for educational purposes only. Please respect the website's terms of service and robots.txt file.")

# 處理數據函數
def process_data(df, current_date):
    processed_data = []
    for _, row in df.iterrows():
        indicator = row['Indicator']
        date_str = row['Date']
        try:
            date = datetime.strptime(date_str, "%b %d, %Y")
        except ValueError:
            # 如果日期格式不匹配，跳過這一行
            continue
        
        if date > current_date:
            # 如果數據日期在未來，使用上個月的數據
            date = date.replace(month=date.month-1)
        
        forecast = row['Forecast']
        actual = row['Actual']
        
        try:
            vs_forecast = "Better Off" if float(actual.rstrip('K%M')) > float(forecast.rstrip('K%M')) else "Worse Off"
        except ValueError:
            vs_forecast = "N/A"
        
        processed_row = [indicator, date.strftime("%b %d, %Y"), vs_forecast, forecast, actual, row['Previous']]
        processed_data.append(processed_row)
    
    return processed_data

# 主應用
def main():
    if st.button("Scrape and Analyze Data"):
        with st.spinner("Scraping and analyzing data... This may take a few minutes."):
            df = scrape_data(urls)
            
            if not df.empty:
                st.success("Data scraped successfully!")
                
                # 獲取當前日期
                current_date = datetime.now()
                
                # 處理數據
                processed_data = process_data(df, current_date)
                
                # 創建 DataFrame
                processed_df = pd.DataFrame(processed_data, columns=["Indicator", "Data Update", "Vs Forecast", "Forecast", "Actual", "Previous"])
                
                # 顯示表格
                st.dataframe(processed_df.style.apply(lambda x: ['background: pink' if x['Vs Forecast'] == 'Worse Off' else 'background: lightgreen' if x['Vs Forecast'] == 'Better Off' else '' for i in x], axis=1))
                
                csv = processed_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download processed data as CSV",
                    data=csv,
                    file_name="processed_us_economic_data.csv",
                    mime="text/csv",
                )
            else:
                st.warning("No data was scraped. Please check the URLs and try again.")

    st.warning("Note: This scraper is for educational purposes only. Please respect the website's terms of service and robots.txt file.")

if __name__ == "__main__":
    main()
