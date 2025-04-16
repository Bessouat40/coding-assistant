import json
from typing import List

from fastapi import logger
import streamlit as st
import requests
import os
import tiktoken

FASTAPI_BACKEND_URL = os.getenv("FASTAPI_URL", "http://localhost:8000")
SET_DIR_ENDPOINT = f"{FASTAPI_BACKEND_URL}/set_working_directory"
GENERATE_ENDPOINT = f"{FASTAPI_BACKEND_URL}/generate"

TOKENIZER_NAME = "cl100k_base"
try:
    tokenizer = tiktoken.get_encoding(TOKENIZER_NAME)
except:
    st.error(f"Could not load tokenizer '{TOKENIZER_NAME}'. Falling back to p50k_base.")
    TOKENIZER_NAME = "p50k_base"
    tokenizer = tiktoken.get_encoding(TOKENIZER_NAME)

MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", 32000))

st.set_page_config(page_title="Coding Assistant (Session Memory)", layout="wide")
st.title("🤖 Simple Coding Assistant (Session Memory Only)")
st.caption(f"Conversation history is kept for this session (Max Context: ~{MAX_CONTEXT_TOKENS} tokens).")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "working_directory" not in st.session_state:
    st.session_state.working_directory = None

def count_tokens(text):
    """Counts tokens using the loaded tokenizer."""
    return len(tokenizer.encode(text))

def truncate_history(messages: List[dict], max_tokens: int) -> List[dict]:
    """
    Truncates message history to fit within max_tokens.
    Keeps newest messages. Always keeps the last (current user) message.
    Assumes message format: {"role": str, "content": str}
    """
    buffer_tokens = 50
    target_token_limit = max_tokens - buffer_tokens
    truncated_messages = []
    current_tokens = 0
    preserved_system_message = None

    if messages and messages[0]["role"] == "system":
        preserved_system_message = messages[0]
        system_tokens = count_tokens(preserved_system_message["content"])
        current_tokens += system_tokens

    start_index = 1 if preserved_system_message else 0
    for msg in reversed(messages[start_index:]):
        msg_tokens = count_tokens(msg["content"])
        if current_tokens + msg_tokens <= target_token_limit:
            truncated_messages.insert(0, msg)
            current_tokens += msg_tokens
        else:
            st.warning(f"Context limit reached. Truncating older messages ({current_tokens}/{target_token_limit} tokens used).", icon="⚠️")
            break

    if preserved_system_message:
         if current_tokens <= target_token_limit:
              truncated_messages.insert(0, preserved_system_message)
         else:
              st.warning("Could not fit system prompt within token limit after truncation.", icon="⚠️")

    if not truncated_messages and messages:
         last_msg = messages[-1]
         if preserved_system_message and last_msg != preserved_system_message:
              truncated_messages = [preserved_system_message, last_msg]
         else:
              truncated_messages = [last_msg]
         st.warning("Warning: The last message might exceed the token limit.", icon="⚠️")
    elif messages and truncated_messages[-1]['content'] != messages[-1]['content']:
         pass


    if len(truncated_messages) < len(messages):
         logger.info(f"History truncated from {len(messages)} to {len(truncated_messages)} messages.")

    return json.dumps(truncated_messages)


with st.sidebar:
    st.header("Project Settings")
    st.write("Enter the **absolute path** to your local project directory.")
    with st.form("directory_form"):
        dir_path_input = st.text_input(
            "Project Directory Path",
            value=st.session_state.working_directory or "",
            placeholder="/path/to/your/project",
        )
        submitted = st.form_submit_button("Set Directory (Global)")
        if submitted:
             if not dir_path_input:
                st.warning("Please enter a directory path.")
             else:
                try:
                    response = requests.post(SET_DIR_ENDPOINT, json={"path": dir_path_input})
                    response.raise_for_status()
                    result = response.json()
                    st.session_state.working_directory = result.get("current_path")
                    st.success(result.get("message", "Directory set successfully!"))
                except requests.exceptions.RequestException as e:
                    st.error(f"Failed to set directory via API: {e}")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {e}")


    if st.session_state.working_directory:
        st.success(f"Current Directory Context: `{st.session_state.working_directory}`")
    else:
        st.info("No project directory context set.")

    if st.button("Clear Chat History"):
         st.session_state.messages = []
         st.toast("Chat history cleared.")
         st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask a question..."):
    user_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(user_message)

    with st.chat_message("user"):
        st.markdown(prompt)

    history_to_process = list(st.session_state.messages)

    messages_to_send = truncate_history(history_to_process, MAX_CONTEXT_TOKENS)

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        with st.spinner("Thinking..."):
            try:
                payload = {"query": messages_to_send}
                print(payload)
                api_response = requests.post(GENERATE_ENDPOINT, json=payload)
                api_response.raise_for_status()

                response_data = api_response.json()
                assistant_response_content = response_data.get("response")

                if assistant_response_content:
                    full_response = assistant_response_content
                    message_placeholder.markdown(full_response)
                    st.session_state.messages.append({"role": "assistant", "content": full_response})
                else:
                    full_response = "Error: Received an empty response from the backend."
                    message_placeholder.error(full_response)

            except requests.exceptions.RequestException as e:
                st.error(f"Error communicating with API: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")