import os
import json
import requests
import boto3
import numpy as np
import plotly.graph_objs as go
import streamlit as st
from datetime import datetime
import time
import threading
import logging
import pandas as pd
from prophet import Prophet
from langchain.tools import tool
import pandas as pd
import requests
import matplotlib.pyplot as plt
# Configure logging to suppress specific warnings
logging.basicConfig(level=logging.INFO)
logging.getLogger('Thread').setLevel(logging.ERROR)

# Global API key
API_KEY = "113c5d6f3c5b5365e1ae5e63039150abe56f0ec4cde2002798000cdcc0d67c23"

# Amazon Bedrock configuration
client = boto3.client('bedrock-runtime')
model_id = "amazon.titan-embed-text-v1"
accept = "application/json"
content_type = "application/json"
expected_dimension = 1536
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Define embed_text function using Amazon Titan
def embed_text(text):
    body = json.dumps({"inputText": text})
    response = client.invoke_model(
        body=body,
        modelId=model_id,
        accept=accept,
        contentType=content_type
    )
    response_body = json.loads(response.get('body').read())
    embedding = np.array(response_body['embedding'])
    if embedding.shape[0] != expected_dimension:
        print(f"Invalid embedding dimension: {embedding.shape[0]} for text: {text}")
        return None
    return embedding

# Define tools
@tool
def fetch_current_price(crypto_symbol: str) -> str:
    """Fetch the current price of a cryptocurrency."""
    url = f"https://min-api.cryptocompare.com/data/price?fsym={crypto_symbol}&tsyms=USD"
    response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
    data = response.json()
    return f"The current price of {crypto_symbol} is ${data['USD']}."

@tool
def convert_price(from_symbol: str, to_symbol: str) -> str:
    """Convert the price of one cryptocurrency to another."""
    url = f"https://min-api.cryptocompare.com/data/price?fsym={from_symbol}&tsyms={to_symbol}"
    response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
    data = response.json()
    return f"The price of 1 {from_symbol} in {to_symbol} is {data[to_symbol]} {to_symbol}."

@tool
def fetch_historical_prices(crypto_symbol: str) -> dict:
    """Fetch historical prices of a cryptocurrency for each month since its inception."""
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={crypto_symbol}&tsym=USD&limit=2000&aggregate=30"
    response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
    data = response.json()
    prices = {day['time']: day['close'] for day in data['Data']['Data']}
    return prices

@tool
def fetch_graphical_historical_prices(crypto_symbol: str) -> dict:
    """Fetch historical prices of a cryptocurrency for each month since its inception and display a graph."""
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={crypto_symbol}&tsym=USD&limit=2000&aggregate=30"
    response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
    data = response.json()
    prices = {day['time']: day['close'] for day in data['Data']['Data']}
    
    # Convert timestamps to readable dates
    dates = [datetime.fromtimestamp(ts) for ts in prices.keys()]
    values = list(prices.values())
    
    # Plot the data
    plt.figure(figsize=(10, 5))
    plt.plot(dates, values, label=f'{crypto_symbol} Price')
    plt.xlabel('Date')
    plt.ylabel('Price (USD)')
    plt.title(f'Historical Prices of {crypto_symbol}')
    plt.legend()
    plt.grid(True)
    
    # Display the plot using Streamlit
    st.pyplot(plt)
    
    return prices

# Global stop event for live graph
stop_event = threading.Event()

@tool
def load_live_graph(crypto_symbol: str):
    """Load an interactive live graph of the cryptocurrency using Plotly."""
    st.subheader(f"Live {crypto_symbol} Price Movement")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[], y=[], mode='lines', name='Price'))

    plotly_chart = st.plotly_chart(fig, use_container_width=True)

    xdata, ydata = [], []

    while not stop_event.is_set():
        url = f"https://min-api.cryptocompare.com/data/price?fsym={crypto_symbol}&tsyms=USD"
        response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
        data = response.json()
        current_time = datetime.now().strftime('%H:%M:%S')
        current_price = data['USD']

        xdata.append(current_time)
        ydata.append(current_price)

        fig.update_traces(x=xdata, y=ydata)
        plotly_chart.plotly_chart(fig)

        time.sleep(5)  # Update every 5 seconds

@tool
def close_live_graph() -> str:
    """Close the live graph."""
    stop_event.set()
    return "Live graph closed."

@tool
def predict_future_prices(crypto_symbol: str) -> str:
    """Predict future price movement based on historical prices and display it as a graph."""
    try:
        # Fetch historical prices directly from the API
        url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={crypto_symbol}&tsym=USD&limit=2000&aggregate=30"
        response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
        data = response.json()
        historical_prices = {day['time']: day['close'] for day in data['Data']['Data']}
        
        # Fetch current price
        current_price_url = f"https://min-api.cryptocompare.com/data/price?fsym={crypto_symbol}&tsyms=USD"
        current_price_response = requests.get(current_price_url, headers={"authorization": f"Apikey {API_KEY}"})
        current_price_data = current_price_response.json()
        current_price = current_price_data['USD']
        
        # Debugging: Log the historical prices and current price
        logging.info(f"Historical Prices: {historical_prices}")
        logging.info(f"Current Price: {current_price}")
        
        # Convert historical prices to DataFrame
        df = pd.DataFrame(list(historical_prices.items()), columns=['time', 'close'])
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.set_index('time', inplace=True)

        # Add current price to the DataFrame
        current_time = datetime.now()
        df.loc[current_time] = current_price

        # Debugging: Log the DataFrame
        logging.info(f"DataFrame: {df.head()}")

        # Prepare data for Prophet
        df.reset_index(inplace=True)
        df.rename(columns={'time': 'ds', 'close': 'y'}, inplace=True)

        # Train Prophet model with custom seasonality for 4-year cycles
        model = Prophet()
        model.add_seasonality(name='4-year', period=4*365.25, fourier_order=3)
        model.fit(df)

        # Predict future prices for 5 years (1825 days)
        future = model.make_future_dataframe(periods=1825)
        forecast = model.predict(future)

        # Filter out past predictions
        forecast = forecast[forecast['ds'] >= current_time]

        # Debugging: Log the predictions
        logging.info(f"Predicted Future Prices: {forecast[['ds', 'yhat']].tail()}")

        # Plot historical and predicted prices
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['ds'], y=df['y'], mode='lines', name='Historical Prices'))
        fig.add_trace(go.Scatter(x=forecast['ds'], y=forecast['yhat'], mode='lines', name='Predicted Prices'))

        st.subheader(f"Predicted {crypto_symbol} Price Movement")
        st.plotly_chart(fig, use_container_width=True)

        # Return the prediction results as a string
        prediction_results = ", ".join([f"{date.strftime('%Y-%m-%d')}: ${price:.2f}" for date, price in zip(forecast['ds'], forecast['yhat'])])
        return f"Predicted future prices for {crypto_symbol} are: {prediction_results}"
    except Exception as e:
        logging.error(f"An error occurred in predict_future_prices: {e}")
        return f"An error occurred: {e}"

# @tool
# def simulate_crypto_trading(crypto_symbol: str):
#     """Simulate crypto trading with advice from the chatbot and display trades on a live graph."""
#     st.subheader(f"Simulated Trading for {crypto_symbol}")

#     # Initialize balance and trading parameters
#     balance = 1000.0
#     position = 0.0
#     trade_log = []

#     xdata, ydata = [], []

#     while not stop_event.is_set():
#         try:
#             url = f"https://min-api.cryptocompare.com/data/price?fsym={crypto_symbol}&tsyms=USD"
#             response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
#             data = response.json()
#             current_time = datetime.now().strftime('%H:%M:%S')
#             current_price = data['USD']

#             xdata.append(current_time)
#             ydata.append(current_price)

#             # Logging for debugging
#             logging.debug(f"Current time: {current_time}, Current price: {current_price}")
#             logging.debug(f"xdata: {xdata}, ydata: {ydata}")

#             # Ask the chatbot for trading advice
#             advice = agent_executor.invoke({"input": f"Current price of {crypto_symbol} is ${current_price:.2f}. Should I buy, sell, or hold?"})

#             # Trading logic based on chatbot's advice
#             if "buy" in advice.lower() and position == 0:
#                 # Buy
#                 position = balance / current_price
#                 balance = 0.0
#                 trade_log.append(f"Bought {crypto_symbol} at ${current_price:.2f}")

#             elif "sell" in advice.lower() and position > 0:
#                 # Sell
#                 balance = position * current_price
#                 profit = balance - 1000.0
#                 position = 0.0
#                 trade_log.append(f"Sold {crypto_symbol} at ${current_price:.2f}, Profit: ${profit:.2f}")

#             # Display trade log
#             st.write("Trade Log:")
#             for log in trade_log:
#                 st.write(log)

#             time.sleep(60)  # Update every 1 minute

#         except Exception as e:
#             logging.error(f"An error occurred: {e}")
#             st.error(f"An error occurred: {e}")

#     return "Simulation ended."

@tool
def export_trade_log_to_excel(filename: str):
    """Export the trade log to an Excel spreadsheet."""
    if 'trade_log' in st.session_state and st.session_state.trade_log:
        trade_log_df = pd.DataFrame(st.session_state.trade_log)
        trade_log_df.to_excel(filename, index=False)
        return f"Trade log exported to {filename}"
    else:
        return "No trade log available to export."
    

@tool
def read_trade_log_and_display_statistics(filename: str):
    """Read the trade log from an Excel spreadsheet and display statistics."""
    try:
        # Read the Excel file into a DataFrame
        trade_log_df = pd.read_excel(filename)
        
        # Calculate statistics
        total_trades = len(trade_log_df)
        total_profit = trade_log_df['Profit'].sum()
        average_profit_per_trade = trade_log_df['Profit'].mean()
        max_profit = trade_log_df['Profit'].max()
        min_profit = trade_log_df['Profit'].min()
        
        # Calculate loss rate
        loss_trades = trade_log_df[trade_log_df['Profit'] < 0]
        loss_rate = len(loss_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # Display statistics using Streamlit
        st.write(f"**Trade Log Statistics for {filename}:**")
        st.write(f"Total Trades: {total_trades}")
        st.write(f"Total Profit: {total_profit:.2f} USD")
        st.write(f"Average Profit per Trade: {average_profit_per_trade:.2f} USD")
        st.write(f"Maximum Profit: {max_profit:.2f} USD")
        st.write(f"Minimum Profit: {min_profit:.2f} USD")
        st.write(f"Loss Rate: {loss_rate:.2f}%")
        
        # Plot the profits and losses
        plt.figure(figsize=(10, 5))
        plt.bar(trade_log_df.index, trade_log_df['Profit'], color=['red' if x < 0 else 'green' for x in trade_log_df['Profit']])
        plt.xlabel('Trade Number')
        plt.ylabel('Profit (USD)')
        plt.title('Profit and Loss per Trade')
        plt.axhline(0, color='black', linewidth=0.5)
        plt.grid(True)
        
        # Display the plot using Streamlit
        st.pyplot(plt)
        
        # Save the DataFrame to an Excel file named 'cryptolog.xlsx'
        output_filename = 'cryptolog.xlsx'
        trade_log_df.to_excel(output_filename, index=False)
        st.write(f"Trade log has been saved to {output_filename}")
        
        return {
            "Total Trades": total_trades,
            "Total Profit": total_profit,
            "Average Profit per Trade": average_profit_per_trade,
            "Maximum Profit": max_profit,
            "Minimum Profit": min_profit,
            "Loss Rate": loss_rate
        }
    except Exception as e:
        st.error(f"An error occurred while reading the trade log: {e}")
        return {"error": str(e)}