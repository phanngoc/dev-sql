import streamlit as st
import os
from dotenv import load_dotenv
from schema_analyze import generate_sql
from model import Message  # Import the Message model

load_dotenv()  # Load environment variables from a .env file

st.title("🦜🔗 SQL assistant")

if "messages" not in st.session_state:
    # Load messages from the database
    st.session_state["messages"] = [{"role": msg.role, "content": msg.content} for msg in Message.select()]

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password", value=os.getenv("OPENAI_API_KEY"))
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"


def generate_response(input_text):
    print("Generating response...", input_text)

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    # Save user message to the database
    Message.create(role="user", content=prompt)
    
    response = generate_sql(prompt)
    print('response:', response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
    
    # Save assistant response to the database
    Message.create(role="assistant", content=response)