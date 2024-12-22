import streamlit as st
import os
from dotenv import load_dotenv
from schema_analyze import generate_sql, analyzer
from model import Message, Thread

load_dotenv()  # Load environment variables from a .env file

st.title("🦜🔗 SQL assistant")

if "messages" not in st.session_state:
    # Load messages from the database
    st.session_state["messages"] = [{"role": msg.role, "content": msg.content} for msg in Message.select()]

with st.sidebar:
    openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password", value=os.getenv("OPENAI_API_KEY"))
    "[Get an OpenAI API key](https://platform.openai.com/account/api-keys)"
    threads = Thread.select().order_by(Thread.created_at.desc()).limit(20)
    
    if not threads:
        # Create a new thread if none exist
        new_thread = Thread.create(name="Default Thread")
        threads = [new_thread]
    
    for thread in threads:
        st.write(f"{thread.id}: {thread.name} (Created at: {thread.created_at})")
    
    # Get the latest thread ID
    latest_thread_id = threads[0].id if threads else None
    selected_thread_id = st.selectbox("Select Thread", [thread.id for thread in threads], index=0 if latest_thread_id else -1)
    
    new_thread_name = st.text_input("New Thread Name")
    if st.button("Create Thread"):
        Thread.create(name=new_thread_name)

def generate_response(input_text):
    print("Generating response...", input_text)

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])


# Add a selectbox to choose a valid table
valid_tables = analyzer.get_schema().keys()
selected_tables = st.multiselect("Select Tables", valid_tables, default=None, help="Search")

if prompt := st.chat_input():
    if not openai_api_key:
        st.info("Please add your OpenAI API key to continue.")
        st.stop()

    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    Message.create(role="user", content=prompt, thread_id=selected_thread_id)
    
    response = generate_sql(prompt, valid_tables)
    print('response:', response)
    st.session_state.messages.append({"role": "assistant", "content": response})
    st.chat_message("assistant").write(response)
    
    # Save assistant response to the database
    Message.create(role="assistant", content=response, thread_id=selected_thread_id)