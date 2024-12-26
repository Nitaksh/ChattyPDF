import os
import streamlit as st
from PyPDF2 import PdfReader
import google.generativeai as genai

# Set your Gemini (PaLM) API key
API_KEY = "AIzaSyAAau5hCou3luC9oNwisfMS32tyYCk4aKw"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")  # Use the specified Gemini model

# Streamlit UI Configuration
st.set_page_config(page_title="PDF Chatbot (Gemini)", page_icon="📄", layout="wide")

# Title and Description
st.title("📄 PDF Chatbot (Gemini)")
st.markdown(
    """
    **Interact with your PDFs** - Upload one or multiple PDF files and ask questions about their content.
    The application uses Google's Gemini (PaLM) API to provide responses based on the uploaded files.
    """
)

# Initialize session states
if "uploaded_text" not in st.session_state:
    st.session_state.uploaded_text = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Sidebar for file upload
st.sidebar.header("Upload PDFs")
uploaded_files = st.sidebar.file_uploader(
    "Upload your PDF files here", type=["pdf"], accept_multiple_files=True
)

# Process uploaded PDFs
if uploaded_files:
    st.sidebar.success("Files uploaded successfully!")
    extracted_text = ""

    # Extract text from each uploaded file
    for uploaded_file in uploaded_files:
        try:
            reader = PdfReader(uploaded_file)
            file_text = ""
            for page in reader.pages:
                file_text += page.extract_text()
            extracted_text += f"### File: {uploaded_file.name}\n\n{file_text}\n\n"
        except Exception as e:
            st.error(f"Error reading {uploaded_file.name}: {e}")

    # Store the extracted text in session state
    st.session_state.uploaded_text = extracted_text

# Display extracted content
if st.session_state.uploaded_text:
    with st.expander("View Extracted Content"):
        st.text_area("Extracted Text", st.session_state.uploaded_text, height=300)

# Function to interact with Gemini API
def call_gemini_api(prompt):
    try:
        response = model.generate_content(prompt)
        if response and hasattr(response, "text"):
            return response.text.strip()
        else:
            return "Error: No response from Gemini API."
    except Exception as e:
        return f"Error: {e}"

# Chat Interface
st.subheader("Chat with Your PDFs")
user_input = st.text_input("Ask a question:", placeholder="Type your question here...")

# Send Prompt Button
if st.button("Send Prompt"):
    if not user_input.strip():
        st.warning("Please enter a valid question!")
    elif not st.session_state.uploaded_text.strip():
        st.warning("Please upload PDF(s) before asking a question!")
    else:
        # Combine extracted text with user question as context
        prompt = (
            f"Context: {st.session_state.uploaded_text}\n\n"
            f"Question: {user_input}\n\n"
            "Please provide a detailed and accurate answer based on the context above."
        )
        # Call Gemini API
        assistant_message = call_gemini_api(prompt)
        st.session_state.chat_history.append({"role": "user", "content": user_input})
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_message})

        # Display response
       # Define the HTML content with inline CSS for styling
        html_content = f"""
        <div style="
            padding: 10px;
            background-color: #71797E;
            border: 1px solid #ddd;
            border-radius: 5px;
            height: 500px;
            overflow-y: auto;
        ">
            <h3>Assistant's Response:</h3>
            <p>{assistant_message}</p>
        </div>
        """

        # Render the HTML content using st.markdown
        st.markdown(html_content, unsafe_allow_html=True)

# Display Chat History
if st.session_state.chat_history:
    st.subheader("Chat History")
    for chat in st.session_state.chat_history:
        role = "🧑 User" if chat["role"] == "user" else "🤖 Assistant"
        st.markdown(
            f"""
            **{role}:**
            <div style="padding: 10px; margin-bottom: 10px; background-color: {'#71797E' if role == '🤖 Assistant' else '#71797E'}; border: 1px solid #ddd; border-radius: 5px;">
                {chat['content']}
            </div>
            """,
            unsafe_allow_html=True,
        )
