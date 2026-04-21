import streamlit as st
import PyPDF2
from api_client import APIClient

st.set_page_config(page_title="Document Q&A Engine", layout="wide")

api_client = APIClient()

# Initialize from DB on load
if "messages" not in st.session_state:
    st.session_state.messages = api_client.get_history()
if "document_text" not in st.session_state:
    st.session_state.document_text = ""
if "summary" not in st.session_state:
    st.session_state.summary = ""

with st.sidebar:
    st.header("⚙️ Configuration")
    if st.button("🗑️ Clear Document", use_container_width=True):
        st.session_state.document_text = ""
        st.session_state.summary = ""
        st.success("Document cleared!")
        
    if st.button("🚨 Deep Clean (Wipe Database & Vectors)", use_container_width=True):
        with st.spinner("Purging databases..."):
            api_client.clear_all()
            st.session_state.messages = []
            st.session_state.document_text = ""
            st.session_state.summary = ""
            st.success("System completely reset!")

st.title("📄 Document Q&A & Summarization Engine")
col1, col2 = st.columns(2)

with col1:
    st.header("📤 Upload Document")
    uploaded_file = st.file_uploader("Choose a PDF file", type=["pdf"])
    
    if uploaded_file is not None:
        try:
            pdf_reader = PyPDF2.PdfReader(uploaded_file)
            extracted_text = ""
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
            st.session_state.document_text = extracted_text
            st.success(f"✅ Loaded: {uploaded_file.name}")
        except Exception as e:
            st.error(f"Error loading document: {str(e)}")

with col2:
    st.header("✨ Generate Summary")
    if st.session_state.document_text:
        if st.button("📝 Generate Summary", use_container_width=True):
            with st.spinner("Generating summary..."):
                try:
                    st.session_state.summary = api_client.summarize(st.session_state.document_text)
                    st.info(st.session_state.summary)
                except Exception as e:
                    st.error(f"Error generating summary: {str(e)}")

st.header("💬 Ask Questions")
if st.session_state.document_text:
    # Display historical messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
            
    # Input for new question
    if prompt := st.chat_input("Ask a question about the document..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
            
        with st.spinner("Finding answer..."):
            try:
                answer = api_client.ask_question(st.session_state.document_text, prompt)
                st.session_state.messages.append({"role": "assistant", "content": answer})
                with st.chat_message("assistant"):
                    st.write(answer)
            except Exception as e:
                st.error(f"Error getting answer: {str(e)}")
else:
    st.info("📌 Upload a document first to start asking questions")