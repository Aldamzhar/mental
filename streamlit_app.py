from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv
import json
import requests
import glob

load_dotenv()

st.title("Mental AI")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o"
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load instruction text from a file
def load_instructions(file_path):
    with open(file_path, "r") as file:
        return file.read()

instruction_txt = load_instructions("instructions.txt")

# Function to save chat history
def save_chat_history():
    if not os.path.exists("chat_history"):
        os.makedirs("chat_history")
    with open("chat_history/continuous_chat.json", "w") as file:
        json.dump(st.session_state.messages, file)

# Function to load chat history
def load_chat_history():
    if os.path.exists("chat_history/continuous_chat.json"):
        with open("chat_history/continuous_chat.json", "r") as file:
            st.session_state.messages = json.load(file)

# Load chat history at the start
# load_chat_history()
                    
# Display messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        
def get_perplexity_response(prompt):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "llama-3-sonar-small-32k-chat",
        "messages": [
            {
                "role": "system",
                "content": ""
            },
            {
                "role": "user",
                "content": prompt + " Search on the matter of the question and provide titles of the credible sources where you find your information below the body of the answer"
            }
        ]
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "Authorization": "Bearer " + st.secrets["PRPLX_API_KEY"]
    }

    response = requests.post(url, json=payload, headers=headers)
    return json.loads(response.text)['choices'][0]['message']['content']        
        
if prompt := st.chat_input("What is up?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):   
        st.markdown(prompt)

    with st.chat_message("assistant"):
        perplexity_response = get_perplexity_response(prompt)
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                {"role": "system", "content": instruction_txt + " " + perplexity_response}
            ],
            stream=True,
        )
        response = st.write_stream(stream)
    st.session_state.messages.append({"role": "assistant", "content": response})
    # save_chat_history()
