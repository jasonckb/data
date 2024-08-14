import streamlit as st
import pandas as pd
import investpy
from datetime import datetime, timedelta

def fetch_economic_data(indicator, country='united states', num_events=12):
    """
    Fetch economic data using investpy, limited to the last 12 events with medium or high importance.
    """
    try:
        # Calculate date range for the past year
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        
        data = investpy.economic_calendar(
            countries=[country],
            importances=['medium', 'high'],
            categories=[indicator],
            from_date=start_date.strftime('%d/%m/%Y'),
            to_date=end_date.strftime('%d/%m/%Y')
        )
        
        # Filter to keep only the specified indicator and sort by date
        data = data[data['event'] == indicator].sort_values('date', ascending=False)
        
        # Limit to the last num_events (12 by default)
        return data.head(num_events)
    except Exception as e:
        st.error(f"Error fetching data for {indicator}: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("US Economic Data Dashboard")
    
    # Sidebar for user input
    st.sidebar.header("Select Economic Indicators")
    indicators = st.sidebar.multiselect(
        "Choose indicators",
        ["GDP", "CPI", "Unemployment Rate", "Initial Jobless Claims", "Non-Farm Payrolls"]
    )
    
    # Main content
    if indicators:
        for indicator in indicators:
            st.header(f"{indicator} Data")
            data = fetch_economic_data(indicator)
            if not data.empty:
                st.dataframe(data)
                
                # Create a line chart if 'actual' column exists and is numeric
                if 'actual' in data.columns and pd.to_numeric(data['actual'], errors='coerce').notnull().all():
                    chart_data = data.set_index('date')['actual'].sort_index()
                    st.line_chart(chart_data)
                else:
                    st.write("Unable to create chart: 'actual' column not found or not numeric")
            else:
                st.write(f"No data available for {indicator}")
    else:
        st.write("Please select at least one indicator from the sidebar.")

if __name__ == "__main__":
    main()