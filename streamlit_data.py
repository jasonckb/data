import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

st.set_page_config(page_title="US Economic Data Scraper", layout="wide")
st.title("US Economic Data Scraper")

@st.cache_data
def scrape_data(urls):
    data = []
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        title = soup.title.string
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
    
    st.success("Data scraped successfully!")
    st.dataframe(df)
    
    csv = df.to_csv(index=False)
    st.download_button(
        label="Download data as CSV",
        data=csv,
        file_name="us_economic_data.csv",
        mime="text/csv",
    )

st.warning("Note: This scraper is for educational purposes only. Please respect the website's terms of service and robots.txt file.")
