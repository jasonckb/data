import streamlit as st
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time

# Setup Playwright browser
@st.cache_resource
def get_browser():
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=True)
    return browser

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

def scrape_investing_com(url, browser):
    page = browser.new_page()
    page.goto(url)
    time.sleep(2)  # Wait for the page to load
    
    html = page.content()
    soup = BeautifulSoup(html, 'html.parser')
    
    title = soup.title.string
    rows = soup.find_all('tr')
    
    data = []
    row_counter = 0
    
    for row in rows:
        if row_counter >= 6:
            break
        
        cols = row.find_all('td')
        
        if len(cols) == 6:
            cols_text = [col.text.strip() for col in cols]
            data.append([title] + cols_text)
            row_counter += 1
    
    page.close()
    return pd.DataFrame(data, columns=['Indicator', 'Date', 'Time', 'Actual', 'Forecast', 'Previous'])

def main():
    st.title("US Economic Data Dashboard")
    
    browser = get_browser()
    
    st.sidebar.header("Select Economic Indicators")
    selected_urls = st.sidebar.multiselect(
        "Choose indicators",
        urls,
        format_func=lambda x: x.split('/')[-1].replace('-', ' ').title()
    )
    
    if selected_urls:
        all_data = []
        for url in selected_urls:
            indicator_name = url.split('/')[-1].replace('-', ' ').title()
            with st.spinner(f'Fetching data for {indicator_name}...'):
                df = scrape_investing_com(url, browser)
                all_data.append(df)
            
            st.subheader(f"{indicator_name} Data")
            st.dataframe(df)
            
            # Attempt to create a line chart
            if 'Actual' in df.columns:
                df['Actual'] = pd.to_numeric(df['Actual'].replace('[^\d.-]', '', regex=True), errors='coerce')
                if df['Actual'].notna().any():
                    st.line_chart(df.set_index('Date')['Actual'])
                else:
                    st.write("Unable to create chart: 'Actual' column not numeric")
        
        # Combine all data and offer download
        if all_data:
            combined_df = pd.concat(all_data)
            csv = combined_df.to_csv(index=False)
            st.download_button(
                label="Download all data as CSV",
                data=csv,
                file_name="US_economic_data.csv",
                mime="text/csv",
            )
    
    browser.close()

if __name__ == "__main__":
    main()