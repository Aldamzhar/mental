from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv
import json
import requests
import glob
import re
from deep_translator import GoogleTranslator
from lingua import Language, LanguageDetectorBuilder

load_dotenv()

languages = [Language.ENGLISH, Language.RUSSIAN, Language.KAZAKH]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

st.title("Mental")

st.subheader("Your AI therapist. 24/7. No data recorded. Limited free access!")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = st.secrets['OPENAI_MODEL']
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load instruction text from a file
def load_instructions(file_path):
    with open(file_path, "r") as file:
        return file.read()

instruction_txt = load_instructions("instructions.txt")

# # Function to save chat history
# def save_chat_history():
#     if not os.path.exists("chat_history"):
#         os.makedirs("chat_history")
#     with open("chat_history/continuous_chat.json", "w") as file:
#         json.dump(st.session_state.messages, file)

# # Function to load chat history
# def load_chat_history():
#     if os.path.exists("chat_history/continuous_chat.json"):
#         with open("chat_history/continuous_chat.json", "r") as file:
#             st.session_state.messages = json.load(file)

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
    language = detector.detect_language_of(prompt)
    print(language.iso_code_639_1.name)
    prompt_translation = GoogleTranslator(source=language.iso_code_639_1.name.lower(), target='en').translate(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):   
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # perplexity_response = get_perplexity_response(prompt)
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=[
                # {"role": "system", "content": prompt + " " + instruction_txt + " " + perplexity_response}
                {"role": "system", "content": prompt_translation + "" + instruction_txt}
            ],
            stream=True
        )
        response_content = ""
        for stream_resp in stream:
            print(stream_resp.choices[0].delta.content)
            content = stream_resp.choices[0].delta.content
            if content: 
                response_content += content

        output_string = response_content
        pattern = r'^[^\w.!?]+|[^\w.!?]+$'
        cleaned_string = re.sub(pattern, '', output_string)
        cleaned_string_translation = GoogleTranslator(source='en', target=language.iso_code_639_1.name.lower()).translate(cleaned_string)
        st.session_state.messages.append({"role": "assistant", "content": cleaned_string_translation})
        st.markdown(cleaned_string_translation)
