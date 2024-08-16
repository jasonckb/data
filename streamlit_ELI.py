import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
import plotly.io as pio
import os
from yahoofinancials import YahooFinancials  # Add this line

# Set page to wide mode
st.set_page_config(layout="wide")

def get_stock_data(ticker, period="1y"):
    stock = yf.Ticker(ticker)
    data = stock.history(period=period)
    data = data.dropna()
    return data

def format_ticker(ticker):
    if ticker.isdigit():
        return f"{int(ticker):04d}.HK"
    return ticker

def calculate_price_levels(current_price, strike_pct, airbag_pct, knockout_pct):
    strike_price = current_price * (strike_pct / 100) if strike_pct != 0 else 0
    airbag_price = current_price * (airbag_pct / 100) if airbag_pct != 0 else 0
    knockout_price = current_price * (knockout_pct / 100) if knockout_pct != 0 else 0
    return strike_price, airbag_price, knockout_price

def calculate_ema(data, period):
    return data['Close'].ewm(span=period, adjust=False).mean()

def calculate_volume_profile(data, bins=40):
    price_range = data['Close'].max() - data['Close'].min()
    bin_size = price_range / bins
    price_bins = pd.cut(data['Close'], bins=bins)
    volume_profile = data.groupby(price_bins)['Volume'].sum()
    bin_centers = [(i.left + i.right) / 2 for i in volume_profile.index]
    
    # Calculate POC
    poc_price = bin_centers[volume_profile.argmax()]
    
    # Calculate Value Area (70% of volume)
    total_volume = volume_profile.sum()
    target_volume = total_volume * 0.7
    cumulative_volume = 0
    value_area_low = value_area_high = poc_price
    
    for price, volume in zip(bin_centers, volume_profile):
        cumulative_volume += volume
        if cumulative_volume <= target_volume / 2:
            value_area_low = price
        if cumulative_volume >= total_volume - target_volume / 2:
            value_area_high = price
            break
    
    return volume_profile, bin_centers, bin_size, poc_price, value_area_low, value_area_high

def plot_stock_chart(data, ticker, strike_price, airbag_price, knockout_price):
    fig = go.Figure()

    # Candlestick chart with custom colors
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price',
        increasing_line_color='dodgerblue',  # Bullish bars in Dodge Blue
        decreasing_line_color='red'  # Bearish bars in red
    ))

    # Calculate EMAs
    ema_20 = calculate_ema(data, 20)
    ema_50 = calculate_ema(data, 50)
    ema_200 = calculate_ema(data, 200)

    # Calculate the position for price annotations
    first_date = data.index[0]
    last_date = data.index[-1]
    annotation_x = last_date + pd.Timedelta(days=2)  # 2 days after the last candle
    mid_date = first_date + (last_date - first_date) / 2  # Middle of the date range

    # Add price level lines with annotations on the right (only if not zero)
    if strike_price != 0:
        fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=strike_price, y1=strike_price,
                      line=dict(color="blue", width=2, dash="dash"))
        fig.add_annotation(x=annotation_x, y=strike_price, text=f"Strike Price: {strike_price:.2f}",
                           showarrow=False, xanchor="left", font=dict(size=14, color="blue"))

    if airbag_price != 0:
        fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=airbag_price, y1=airbag_price,
                      line=dict(color="green", width=2, dash="dash"))
        fig.add_annotation(x=annotation_x, y=airbag_price, text=f"Airbag Price: {airbag_price:.2f}",
                           showarrow=False, xanchor="left", font=dict(size=14, color="green"))

    if knockout_price != 0:
        fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=knockout_price, y1=knockout_price,
                      line=dict(color="orange", width=2, dash="dash"))
        fig.add_annotation(x=annotation_x, y=knockout_price, text=f"Knock-out Price: {knockout_price:.2f}",
                           showarrow=False, xanchor="left", font=dict(size=14, color="orange"))

    # Add EMA lines
    fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=ema_20.iloc[-1], y1=ema_20.iloc[-1],
                  line=dict(color="gray", width=1, dash="dash"))
    fig.add_annotation(x=annotation_x, y=ema_20.iloc[-1], text=f"20 EMA: {ema_20.iloc[-1]:.2f}",
                       showarrow=False, xanchor="left", font=dict(size=12, color="gray"))

    fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=ema_50.iloc[-1], y1=ema_50.iloc[-1],
                  line=dict(color="gray", width=2, dash="dash"))
    fig.add_annotation(x=annotation_x, y=ema_50.iloc[-1], text=f"50 EMA: {ema_50.iloc[-1]:.2f}",
                       showarrow=False, xanchor="left", font=dict(size=12, color="gray"))

    fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=ema_200.iloc[-1], y1=ema_200.iloc[-1],
                  line=dict(color="gray", width=3, dash="dash"))
    fig.add_annotation(x=annotation_x, y=ema_200.iloc[-1], text=f"200 EMA: {ema_200.iloc[-1]:.2f}",
                       showarrow=False, xanchor="left", font=dict(size=12, color="gray"))

    # Add current price annotation
    current_price = data['Close'].iloc[-1]
    fig.add_annotation(x=annotation_x, y=current_price, text=f"Current Price: {current_price:.2f}",
                       showarrow=False, xanchor="left", font=dict(size=14, color="black"))

    # Calculate and add volume profile
    volume_profile, bin_centers, bin_size, poc_price, value_area_low, value_area_high = calculate_volume_profile(data)
    max_volume = volume_profile.max()
    fig.add_trace(go.Bar(
        x=volume_profile.values,
        y=bin_centers,
        orientation='h',
        name='Volume Profile',
        marker_color='rgba(200, 200, 200, 0.5)',
        width=bin_size,
        xaxis='x2'
    ))

    # Add POC line (red)
    fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=poc_price, y1=poc_price,
                  line=dict(color="red", width=4))
    fig.add_annotation(x=annotation_x, y=poc_price, text=f"POC: {poc_price:.2f}",
                       showarrow=False, xanchor="left", font=dict(size=12, color="red"))

    # Add Value Area lines (purple) with labels above and below the lines
    fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=value_area_low, y1=value_area_low,
                  line=dict(color="purple", width=2))
    fig.add_annotation(x=mid_date, y=value_area_low, text=f"Value at Low: {value_area_low:.2f}",
                       showarrow=False, xanchor="center", yanchor="top", font=dict(size=12, color="purple"),
                       yshift=-5)  # Shift the label 5 pixels below the line

    fig.add_shape(type="line", x0=first_date, x1=annotation_x, y0=value_area_high, y1=value_area_high,
                  line=dict(color="purple", width=2))
    fig.add_annotation(x=mid_date, y=value_area_high, text=f"Value at High: {value_area_high:.2f}",
                       showarrow=False, xanchor="center", yanchor="bottom", font=dict(size=12, color="purple"),
                       yshift=5)  # Shift the label 5 pixels above the line

    fig.update_layout(
        title=f"{ticker} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price",
        xaxis_rangeslider_visible=False,
        height=600,
        width=800,
        margin=dict(l=50, r=150, t=50, b=50),
        showlegend=False,
        font=dict(size=14),
        xaxis2=dict(
            side='top',
            overlaying='x',
            range=[0, max_volume],
            showgrid=False,
            showticklabels=False,
        ),
    )

    # Set x-axis to show only trading days and extend range for annotations
    fig.update_xaxes(
        rangebreaks=[
            dict(bounds=["sat", "mon"]),  # Hide weekends
            dict(values=["2023-12-25", "2024-01-01"])  # Example: hide specific holidays
        ],
        range=[first_date, annotation_x]  # Extend x-axis range for annotations
    )

    return fig

def get_financial_metrics(ticker):
    stock = yf.Ticker(ticker)
    info = stock.info
    
    metrics = {
        "Market Cap": info.get("marketCap", "N/A"),       
        "Historical P/E": info.get("trailingPE", "N/A"),
        "Forward P/E": info.get("forwardPE", "N/A"),
        "PEG Ratio (5yr expected)": info.get("pegRatio", "N/A"),
        "Historical Dividend(%)": info.get("trailingAnnualDividendYield", "N/A")*100,
        "Price/Book": info.get("priceToBook", "N/A"),
        "Net Income": info.get("netIncomeToCommon", "N/A"),
        "Revenue": info.get("totalRevenue", "N/A"),  # Changed from "revenue" to "totalRevenue"
        "Profit Margin": info.get("profitMargins", "N/A"),  # Changed from "profitMargin" to "profitMargins"
        "ROE": info.get("returnOnEquity", "N/A"),
    }
    
    # Format large numbers
    for key in ["Market Cap", "Net Income", "Revenue"]:
        if isinstance(metrics[key], (int, float)):
            if abs(metrics[key]) >= 1e12:
                metrics[key] = f"{metrics[key]/1e12:.2f}T"
            elif abs(metrics[key]) >= 1e9:
                metrics[key] = f"{metrics[key]/1e9:.2f}B"
            elif abs(metrics[key]) >= 1e6:
                metrics[key] = f"{metrics[key]/1e6:.2f}M"
    
    # Format percentages
    for key in ["Profit Margin", "ROE"]:
        if isinstance(metrics[key], float):
            metrics[key] = f"{metrics[key]:.2%}"
    
    # Round floating point numbers
    for key, value in metrics.items():
        if isinstance(value, float):
            metrics[key] = round(value, 2)
    
    return metrics

def get_yahoo_finance_news(ticker):
    url = f"https://finance.yahoo.com/quote/{ticker}/news/"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        news_items = soup.find_all('li', class_='js-stream-content Pos(r)')
        
        news = []
        for item in news_items[:5]:  # Get top 5 news items
            title_element = item.find('h3')
            link_element = item.find('a', href=True)
            
            if title_element and link_element:
                title = title_element.text.strip()
                link = link_element['href']
                # Ensure the link is absolute
                if link.startswith('/'):
                    link = f"https://finance.yahoo.com{link}"
                news.append((title, link))
        
        return news
    except Exception as e:
        st.error(f"Error fetching news: {str(e)}")
        return []
    
def get_analyst_ratings(ticker):
    yahoo_financials = YahooFinancials(ticker)
    analyst_data = yahoo_financials.get_stock_earnings_data()
    
    if analyst_data and ticker in analyst_data:
        earnings_data = analyst_data[ticker]
        if 'quarterly_earnings_data' in earnings_data:
            quarterly_data = earnings_data['quarterly_earnings_data']
            if quarterly_data:
                latest_quarter = list(quarterly_data.keys())[0]
                return quarterly_data[latest_quarter]
    
    return None

def get_analyst_recommendations(ticker):
    stock = yf.Ticker(ticker)
    recommendations = stock.recommendations
    if recommendations is not None and not recommendations.empty:
        recent_recommendations = recommendations.tail(10)  # Get last 10 recommendations
        upgrades = recent_recommendations[recent_recommendations['To Grade'] > recent_recommendations['From Grade']]
        downgrades = recent_recommendations[recent_recommendations['To Grade'] < recent_recommendations['From Grade']]
        
        latest_recommendations = recommendations.iloc[-1]
        buy_count = latest_recommendations.get('Buy', 0)
        hold_count = latest_recommendations.get('Hold', 0)
        sell_count = latest_recommendations.get('Sell', 0)
        
        return {
            'upgrades': upgrades,
            'downgrades': downgrades,
            'summary': {
                'Buy': buy_count,
                'Hold': hold_count,
                'Sell': sell_count
            }
        }
    return None  

def main():
    st.title("Stock Fundamentals with Key Levels by JC")

    # Create two columns for layout
    col1, col2 = st.columns([1, 4])

    # Sidebar inputs (now in the first column)
    with col1:
        ticker = st.text_input("Enter Stock Ticker:", value="AAPL")
        strike_pct = st.number_input("Strike Price %:", value=0.0)
        airbag_pct = st.number_input("Airbag Price %:", value=0.0)
        knockout_pct = st.number_input("Knock-out Price %:", value=0.0)
        
        # Add a refresh button
        refresh = st.button("Refresh Data")

        # Display current price and calculated levels with larger text in the sidebar
        st.markdown("<h3>Price Levels:</h3>", unsafe_allow_html=True)

    # Format ticker and fetch data when input changes or refresh is clicked
    if 'formatted_ticker' not in st.session_state or ticker != st.session_state.formatted_ticker or refresh:
        st.session_state.formatted_ticker = format_ticker(ticker)
        try:
            st.session_state.data = get_stock_data(st.session_state.formatted_ticker)
            st.success(f"Data fetched successfully for {st.session_state.formatted_ticker}")
        except Exception as e:
            st.error(f"Error fetching data: {str(e)}")

    # Main logic
    if hasattr(st.session_state, 'data') and not st.session_state.data.empty:
        try:
            current_price = st.session_state.data['Close'].iloc[-1]
            strike_price, airbag_price, knockout_price = calculate_price_levels(current_price, strike_pct, airbag_pct, knockout_pct)

            # Display current price and calculated levels in the sidebar
            with col1:
                st.markdown(f"<h4>Current Price: {current_price:.2f}</h4>", unsafe_allow_html=True)
                st.markdown(f"<p>Strike Price ({strike_pct}%): {strike_price:.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"<p>Airbag Price ({airbag_pct}%): {airbag_price:.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"<p>Knock-out Price ({knockout_pct}%): {knockout_price:.2f}</p>", unsafe_allow_html=True)

            # Main chart and data display
            with col2:
                # Add financial metrics above the chart
                st.markdown("<h3>Financial Metrics & Data from Yahoo Finance:</h3>", unsafe_allow_html=True)
                try:
                    metrics = get_financial_metrics(st.session_state.formatted_ticker)
                    cols = st.columns(2)  # Create 2 columns for metrics display
                    for i, (key, value) in enumerate(metrics.items()):
                        cols[i % 2].markdown(f"<b>{key}:</b> {value}", unsafe_allow_html=True)
                except Exception as e:
                    st.error(f"Error fetching financial metrics: {str(e)}")

                # Add analyst ratings
                st.markdown("<h3>Analyst Ratings:</h3>", unsafe_allow_html=True)
                try:
                    recommendations = get_analyst_recommendations(st.session_state.formatted_ticker)
                    if recommendations:
                        # Summary box
                        st.subheader("Recommendation Summary")
                        summary = recommendations['summary']
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Buy", summary.get('Buy', 'N/A'))
                        col2.metric("Hold", summary.get('Hold', 'N/A'))
                        col3.metric("Sell", summary.get('Sell', 'N/A'))

                        # Recent changes
                        st.subheader("Recent Changes in Analyst Ratings")
                        changes = recommendations['changes']
                        if not changes.empty:
                            st.dataframe(changes)
                        else:
                            st.write("No recent changes in analyst ratings.")
                    else:
                        st.write("No analyst recommendations available.")
                except Exception as e:
                    st.error(f"Error fetching analyst ratings: {str(e)}")

                # Add some space between metrics and chart
                st.markdown("<br>", unsafe_allow_html=True)

                # Plot the chart
                st.markdown("<h3>Stock Chart:</h3>", unsafe_allow_html=True)
                fig = plot_stock_chart(st.session_state.data, st.session_state.formatted_ticker, strike_price, airbag_price, knockout_price)
                st.plotly_chart(fig, use_container_width=True)

                # Display EMA values
                st.markdown("<h3>Exponential Moving Averages:</h3>", unsafe_allow_html=True)
                ema_20 = calculate_ema(st.session_state.data, 20).iloc[-1]
                ema_50 = calculate_ema(st.session_state.data, 50).iloc[-1]
                ema_200 = calculate_ema(st.session_state.data, 200).iloc[-1]
                st.markdown(f"<p>20 EMA: {ema_20:.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"<p>50 EMA: {ema_50:.2f}</p>", unsafe_allow_html=True)
                st.markdown(f"<p>200 EMA: {ema_200:.2f}</p>", unsafe_allow_html=True)

                # Display news
                st.markdown("<h3>Latest News:</h3>", unsafe_allow_html=True)
                st.info(f"You can try visiting this URL directly for news: https://finance.yahoo.com/quote/{st.session_state.formatted_ticker}/news/")

                # Add screenshot button
                if st.button("Take Screenshot"):
                    try:
                        # Save the figure as a temporary file
                        temp_file = f"{st.session_state.formatted_ticker}_chart.png"
                        pio.write_image(fig, temp_file)
                        
                        # Read the file and create a download button
                        with open(temp_file, "rb") as file:
                            btn = st.download_button(
                                label="Download Chart Screenshot",
                                data=file,
                                file_name=f"{st.session_state.formatted_ticker}_chart.png",
                                mime="image/png"
                            )
                        
                        # Remove the temporary file
                        os.remove(temp_file)
                        
                    except Exception as e:
                        st.error(f"Error generating screenshot: {str(e)}")
                        st.error("If the error persists, please try updating plotly and kaleido: pip install -U plotly kaleido")

        except Exception as e:
            st.error(f"Error processing data: {str(e)}")
            st.write("Debug information:")
            st.write(f"Data shape: {st.session_state.data.shape}")
            st.write(f"Data columns: {st.session_state.data.columns}")
            st.write(f"Data head:\n{st.session_state.data.head()}")
    else:
        st.warning("No data available. Please check the ticker symbol and try again.")

if __name__ == "__main__":
    main()