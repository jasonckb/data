import requests
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
import time

# The URLs of the webpages you want to scrape
urls = ["https://www.investing.com/economic-calendar/unemployment-rate-300",
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

def scrape_investing_com(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract the indicator name
    indicator = soup.find('h1', class_='ecTitle').text.strip()
    
    # Find the table with historical data
    table = soup.find('table', id='eventHistoryTable')
    
    if table:
        rows = table.find_all('tr')[1:]  # Skip the header row
        data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                date = cols[0].text.strip()
                actual = cols[1].text.strip()
                forecast = cols[2].text.strip()
                previous = cols[3].text.strip()
                data.append([date, actual, forecast, previous])
        
        df = pd.DataFrame(data, columns=['Date', 'Actual', 'Forecast', 'Previous'])
        return indicator, df
    else:
        return indicator, pd.DataFrame()

def main():
    st.title("US Economic Data Dashboard")
    
    st.sidebar.header("Select Economic Indicators")
    selected_urls = st.sidebar.multiselect(
        "Choose indicators",
        urls,
        format_func=lambda x: x.split('/')[-1].replace('-', ' ').title()
    )
    
    if selected_urls:
        for url in selected_urls:
            indicator, data = scrape_investing_com(url)
            st.header(f"{indicator} Data")
            
            if not data.empty:
                st.dataframe(data)
                
                # Convert 'Actual' to numeric, removing any non-numeric characters
                data['Actual'] = pd.to_numeric(data['Actual'].replace('[^\d.-]', '', regex=True), errors='coerce')
                
                # Create a line chart if 'Actual' column is numeric
                if data['Actual'].notna().any():
                    st.line_chart(data.set_index('Date')['Actual'])
                else:
                    st.write("Unable to create chart: 'Actual' column not numeric")
            else:
                st.error(f"No data available for {indicator}")
            
            # Add a delay to avoid overwhelming the server
            time.sleep(1)

if __name__ == "__main__":
    main()