from openai import OpenAI
import streamlit as st
import os
from dotenv import load_dotenv
import re
from deep_translator import GoogleTranslator
from lingua import Language, LanguageDetectorBuilder

load_dotenv()

languages = [Language.ENGLISH, Language.RUSSIAN, Language.KAZAKH]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

st.title("Mental")

st.subheader("Your friendly AI companion. 24/7. No data and history chat recorded")

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = st.secrets['OPENAI_MODEL']
if "messages" not in st.session_state:
    st.session_state.messages = []

def load_instructions(file_path):
    with open(file_path, "r") as file:
        return file.read()

instruction_txt = st.secrets['INSTRUCTIONS']

def num_tokens_from_messages(messages):
    return sum([len(message['content'].split()) for message in messages])

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("What is up?"):
    # language = detector.detect_language_of(prompt)
    # prompt_translation = GoogleTranslator(source=language.iso_code_639_1.name.lower(), target='en').translate(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):   
        st.markdown(prompt)

    context = [{"role": "system", "content": instruction_txt}]

    for msg in st.session_state.messages:
        context.append({"role": msg["role"], "content": msg["content"]})
        if num_tokens_from_messages(context) > 8192:
            context.pop(1)  

    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model=st.session_state["openai_model"],
            messages=context,
            stream=True
        )
        response_content = ""
        for stream_resp in stream:
            content = stream_resp.choices[0].delta.content
            if content: 
                response_content += content


        pattern = r'^[^\w.!?]+|[^\w.!?]+$'
        cleaned_string = re.sub(pattern, '', response_content)
        # cleaned_string_translation = GoogleTranslator(source='en', target=language.iso_code_639_1.name.lower()).translate(cleaned_string)
        
        st.session_state.messages.append({"role": "assistant", "content": cleaned_string})
        st.markdown(cleaned_string)
