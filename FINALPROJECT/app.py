import json
import streamlit as st
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from weathertools import get_current_weather, get_weather_forecast
from wikipediatools import get_city_highlights

# Bind tools to model
chat_model_id = "anthropic.claude-3-haiku-20240307-v1:0"
chat_model = ChatBedrock(model_id=chat_model_id).bind_tools([get_current_weather, get_weather_forecast, get_city_highlights])

# Create agent with prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Use the tools at your disposal to answer questions."),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}")
])

# Initialize memory for chat history
memory = ChatMessageHistory()

# Define tools
tools = [get_current_weather, get_weather_forecast, get_city_highlights]

# Create agent and executor
agent = create_tool_calling_agent(chat_model, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
with_message_history = RunnableWithMessageHistory(agent_executor, lambda x: memory, input_messages_key="input")

# Function to handle user input
def handle_user_input(user_input):
    try:
        response = with_message_history.invoke({"input": user_input}, config={"configurable": {"session_id": "stringx"}})
        # Extract and format the bot's response
        bot_response = response['output']
        return bot_response
    except Exception as e:
        return f"An error occurred: {e}"

# Streamlit UI
st.title("Weather and Olympic Data Chatbot")

# Images for user and bot
user_image = "https://via.placeholder.com/50/007bff/ffffff?text=U"
bot_image = "https://via.placeholder.com/50/ff0000/ffffff?text=B"

# Function to display messages
def display_message(image_url, sender, message, is_user=True):
    col1, col2 = st.columns([1, 9])
    with col1:
        st.image(image_url, width=50)
    with col2:
        if is_user:
            st.write(f"**{sender}:** {message}", unsafe_allow_html=True)
        else:
            st.write(f"**{sender}:** {message}", unsafe_allow_html=True)

user_input = st.text_input("Enter your query:")
if st.button("Send"):
    display_message(user_image, "User", user_input, is_user=True)
    response = handle_user_input(user_input)
    if response:  # Only display the bot's response if it's not empty
        display_message(bot_image, "Bot", response, is_user=False)