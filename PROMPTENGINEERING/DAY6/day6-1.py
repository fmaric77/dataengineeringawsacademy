import sys
from langchain_aws import ChatBedrock
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, trim_messages
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnablePassthrough
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from operator import itemgetter

# Initialize model
model_id = "anthropic.claude-3-haiku-20240307-v1:0"
model = ChatBedrock(model_id=model_id)

# Custom ChatMessageHistory to store only the last 50 messages
class LimitedChatMessageHistory(ChatMessageHistory):
    def __init__(self, max_messages=50):
        super().__init__()
        object.__setattr__(self, '_max_messages', max_messages)

    def add_message(self, message):
        super().add_message(message)
        # Trim the history to the last 50 messages
        if len(self.messages) > self._max_messages:
            self.messages = self.messages[-self._max_messages:]

# Setup message history store
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = LimitedChatMessageHistory()
    return store[session_id]

# Define prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are shrek. Answer all questions to the best of your ability."),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# Setup chain with message history
chain = prompt | model
with_message_history = RunnableWithMessageHistory(chain, get_session_history, input_messages_key="messages")

# Trimmer to manage conversation history
trimmer = trim_messages(
    max_tokens=1024,
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

chain = (
    RunnablePassthrough.assign(messages=itemgetter("messages") | trimmer)
    | prompt
    | model
)

with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="messages",
)

# Main loop
current_session_id = "default"
current_language = "English"

def handle_user_input(user_input):
    global current_session_id, current_language

    if user_input.startswith("CONVERSATION "):
        current_session_id = user_input.split(" ")[1]
        print(f"Switched to conversation {current_session_id}")
    elif user_input.startswith("LANGUAGE "):
        current_language = user_input.split(" ")[1]
        print(f"Language set to {current_language}")
    elif user_input == "RESTART":
        store[current_session_id] = LimitedChatMessageHistory()
        print(f"Conversation {current_session_id} restarted")
    elif user_input == "END":
        print("Ending conversation. Goodbye!")
        sys.exit(0)
    elif user_input == "LIST_CONVERSATIONS":
        print("Active conversation IDs:")
        for session_id in store.keys():
            print(session_id)
    else:
        response = with_message_history.invoke(
            {"messages": [HumanMessage(content=user_input)], "language": current_language},
            config={"configurable": {"session_id": current_session_id}},
        )
        print(response.content)

print("Chatbot is running. Type 'END' to terminate, 'CONVERSATION <id>' to switch conversations, 'LANGUAGE <language_name>' to change language, 'RESTART' to restart the current conversation, and 'LIST_CONVERSATIONS' to list all active conversation IDs.")
while True:
    user_input = input("User: ")
    handle_user_input(user_input)