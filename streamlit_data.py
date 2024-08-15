import streamlit as st
import investpy
import pandas as pd
from datetime import datetime, timedelta
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the list of economic indicators we want to fetch
indicators = [
    "Unemployment Rate", "Non-Farm Payrolls", "Average Hourly Earnings",
    "ADP Nonfarm Employment Change", "JOLTs Job Openings",
    "ISM Manufacturing PMI", "ISM Services PMI",
    "Core PCE Price Index", "PCE Price Index",
    "Core CPI", "CPI", "Core PPI", "PPI",
    "GDP Price Index", "Core Retail Sales", "Retail Sales",
    "Building Permits", "Housing Starts", "Existing Home Sales", "New Home Sales",
    "CB Consumer Confidence", "Michigan Consumer Sentiment",
    "GDP", "Durable Goods Orders", "Core Durable Goods Orders",
    "Industrial Production", "Personal Income"
]

@st.cache_data
def fetch_economic_data(indicator, country="United States", n_results=6):
    try:
        from_date = (datetime.now() - timedelta(days=365)).strftime('%d/%m/%Y')
        to_date = datetime.now().strftime('%d/%m/%Y')
        
        data = investpy.economic_calendar(
            countries=[country],
            from_date=from_date,
            to_date=to_date,
            categories=[indicator]
        )
        
        # Filter for high and medium importance events
        data = data[data['importance'].isin(['high', 'medium'])]
        
        # Sort by date (most recent first) and get the last n_results
        data = data.sort_values('date', ascending=False).head(n_results)
        
        # Rename columns to match our previous format
        data = data.rename(columns={
            'actual': 'Actual',
            'forecast': 'Forecast',
            'previous': 'Previous'
        })
        
        # Add the Indicator column
        data['Indicator'] = indicator
        
        return data[['date', 'time', 'Actual', 'Forecast', 'Previous', 'Indicator']]
    except Exception as e:
        logger.error(f"Error fetching data for {indicator}: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("US Economic Data Dashboard")
    
    st.sidebar.header("Select Economic Indicators")
    selected_indicators = st.sidebar.multiselect(
        "Choose indicators",
        indicators
    )
    
    if selected_indicators:
        all_data = []
        for indicator in selected_indicators:
            with st.spinner(f'Fetching data for {indicator}...'):
                df = fetch_economic_data(indicator)
                if not df.empty:
                    all_data.append(df)
                    st.subheader(f"{indicator} Data")
                    st.dataframe(df)
                    
                    if 'Actual' in df.columns:
                        df['Actual'] = pd.to_numeric(df['Actual'], errors='coerce')
                        if df['Actual'].notna().any():
                            st.line_chart(df.set_index('date')['Actual'])
                        else:
                            st.write("Unable to create chart: 'Actual' column not numeric")
                else:
                    st.warning(f"No data available for {indicator}")
        
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