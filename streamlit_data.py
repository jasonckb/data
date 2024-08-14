import streamlit as st
import pandas as pd
import investpy

def fetch_economic_data(indicator, country='united states'):
    """
    Fetch economic data using investpy.
    """
    try:
        # Fetch data for the last 5 years
        data = investpy.economic_calendar(
            countries=[country],
            importances=['high'],
            categories=[indicator],
            from_date=(pd.Timestamp.now() - pd.DateOffset(years=5)).strftime('%d/%m/%Y'),
            to_date=pd.Timestamp.now().strftime('%d/%m/%Y')
        )
        return data
    except Exception as e:
        st.error(f"Error fetching data for {indicator}: {str(e)}")
        return pd.DataFrame()

def main():
    st.title("US Economic Data Dashboard")
    
    # Sidebar for user input
    st.sidebar.header("Select Economic Indicators")
    indicators = st.sidebar.multiselect(
        "Choose indicators",
        ["GDP", "CPI", "Unemployment Rate"]
    )
    
    # Main content
    if indicators:
        for indicator in indicators:
            st.header(f"{indicator} Data")
            data = fetch_economic_data(indicator)
            if not data.empty:
                st.dataframe(data)
                
                # Create a line chart if 'Actual' column exists and is numeric
                if 'Actual' in data.columns and pd.api.types.is_numeric_dtype(data['Actual']):
                    chart_data = data.set_index('Date')['Actual'].sort_index()
                    st.line_chart(chart_data)
                else:
                    st.write("Unable to create chart: 'Actual' column not found or not numeric")
            else:
                st.write(f"No data available for {indicator}")
    else:
        st.write("Please select at least one indicator from the sidebar.")

if __name__ == "__main__":
    main()