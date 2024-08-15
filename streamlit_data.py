import streamlit as st
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

def fetch_page_content(url):
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, wait_until="networkidle")
            page.wait_for_selector('#eventHistoryTable', state="attached", timeout=30000)
            content = page.content()
            browser.close()
        return content
    except Exception as e:
        logger.error(f"Error fetching {url}: {str(e)}")
        return None

@st.cache_data
def scrape_investing_com(url):
    content = fetch_page_content(url)
    
    if content is None:
        return pd.DataFrame()
    
    soup = BeautifulSoup(content, 'html.parser')
    table = soup.find('table', {'id': 'eventHistoryTable'})
    
    if not table:
        logger.warning(f"No table found for {url}")
        return pd.DataFrame()
    
    data = []
    rows = table.find_all('tr')
    for row in rows[1:7]:  # Get first 6 data rows
        cols = row.find_all('td')
        if len(cols) >= 6:
            date = cols[0].text.strip()
            time = cols[1].text.strip()
            actual = cols[2].text.strip()
            forecast = cols[3].text.strip()
            previous = cols[4].text.strip()
            data.append([date, time, actual, forecast, previous])
    
    if not data:
        logger.warning(f"No data rows found for {url}")
        return pd.DataFrame()
    
    df = pd.DataFrame(data, columns=['Date', 'Time', 'Actual', 'Forecast', 'Previous'])
    indicator_element = soup.find('h1', {'class': 'ecTitle'})
    df['Indicator'] = indicator_element.text.strip() if indicator_element else 'Unknown Indicator'
    
    logger.info(f"Successfully scraped data for {url}")
    return df

def main():
    st.title("US Economic Data Dashboard")
    
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
                df = scrape_investing_com(url)
                if not df.empty:
                    all_data.append(df)
                    st.subheader(f"{indicator_name} Data")
                    st.dataframe(df)
                    
                    if 'Actual' in df.columns:
                        df['Actual'] = pd.to_numeric(df['Actual'].replace('[^\d.-]', '', regex=True), errors='coerce')
                        if df['Actual'].notna().any():
                            st.line_chart(df.set_index('Date')['Actual'])
                        else:
                            st.write("Unable to create chart: 'Actual' column not numeric")
                else:
                    st.warning(f"No data available for {indicator_name}")
            
            time.sleep(2)  # Add a delay to prevent getting blocked
        
        if all_data:
            combined_df = pd.concat(all_data)
            csv = combined_df.to_csv(index=False)
            st.download_button(
                label="Download all data as CSV",
                data=csv,
                file_name="US_economic_data.csv",
                mime="text/csv",
            )
        else:
            st.error("No data was successfully retrieved for any selected indicator.")

if __name__ == "__main__":
    main()