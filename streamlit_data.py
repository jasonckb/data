import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta 
import re
import logging
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="US and China Economic Data Analysis (Jason Chan)", layout="wide")

def get_urls(country):
    if country == "US":
        return [
            "https://www.investing.com/economic-calendar/unemployment-rate-300",
            "https://www.investing.com/economic-calendar/nonfarm-payrolls-227",
            "https://www.investing.com/economic-calendar/average-hourly-earnings-8",
            "https://www.investing.com/economic-calendar/average-hourly-earnings-1777",        
            "https://www.investing.com/economic-calendar/adp-nonfarm-employment-change-1",
            "https://www.investing.com/economic-calendar/core-pce-price-index-905",
            "https://www.investing.com/economic-calendar/core-pce-price-index-61",
            "https://www.investing.com/economic-calendar/cpi-733",
            "https://www.investing.com/economic-calendar/cpi-69",
            "https://www.investing.com/economic-calendar/core-cpi-736", 
            "https://www.investing.com/economic-calendar/core-cpi-56",        
            "https://www.investing.com/economic-calendar/core-ppi-62",
            "https://www.investing.com/economic-calendar/ppi-238",
            "https://www.investing.com/economic-calendar/ism-manufacturing-pmi-173",
            "https://www.investing.com/economic-calendar/ism-non-manufacturing-pmi-176", 
            "https://www.investing.com/economic-calendar/industrial-production-1755",
            "https://www.investing.com/economic-calendar/industrial-production-161",
            "https://www.investing.com/economic-calendar/core-retail-sales-63",
            "https://www.investing.com/economic-calendar/retail-sales-256",
            "https://www.investing.com/economic-calendar/housing-starts-151",
            "https://www.investing.com/economic-calendar/existing-home-sales-99",
            "https://www.investing.com/economic-calendar/new-home-sales-222",
            "https://www.investing.com/economic-calendar/cb-consumer-confidence-48",
            "https://www.investing.com/economic-calendar/gdp-375",
            "https://www.investing.com/economic-calendar/durable-goods-orders-86",
            "https://www.investing.com/economic-calendar/core-durable-goods-orders-59",
        ]
    elif country == "China":
        return [
            "https://www.investing.com/economic-calendar/chinese-exports-595",
            "https://www.investing.com/economic-calendar/chinese-imports-867",
            "https://www.investing.com/economic-calendar/chinese-trade-balance-466",
            "https://www.investing.com/economic-calendar/chinese-fixed-asset-investment-460",
            "https://www.investing.com/economic-calendar/chinese-industrial-production-462",
            "https://www.investing.com/economic-calendar/chinese-unemployment-rate-1793",
            "https://www.investing.com/economic-calendar/chinese-cpi-743",
            "https://www.investing.com/economic-calendar/chinese-cpi-459",
            "https://www.investing.com/economic-calendar/chinese-ppi-464",
            "https://www.investing.com/economic-calendar/chinese-new-loans-1060",
            "https://www.investing.com/economic-calendar/chinese-outstanding-loan-growth-1081",
            "https://www.investing.com/economic-calendar/chinese-total-social-financing-1919",
            "https://www.investing.com/economic-calendar/china-loan-prime-rate-5y-2225",
            "https://www.investing.com/economic-calendar/pboc-loan-prime-rate-1967",
            "https://www.investing.com/economic-calendar/chinese-caixin-services-pmi-596",
            "https://www.investing.com/economic-calendar/chinese-composite-pmi-1913",
            "https://www.investing.com/economic-calendar/chinese-manufacturing-pmi-594",
            "https://www.investing.com/economic-calendar/chinese-non-manufacturing-pmi-831",
        ]

def get_indicators(country):
    if country == "US":
        return {
            "United States Unemployment Rate": [],
            "United States Nonfarm Payrolls": [],
            "United States Average Hourly Earnings MoM": [],
            "United States Average Hourly Earnings YoY": [],
            "United States ADP Nonfarm Employment Change": [],
            "United States Core PCE Price Index YoY": [],
            "United States Core PCE Price Index MoM": [],
            "United States Consumer Price Index (CPI) YoY": [],
            "United States Consumer Price Index (CPI) MoM": [],
            "United States Core Consumer Price Index (CPI) YoY": [],
            "United States Core Consumer Price Index (CPI) MoM": [],
            "United States Core Producer Price Index (PPI) MoM": [],
            "United States Producer Price Index (PPI) MoM": [],
            "United States ISM Manufacturing PMI": [],
            "United States ISM Non-Manufacturing PMI": [],
            "United States Industrial Production YoY": [],
            "United States Industrial Production MoM": [],
            "United States Core Retail Sales MoM": [],
            "United States Retail Sales MoM": [],
            "United States Housing Starts": [],
            "United States Existing Home Sales": [],
            "United States New Home Sales": [],
            "United States CB Consumer Confidence": [],
            "United States Gross Domestic Product (GDP) QoQ": [],
            "United States Durable Goods Orders MoM": [],
            "United States Core Durable Goods Orders MoM": []
        }
    elif country == "China":
        return {
            "China Exports YoY": [],
            "China Imports YoY": [],
            "China Trade Balance (USD)": [],
            "China Fixed Asset Investment YoY": [],
            "China Industrial Production YoY": [],
            "Chinese Unemployment Rate": [],
            "China Consumer Price Index (CPI) MoM": [],
            "China Consumer Price Index (CPI) YoY": [],
            "China Producer Price Index (PPI) YoY": [],
            "China New Loans": [],
            "China Outstanding Loan Growth YoY": [],
            "China Total Social Financing": [],
            "China Loan Prime Rate 5Y": [],
            "People's Bank of China Loan Prime Rate": [],
            "China Caixin Services Purchasing Managers Index (PMI)": [],
            "China Composite Purchasing Managers' Index (PMI)": [],
            "China Manufacturing Purchasing Managers Index (PMI)": [],
            "China Non-Manufacturing Purchasing Managers Index (PMI)": []
        }

def get_lower_is_better(country):
    if country == "US":
        return [
            "United States Unemployment Rate",
            "United States Core PCE Price Index YoY",
            "United States Core PCE Price Index MoM",
            "United States Core Consumer Price Index (CPI) YoY",
            "United States Core Consumer Price Index (CPI) MoM",
            "United States Consumer Price Index (CPI) YoY",
            "United States Consumer Price Index (CPI) MoM",
            "United States Core Producer Price Index (PPI) MoM",
            "United States Producer Price Index (PPI) MoM"
        ]
    elif country == "China":
        return [
            "Chinese Unemployment Rate",            
            "China Loan Prime Rate 5Y",
            "People's Bank of China Loan Prime Rate"
        ]


def safe_strip(value):
    """Safely strip the value"""
    return value.strip() if isinstance(value, str) else value

def is_future_month(date_str):
    actual_date, reported_month = parse_date(date_str)
    if actual_date:
        current_date = datetime.now()
        # Use the actual date for filtering, not the reported month
        return actual_date > current_date
    return False

def scrape_data(urls):
    data = []
    current_date = datetime.now()

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
                    date_str = safe_strip(cols[0].text)
                    actual_date, reported_month = parse_date(date_str)
                    if actual_date and actual_date <= current_date:
                        cols_text = [safe_strip(col.text) for col in cols]
                        if cols_text[3] == '':
                            cols_text[3] = None
                        data.append([title] + cols_text)
                        row_counter += 1
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
    
    return pd.DataFrame(data, columns=['Title', 'Date', 'Time', 'Actual', 'Forecast', 'Previous', 'Importance'])

def parse_date(date_str):
    patterns = [
        r'(\w+ \d{2}, \d{4}) \((\w+)\)',
        r'(\w+ \d{2}, \d{4})',
        r'(\w+ \d{2}, \d{4}) \(Q\d\)'
    ]
    for pattern in patterns:
        match = re.match(pattern, date_str)
        if match:
            actual_date = datetime.strptime(match.group(1), '%b %d, %Y')
            reported_month = match.group(2) if len(match.groups()) > 1 else None
            return actual_date, reported_month
    return None, None

def compare_values(actual, forecast, indicator, lower_is_better):
    if actual is None or forecast is None or actual == '' or forecast == '':
        return ''
    
    def parse_value(value):
        if isinstance(value, str):
            value = value.strip().rstrip('%')
            if value.endswith('B'):
                return float(value[:-1]) * 1e9
            elif value.endswith('M'):
                return float(value[:-1]) * 1e6
            elif value.endswith('K'):
                return float(value[:-1]) * 1e3
            else:
                return float(value)
        return value

    try:
        actual_value = parse_value(actual)
        forecast_value = parse_value(forecast)
    except ValueError:
        return ''

    if indicator in lower_is_better:
        return "Better" if actual_value < forecast_value else "Worse" if actual_value > forecast_value else "Same"
    else:
        return "Better" if actual_value > forecast_value else "Worse" if actual_value < forecast_value else "Same"

def process_data(df, country):
    indicators = get_indicators(country)
    lower_is_better = get_lower_is_better(country)

    for _, row in df.iterrows():
        indicator = row['Title'].split(' - ')[0]
        if indicator in indicators:
            date, month_in_parentheses = parse_date(row['Date'])
            if date is None:
                logging.warning(f"Unable to parse date: {row['Date']} for indicator: {indicator}")
                continue

            forecast = safe_strip(row.get('Forecast', ''))
            actual = safe_strip(row.get('Actual', ''))
            
            vs_forecast = compare_values(actual, forecast, indicator, lower_is_better)
            
            indicators[indicator].append({
                "Date": date,
                "MonthInParentheses": month_in_parentheses,
                "Vs Forecast": vs_forecast,
                "Forecast": forecast if forecast and forecast != '-' else None,
                "Actual": actual if actual and actual != '-' else None
            })

    processed_data = []
    for indicator, data in indicators.items():
        if data:
            sorted_data = sorted(data, key=lambda x: x['Date'], reverse=True)
            latest = sorted_data[0]
            row = [
                indicator,
                latest['Date'].strftime("%b %d, %Y") + f" ({latest['MonthInParentheses']})",
                latest['Vs Forecast'] if latest['Actual'] is not None else '',
                latest['Forecast'] if latest['Forecast'] else 'None'
            ]
            actuals = []
            for i in range(5):
                if i < len(sorted_data):
                    actuals.append(sorted_data[i].get('Actual') or 'None')
                else:
                    actuals.append('None')
            row.extend(actuals)
            processed_data.append(row)
        else:
            logging.warning(f"No data for indicator: {indicator}")

    return processed_data, indicators


def create_chart(data, indicator):
    dates = [d['Date'] for d in data]
    actuals = [float(safe_strip(d['Actual']).rstrip('K%M')) if d['Actual'] and d['Actual'] not in ['', 'None'] else None for d in data]
    forecasts = [float(safe_strip(d['Forecast']).rstrip('K%M')) if d['Forecast'] and d['Forecast'] not in ['', 'None'] else None for d in data]
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])

    fig.add_trace(
        go.Scatter(x=dates, y=actuals, name="Actual", mode="lines+markers"),
        secondary_y=False,
    )

    # Only get the latest forecast value
    latest_forecast = next((f for f in forecasts if f is not None), None)
    latest_date = dates[0]

    if latest_forecast is not None:
        # Only draw the forecast line from the latest date
        forecast_dates = [d for d in dates if d <= latest_date]
        forecast_values = [latest_forecast] * len(forecast_dates)
        
        fig.add_trace(
            go.Scatter(x=forecast_dates, y=forecast_values, name="Forecast (Current/Previous Month)", 
                       mode="lines", line=dict(dash="dash", color="gray")),
            secondary_y=False,
        )
        logging.info(f"Drawing forecast line, value: {latest_forecast}")
    else:
        logging.info("No valid forecast value, not drawing forecast line")

    fig.update_layout(
        title=indicator,
        xaxis_title="Date",
        yaxis_title="Value",
        legend_title="Legend",
        height=400,
        width=600
    )

    return fig

def main():
    st.title("US and China Economic Data Analysis (Jason Chan)")

    # Add dropdown menu to sidebar
    country = st.sidebar.selectbox
