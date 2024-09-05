import os
import json
import requests
import boto3
import numpy as np
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
from tools import fetch_current_price, convert_price, fetch_historical_prices, load_live_graph, close_live_graph, predict_future_prices,fetch_graphical_historical_prices 

stop_event = threading.Event()
API_KEY = "113c5d6f3c5b5365e1ae5e63039150abe56f0ec4cde2002798000cdcc0d67c23"

# Initialize session state for trade log and cumulative profit
if 'trade_log' not in st.session_state:
    st.session_state.trade_log = []
if 'cumulative_profit' not in st.session_state:
    st.session_state.cumulative_profit = 0.0
if 'balance' not in st.session_state:
    st.session_state.balance = 100000.0
if 'position' not in st.session_state:
    st.session_state.position = 0.0
if 'buy_price' not in st.session_state:
    st.session_state.buy_price = 0.0

# Define the simulate_crypto_trading tool
@tool
def simulate_crypto_trading(crypto_symbol: str):
    """Simulate crypto trading with advice from the chatbot. DO NOT CALL PREDICT_FUTURE_PRICES, LOAD_LIVE_GRAPH, DO NOT CALL fetch_graphical_historical_prices IN THIS FUNCTION """
    # Prepare trade log for the chatbot
    if not st.session_state.trade_log:
        trade_log_str = "No previous trades."
    else:
        trade_log_str = json.dumps(st.session_state.trade_log)

    while not stop_event.is_set():
        try:
            # Fetch current price
            url = f"https://min-api.cryptocompare.com/data/price?fsym={crypto_symbol}&tsyms=USD"
            response = requests.get(url, headers={"authorization": f"Apikey {API_KEY}"})
            data = response.json()
            current_time = datetime.now().strftime('%H:%M:%S')
            current_price = data['USD']

            # Fetch historical prices
            historical_prices = fetch_historical_prices(crypto_symbol)
            historical_prices_str = json.dumps(historical_prices)

            # Ask the chatbot for trading advice
            logging.debug("Invoking agent_executor for trading advice...")
            advice_response = agent_executor.invoke({
                "input": f"Current price of {crypto_symbol} is {current_price}. Here is the trade log: {trade_log_str}. Here are the historical prices: {historical_prices_str}. Should I buy, sell, or hold?"
            })
            logging.debug(f"Advice response: {advice_response}")
            advice = advice_response.get('output', '')

            # Ensure advice is a string
            if isinstance(advice, dict):
                advice = advice.get('text', '')

            logging.debug(f"Received advice: {advice}")

            # Trading logic based on chatbot's advice
            if "buy" in advice.lower() and st.session_state.position == 0:
                # Buy
                if st.session_state.balance > 0:
                    st.session_state.position = st.session_state.balance / current_price
                    st.session_state.buy_price = current_price
                    st.session_state.balance = 0.0
                    st.session_state.trade_log.append({"Action": "Buy", "Price": current_price, "Time": current_time, "Amount": st.session_state.position})
                else:
                    # Hold if balance is zero
                    st.session_state.trade_log.append({"Action": "Hold", "Price": current_price, "Time": current_time})

            elif "sell" in advice.lower() and st.session_state.position > 0:
                # Calculate potential profit
                sell_price = current_price
                potential_profit = (sell_price - st.session_state.buy_price) * st.session_state.position

                # Only execute sell if it results in non-zero profit
                if potential_profit > 0:
                    st.session_state.balance = st.session_state.position * sell_price
                    st.session_state.cumulative_profit += potential_profit
                    st.session_state.trade_log.append({"Action": "Sell", "Price": sell_price, "Time": current_time, "Amount": st.session_state.position, "Profit": potential_profit, "Cumulative Profit": st.session_state.cumulative_profit})
                    st.session_state.position = 0.0
                    st.session_state.buy_price = 0.0
                else:
                    # Hold if the profit is not positive
                    st.session_state.trade_log.append({"Action": "Hold", "Price": current_price, "Time": current_time})

            elif "hold" in advice.lower() or (("sell" in advice.lower() and potential_profit <= 0)):
                # Hold
                if not st.session_state.trade_log or st.session_state.trade_log[-1]["Action"] != "Hold":
                    st.session_state.trade_log.append({"Action": "Hold", "Price": current_price, "Time": current_time})

            # Display trade log
            trade_log_df = pd.DataFrame(st.session_state.trade_log)
            st.write("Trade Log:")
            st.write(trade_log_df)  # Use st.write instead of st.table for better compatibility

            # Display cumulative profit and balance
            st.write(f"Cumulative Profit: {st.session_state.cumulative_profit:.2f} USD")
            st.write(f"Current Balance: {st.session_state.balance:.2f} USD")

            time.sleep(5)  # Update every 5 seconds

        except Exception as e:
            logging.error(f"An error occurred: {e}")
            st.error(f"An error occurred: {e}")

    return "Simulation ended."

# Bind tools to model
chat_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
chat_model = ChatBedrock(model_id=chat_model_id).bind_tools([fetch_current_price, fetch_historical_prices, simulate_crypto_trading, load_live_graph,predict_future_prices,fetch_graphical_historical_prices])

# Create agent
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful Crypto assistant. Use the tools at your disposal to answer questions about cryptocurrencies and to trade."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])
memory = ChatMessageHistory()

tools = [simulate_crypto_trading,fetch_current_price, fetch_historical_prices, load_live_graph,predict_future_prices,fetch_graphical_historical_prices]
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
st.title("Crypto Trading Chatbot")

user_input = st.text_input("Enter your query:")
if st.button("Send"):
    response = handle_user_input(user_input)
    st.write(f"**User:** {user_input}")
    if response:  # Only display the bot's response if it's not empty
        st.write(f"**Bot:** {response}")