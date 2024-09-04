import os
import json
import requests
import boto3
import numpy as np
import plotly.graph_objs as go
import streamlit as st
from opensearchpy import OpenSearch
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from datetime import datetime, timedelta
import time
import threading
import logging
import pandas as pd
from prophet import Prophet
from langchain.tools import tool

# Import tools from tools.py
from tools import fetch_current_price, convert_price, fetch_historical_prices, load_live_graph, close_live_graph, predict_future_prices

stop_event = threading.Event()
API_KEY = "113c5d6f3c5b5365e1ae5e63039150abe56f0ec4cde2002798000cdcc0d67c23"

# Initialize session state for trade log
if 'trade_log' not in st.session_state:
    st.session_state.trade_log = []

# Define the simulate_crypto_trading tool
@tool
def simulate_crypto_trading(crypto_symbol: str):
    """Simulate crypto trading with advice from the chatbot and display trades on a live graph."""
    if 'graph_initialized' not in st.session_state:
        st.subheader(f"Simulated Trading for {crypto_symbol}")

        # Initialize the Plotly figure and chart
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[], y=[], mode='lines+markers', name='Price'))
        price_chart = st.plotly_chart(fig, use_container_width=True)

        # Store the figure and chart in session state
        st.session_state.fig = fig
        st.session_state.price_chart = price_chart
        st.session_state.graph_initialized = True

    # Initialize balance and trading parameters
    balance = 1000.0
    position = 0.0

    xdata, ydata = [], []

    while not stop_event.is_set():
        try:
            url = f"https://min-api.cryptocompare.com/data/price?fsym={crypto_symbol}&tsyms=USD"
            response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
            data = response.json()
            current_time = datetime.now().strftime('%H:%M:%S')
            current_price = data['USD']

            xdata.append(current_time)
            ydata.append(current_price)

            # Update the Plotly figure
            st.session_state.fig.data[0].x = xdata
            st.session_state.fig.data[0].y = ydata
            st.session_state.price_chart.plotly_chart(st.session_state.fig, use_container_width=True)

            # Logging for debugging
            logging.debug(f"Current time: {current_time}, Current price: {current_price}")
            logging.debug(f"xdata: {xdata}, ydata: {ydata}")

            # Prepare trade log for the chatbot
            if not st.session_state.trade_log:
                trade_log_str = "No previous trades."
            else:
                trade_log_str = json.dumps(st.session_state.trade_log)

            # Ask the chatbot for trading advice
            advice_response = agent_executor.invoke({
                "input": f"Current price of {crypto_symbol} is ${current_price:.2f}. Here is the trade log: {trade_log_str}. Should I buy, sell, or hold?"
            })
            advice = advice_response.get('output', '')

            # Ensure advice is a string
            if isinstance(advice, dict):
                advice = advice.get('text', '')

            # Trading logic based on chatbot's advice
            if "buy" in advice.lower() and position == 0:
                # Buy
                position = balance / current_price
                balance = 0.0
                st.session_state.trade_log.append({"Action": "Buy", "Price": current_price, "Time": current_time})

            elif "sell" in advice.lower() and position > 0:
                # Sell
                balance = position * current_price
                profit = balance - 1000.0
                position = 0.0
                st.session_state.trade_log.append({"Action": "Sell", "Price": current_price, "Time": current_time, "Profit": profit})

            elif "hold" in advice.lower():
                # Hold
                if not st.session_state.trade_log or st.session_state.trade_log[-1]["Action"] != "Hold":
                    st.session_state.trade_log.append({"Action": "Hold", "Price": current_price, "Time": current_time})

            # Display trade log
            trade_log_df = pd.DataFrame(st.session_state.trade_log)
            st.write("Trade Log:")
            st.write(trade_log_df)  # Use st.write instead of st.table for better compatibility

            time.sleep(5)  # Update every 1 minute

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            st.error(f"An error occurred: {e}")

    return "Simulation ended."

# Bind tools to model
chat_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
chat_model = ChatBedrock(model_id=chat_model_id).bind_tools([fetch_current_price,fetch_historical_prices, convert_price, load_live_graph, close_live_graph, predict_future_prices, simulate_crypto_trading])

# Create agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful Crypto assistant. Use the tools at your disposal to answer questions about cryptocurrencies and to trade."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])
memory = ChatMessageHistory()

tools = [fetch_current_price, convert_price, load_live_graph, close_live_graph, predict_future_prices, simulate_crypto_trading]
agent = create_tool_calling_agent(chat_model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
with_message_history = RunnableWithMessageHistory(agent_executor, lambda x: memory, input_messages_key="input")

# Chatbot main loop
def handle_user_input(user_input):
    try:
        response = with_message_history.invoke({"input": user_input}, config={"configurable": {"session_id": "stringx"}})
        # Extract and format the bot's response
        bot_response = response['output']
        return bot_response
    except Exception as e:
        return f"An error occurred: {e}"

# Create UI using Streamlit
st.title("Crypto Chatbot")

user_input = st.text_input("Enter your query:")
if st.button("Send"):
    response = handle_user_input(user_input)
    st.write(f"**User:** {user_input}")
    if response:  # Only display the bot's response if it's not empty
        st.write(f"**Bot:** {response}")