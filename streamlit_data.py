import streamlit as st
import pandas as pd
import yfinance as yf

def fetch_economic_data(indicator):
    """
    Fetch economic data using yfinance.
    You can expand this function to include more data sources or indicators.
    """
    if indicator == "GDP":
        data = yf.Ticker("GDP").history(period="max")
    elif indicator == "Inflation":
        data = yf.Ticker("CPI").history(period="max")
    elif indicator == "Unemployment":
        data = yf.Ticker("UNRATE").history(period="max")
    else:
        data = pd.DataFrame()
    
    return data

def main():
    st.title("US Economic Data Dashboard")
    
    # Sidebar for user input
    st.sidebar.header("Select Economic Indicators")
    indicators = st.sidebar.multiselect(
        "Choose indicators",
        ["GDP", "Inflation", "Unemployment"]
    )
    
    # Main content
    if indicators:
        for indicator in indicators:
            st.header(f"{indicator} Data")
            data = fetch_economic_data(indicator)
            st.dataframe(data)
            st.line_chart(data['Close'])
    else:
        st.write("Please select at least one indicator from the sidebar.")

if __name__ == "__main__":
    main()