import streamlit as st
import investpy
import pandas as pd
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

indicators = {
    "Unemployment Rate": "Unemployment Rate",
    "Non-Farm Payrolls": "Nonfarm Payrolls",
    "Average Hourly Earnings": "Average Hourly Earnings",
    "ADP Nonfarm Employment Change": "ADP Nonfarm Employment Change",
    "JOLTs Job Openings": "JOLTs Job Openings",
    "ISM Manufacturing PMI": "ISM Manufacturing PMI",
    "ISM Services PMI": "ISM Services PMI",
    "Core PCE Price Index": "Core PCE Price Index",
    "PCE Price Index": "PCE Price Index",
    "Core CPI": "Core Consumer Price Index (CPI)",
    "CPI": "Consumer Price Index (CPI)",
    "Core PPI": "Core Producer Price Index (PPI)",
    "PPI": "Producer Price Index (PPI)",
    "GDP Price Index": "GDP Price Index",
    "Core Retail Sales": "Core Retail Sales",
    "Retail Sales": "Retail Sales",
    "Building Permits": "Building Permits",
    "Housing Starts": "Housing Starts",
    "Existing Home Sales": "Existing Home Sales",
    "New Home Sales": "New Home Sales",
    "CB Consumer Confidence": "CB Consumer Confidence",
    "Michigan Consumer Sentiment": "Michigan Consumer Sentiment",
    "GDP": "Gross Domestic Product (GDP)",
    "Durable Goods Orders": "Durable Goods Orders",
    "Core Durable Goods Orders": "Core Durable Goods Orders",
    "Industrial Production": "Industrial Production",
    "Personal Income": "Personal Income"
}

@st.cache_data
def fetch_economic_data(indicator, country="united states", n_results=6):
    try:
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365*2)  # Go back 2 years to ensure we get enough data
        
        data = investpy.economic_calendar(
            countries=[country],
            from_date=start_date.strftime('%d/%m/%Y'),
            to_date=end_date.strftime('%d/%m/%Y')
        )
        
        # Filter for the specific indicator and high/medium importance
        data = data[(data['event'].str.contains(indicator, case=False)) & 
                    (data['importance'].isin(['high', 'medium']))]
        
        # Sort by date (most recent first) and get the last n_results
        data = data.sort_values('date', ascending=False).head(n_results)
        
        # Rename columns to match our format
        data = data.rename(columns={
            'actual': 'Actual',
            'forecast': 'Forecast',
            'previous': 'Previous',
            'event': 'Indicator'
        })
        
        return data[['date', 'time', 'Actual', 'Forecast', 'Previous', 'Indicator']]
    except Exception as e:
        logger.error(f"Error fetching data for {indicator}: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("US Economic Data Dashboard")
    
    st.sidebar.header("Select Economic Indicators")
    selected_indicators = st.sidebar.multiselect(
        "Choose indicators",
        list(indicators.keys())
    )
    
    if selected_indicators:
        all_data = []
        for indicator_name in selected_indicators:
            indicator_search = indicators[indicator_name]
            with st.spinner(f'Fetching data for {indicator_name}...'):
                df = fetch_economic_data(indicator_search)
                if not df.empty:
                    all_data.append(df)
                    st.subheader(f"{indicator_name} Data")
                    st.dataframe(df)
                    
                    if 'Actual' in df.columns:
                        df['Actual'] = pd.to_numeric(df['Actual'].replace(r'[^0-9.-]', '', regex=True), errors='coerce')
                        if df['Actual'].notna().any():
                            st.line_chart(df.set_index('date')['Actual'])
                        else:
                            st.write("Unable to create chart: 'Actual' column not numeric")
                else:
                    st.warning(f"No data available for {indicator_name}")
        
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