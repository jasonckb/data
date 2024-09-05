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

def process_data(df):
    indicators = {
        "United States Unemployment Rate": [],
        "United States Nonfarm Payrolls": [],
        "United States Average Hourly Earnings MoM": [],
        "United States Average Hourly Earnings YoY": [],
        "United States ADP Nonfarm Employment Change": [],
        "United States JOLTS Job Openings": [],
        "United States ISM Manufacturing PMI": [],
        "United States ISM Non-Manufacturing PMI": [],
        "United States Core PCE Price Index YoY": [],
        "United States Core PCE Price Index MoM": [],
        "United States PCE Price Index YoY": [],
        "United States Consumer Price Index (CPI) MoM": [],
        "United States Core Consumer Price Index (CPI) YoY": [],
        "United States Consumer Price Index (CPI) YoY": [],
        "United States Core Producer Price Index (PPI) MoM": [],
        "United States Producer Price Index (PPI) MoM": [],
        "United States Gross Domestic Product (GDP) Price Index QoQ": [],
        "United States Core Retail Sales MoM": [],
        "United States Retail Sales MoM": [],
        "United States Housing Starts": [],
        "United States Existing Home Sales": [],
        "United States New Home Sales": [],
        "United States CB Consumer Confidence": [],
        "United States Gross Domestic Product (GDP) QoQ": [],
        "United States Durable Goods Orders MoM": [],
        "United States Core Durable Goods Orders MoM": [],
        "United States Building Permits": []
    }

    for _, row in df.iterrows():
        indicator = row['Title'].split(' - ')[0]
        if indicator in indicators:
            date = datetime.strptime(row['Date'], "%b %d, %Y")
            forecast = row['Forecast']
            actual = row['Actual']
            
            try:
                vs_forecast = "Better Off" if float(actual.rstrip('K%M')) > float(forecast.rstrip('K%M')) else "Worse Off"
            except ValueError:
                vs_forecast = "Par"
            
            indicators[indicator].append({
                "Date": date,
                "Vs Forecast": vs_forecast,
                "Forecast": forecast,
                "Actual": actual
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
                latest['Forecast']
            ]
            row.extend([d['Actual'] if i < len(sorted_data) else '' for i in range(5)])
            processed_data.append(row)

    return processed_data

def main():
    if st.button("Analyze Data"):
        with st.spinner("Analyzing data... This may take a few minutes."):
            df = scrape_data(urls)  # 假設這個函數已經實現
            
            if not df.empty:
                st.success("Data analyzed successfully!")
                
                processed_data = process_data(df)
                
                columns = ["Indicator", "Data Update", "Vs Forecast", "Forecast", "0", "1", "2", "3", "4"]
                processed_df = pd.DataFrame(processed_data, columns=columns)
                
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
