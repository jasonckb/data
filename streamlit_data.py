import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import logging
import json
from urllib.parse import urlencode

# Set up logging
logging.basicConfig(level=logging.DEBUG)
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


@st.cache_data
def scrape_investing_com(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    try:
        # First, get the main page to extract necessary parameters
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract the event ID from the URL
        event_id = url.split('-')[-1]
        
        # Find the smlID parameter
        sml_id = soup.find('div', {'id': 'eventHistoryTable'})
        if sml_id:
            sml_id = sml_id.get('data-sml-id')
        else:
            logger.error(f"Could not find smlID for {url}")
            return pd.DataFrame()
        
        # Construct the API URL
        api_url = "https://www.investing.com/economic-calendar/Service/getCalendarFilteredData"
        
        # Prepare the POST data
        post_data = {
            "country[]": "5",  # 5 is the code for United States
            "eventID": event_id,
            "timeZone": 8,
            "timeFilter": "timeRemain",
            "currentTab": "custom",
            "limit_from": 0,
            "smlID": sml_id
        }
        
        # Make the POST request
        response = requests.post(api_url, headers=headers, data=urlencode(post_data))
        response.raise_for_status()
        
        # Parse the JSON response
        data = json.loads(response.text)
        
        if 'data' not in data:
            logger.error(f"No data found in response for {url}")
            return pd.DataFrame()
        
        # Extract the rows from the HTML in the response
        soup = BeautifulSoup(data['data'], 'html.parser')
        rows = soup.find_all('tr')
        
        parsed_data = []
        for row in rows:
            cols = row.find_all('td')
            if len(cols) >= 4:
                date = cols[0].text.strip()
                actual = cols[1].text.strip()
                forecast = cols[2].text.strip()
                previous = cols[3].text.strip()
                parsed_data.append([date, actual, forecast, previous])
        
        if not parsed_data:
            logger.warning(f"No data rows found for {url}")
            return pd.DataFrame()
        
        df = pd.DataFrame(parsed_data, columns=['Date', 'Actual', 'Forecast', 'Previous'])
        df['Indicator'] = soup.find('h1').text.strip() if soup.find('h1') else "Unknown Indicator"
        
        logger.info(f"Successfully scraped data for {url}")
        return df
    
    except requests.RequestException as e:
        logger.error(f"Error fetching data from {url}: {str(e)}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Unexpected error processing {url}: {str(e)}")
        return pd.DataFrame()

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
                    
                    # Attempt to create a line chart
                    if 'Actual' in df.columns:
                        df['Actual'] = pd.to_numeric(df['Actual'].replace('[^\d.-]', '', regex=True), errors='coerce')
                        if df['Actual'].notna().any():
                            st.line_chart(df.set_index('Date')['Actual'])
                        else:
                            st.write("Unable to create chart: 'Actual' column not numeric")
                else:
                    st.warning(f"No data available for {indicator_name}")
        
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
        else:
            st.error("No data was successfully retrieved for any selected indicator.")

if __name__ == "__main__":
    main()