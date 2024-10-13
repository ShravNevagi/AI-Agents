import streamlit as st
from sales_agent import SalesAgent
import time

# State variables
if 'messages' not in st.session_state:
    st.session_state.messages = []
    
if 'sales_agent' not in st.session_state:
    st.session_state.sales_agent = SalesAgent()

st.title("Sales AI Assistant")

# Sidebar
with st.sidebar:
    st.header("Features")
    st.markdown("""
    This AI Sales Assistant can help you with:
    - Scheduling meetings with clients
    - Sending follow-up emails
    - Providing product information
    
    **Example commands:**
    1. "Schedule a meeting with client@example.com for tomorrow at 2 PM"
    2. "Send a follow-up email to customer@example.com about our meeting"
    3. "What are the features and pricing of product XYZ?"
    """)

# Chat interface
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What can I help you with today?"):
    # User message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""

        # Loading spinner while waiting for the agent's response
        with st.spinner("Thinking..."):
            response = st.session_state.sales_agent.run(prompt)

        # Assistant response to chat history
        st.session_state.messages.append({"role": "assistant", "content": response})
        message_placeholder.markdown(response)

# Clear chat button
if st.button("Clear Chat"):
    st.session_state.messages = []
    st.experimental_rerun()