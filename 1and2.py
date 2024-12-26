import os
import streamlit as st
from PyPDF2 import PdfReader
import requests
import json

# Function to interact with the LLM API for chat
def interact_with_ollama_stream(api_url, model, messages):
    headers = {
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "stream": True
    }

    try:
        response = requests.post(api_url, headers=headers, data=json.dumps(payload), stream=True)
        if response.status_code != 200:
            return f"Error: {response.text}"

        # Yield the streamed content line by line
        def generate():
            for line in response.iter_lines():
                if line:
                    try:
                        data = json.loads(line)
                        yield data.get("response", "")  # Yield the response part
                    except json.JSONDecodeError as e:
                        yield f"Error: {e} in line: {line.decode('utf-8')}"
        return generate()

    except requests.RequestException as e:
        return f"Error interacting with LLM API: {e}"

# Initialize Streamlit session state for extracted content and chat history
if "final_doc" not in st.session_state:
    st.session_state.final_doc = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Streamlit App Title
st.title("Chatty PDF Parser")

# File Uploader for PDFs
uploaded_files = st.file_uploader(
    "Upload PDF files", type=["pdf"], accept_multiple_files=True
)

if uploaded_files:
    # Save files to the local 'uploads' directory
    save_dir = os.path.join(os.getcwd(), "uploads")
    os.makedirs(save_dir, exist_ok=True)

    st.subheader("Extracted Text and PDF Information")

    # Iterate through uploaded files
    for uploaded_file in uploaded_files:
        # Save each file locally
        file_path = os.path.join(save_dir, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Read the PDF file
        reader = PdfReader(file_path)

        # Extract text from each page
        content = ""
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            st.markdown(f"### Page {i+1}")
            st.text(text)
            content += text

        # Append extracted content to final_doc
        st.session_state.final_doc += content

    st.success("Text extraction completed! Ready to send to the LLM.")

# Display the extracted text (final_doc)
st.subheader("Extracted Text from PDFs")
st.text_area("Extracted Content", st.session_state.final_doc, height=300)

# Inputs for LLM interaction
st.subheader("Chat with the Extracted Content")
prompt = st.text_area("Enter your prompt:", placeholder="Ask a question about the extracted text...")
model = st.text_input("Model", "llama3.2")

# Button to send the prompt
if st.button("Send Prompt"):
    if not prompt:
        st.warning("Please enter a prompt!")
    else:
        st.info("Sending your request...")

        api_url = "http://localhost:11434/api/chat"  # Update this URL as needed

        # Append the user prompt to the chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Add extracted content to the chat history as context
        context_message = {"role": "system", "content": st.session_state.final_doc}
        st.session_state.chat_history.insert(0, context_message)

        # To hold the assistant's response
        assistant_response = ""

        # Use custom CSS for scrollable response box
        st.markdown(
            """
            <style>
            .scrollable-textbox {
                height: 400px;
                overflow-y: auto;
                background-color: #36454F;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 5px;
                font-size: 16px;
                font-family: "Courier New", monospace;
                color: white;
                white-space: pre-wrap;
                word-wrap: break-word;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Get the streaming response and append it progressively
        response_container = st.empty()  # Placeholder for the response box
        for response_text in interact_with_ollama_stream(api_url, model, st.session_state.chat_history):
            assistant_response += response_text
            response_container.markdown(
                f'<div class="scrollable-textbox">{assistant_response}</div>', 
                unsafe_allow_html=True
            )

        # Add the assistant's full response to the chat history
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})

# Display chat history
st.subheader("Chat History")
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    elif message["role"] == "assistant":
        st.markdown(f"**Assistant:** {message['content']}")
    elif message["role"] == "system":
        st.markdown(f"**System (Context):** {message['content']}")
