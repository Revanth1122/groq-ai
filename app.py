
import os
import time
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

# Fetch the API key from the environment
api_key = os.getenv("OPENAI_API_KEY")



# Set page config
st.set_page_config(
    page_title="OpenAI Chat Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load ticket data from file
with open("ticket_data.json", "r") as f:
    ticket_data = json.load(f)

example_conversations = ""
for category, examples in ticket_data.items():
    example_conversations += f"\n\n### Category: {category}\n"
    for convo in examples:
        # Directly add the conversation to the examples without splitting
        example_conversations += f"{convo}\n"  # Convo is added as a whole

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# System prompt with conversation examples
system_prompt = (
    "You are a support assistant that classifies incoming customer messages into one of 11 predefined categories, "
    "based on past conversations. Then, you provide a helpful, concise reply.\n\n"
    "Below are example conversations for each category. Use them as reference:\n"
    f"{example_conversations}\n\n"
    "When a user sends a message, do the following:\n"
    "1. Identify the most appropriate category (out of the 11).\n"
    "2. Provide a concise and helpful response in the style of similar examples.\n"
    "3. If the message is too vague or lacks required details (e.g., 'cancel my order'), politely ask for all the necessary information "
    "to proceed (e.g., order ID, reason for cancellation, etc.).\n"
    "4. If the issue cannot be resolved automatically or appears to be beyond your scope, respond politely with: "
    "\"Thanks for contacting us. This issue needs to be escalated to our support team. Someone will reach out to you shortly.\"\n\n"
    "Respond in the following format:\n"
    "- Category: <Category Name>\n""\n"
    "- Response: <Your helpful response or clarification request>"
)



# Custom CSS for styling
st.markdown("""
    <style>
        .main {
            padding: 2rem;
        }
        .stTextArea textarea {
            min-height: 150px;
        }
        .response-box {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            border-left: 5px solid #10a37f; /* OpenAI green */
        }
        .title {
            color: #10a37f; /* OpenAI green */
        }
        .sidebar .sidebar-content {
            background-color: #f8f9fa;
        }
        @media (max-width: 768px) {
            .main {
                padding: 1rem;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Sidebar for settings
with st.sidebar:
    st.title("⚙️ Settings")
    model = st.selectbox(
        "Select Model",
        ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o"],
        index=0
    )
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.slider("Max Tokens", 100, 4096, 1024, 100)

# Main interface
st.title("Quick Resolver")
st.caption("")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What would you like to ask?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Display assistant response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""  # Initialize response variable
        
        # Call OpenAI API
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": system_prompt}] + [
                    {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True
            )
            
            # Stream the response
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_response += chunk.choices[0].delta.content
                    message_placeholder.markdown(full_response + "▌")
            
            message_placeholder.markdown(full_response)
        
        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            full_response = "Sorry, I couldn't process your request."
            message_placeholder.markdown(full_response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": full_response})
