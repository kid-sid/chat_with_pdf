import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
import os
import shutil
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
# openai_api_key = os.getenv("OPENAI_API_KEY")

# Function to extract text from PDF
def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        try:
            pdf_reader = PdfReader(pdf)
            for page in pdf_reader.pages:
                text += page.extract_text()
        except Exception as e:
            st.error(f"Error reading PDF: {e}")
    return text

# Function to split text into chunks
def get_text_chunks(text):
    if not text.strip():
        return []  # Return empty list if text is empty
    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    return text_splitter.split_text(text)

# Function to create a FAISS vector store
def create_vectorstore(text_chunks, user_dir):
    if not text_chunks:
        st.error("No valid text extracted from the uploaded PDF. Please upload a valid document.")
        return None
    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    vectorstore.save_local(user_dir)
    return vectorstore

# Function to load FAISS vector store
def load_vectorstore(user_dir):
    if os.path.exists(os.path.join(user_dir, "index.faiss")):
        try:
            return FAISS.load_local(user_dir, OpenAIEmbeddings())
        except Exception as e:
            st.error(f"Error loading FAISS index: {e}")
    return None

# Main Streamlit App
def main():
    st.set_page_config(page_title="PDF Chatbot", layout="wide")
    
    # Sidebar Header
    st.sidebar.header("📄 PDF Chatbot")
    st.sidebar.info(
        """
        **How it works:**
        - Upload a PDF document.
        - Ask questions about the uploaded document.
        - Get instant, accurate responses!
        """
    )
    st.sidebar.image("https://via.placeholder.com/300x200?text=PDF+Chatbot", use_column_width=True)

    st.title("📄 Query your PDF")
    st.markdown("### Upload a PDF and start asking questions!")

    # Create a unique directory for each user
    if "user_dir" not in st.session_state:
        st.session_state["user_dir"] = os.path.join("faiss_indices", str(uuid.uuid4()))
        os.makedirs(st.session_state["user_dir"], exist_ok=True)

    user_dir = st.session_state["user_dir"]

    # Load vectorstore if it exists
    vectorstore = load_vectorstore(user_dir)

    # PDF Upload and Processing
    uploaded_files = st.file_uploader(
        "Upload your PDF files here:",
        type=["pdf"],
        accept_multiple_files=False
    )

    if uploaded_files:
        with st.spinner("Processing your PDF..."):
            st.sidebar.success("PDF uploaded successfully!")
            
            # Save uploaded file temporarily
            pdf_path = os.path.join(user_dir, uploaded_files.name)
            with open(pdf_path, "wb") as f:
                f.write(uploaded_files.read())

            # Extract and process text
            pdf_text = get_pdf_text([pdf_path])
            
            # Display file info
            st.sidebar.markdown("#### Uploaded File Details:")
            st.sidebar.markdown(f"📄 **Filename:** {uploaded_files.name}")
            st.sidebar.markdown(f"📦 **Size:** {uploaded_files.size // 1024} KB")
            
            # Progress bar for text processing
            progress_bar = st.progress(0)
            text_chunks = get_text_chunks(pdf_text)
            for i in range(0, 101, 25):
                progress_bar.progress(i)

            # Delete old FAISS index and create a new one
            shutil.rmtree(user_dir, ignore_errors=True)
            os.makedirs(user_dir, exist_ok=True)
            vectorstore = create_vectorstore(text_chunks, user_dir)

        if vectorstore:
            st.success("🎉 PDF processing complete! You can now ask questions.")
        else:
            st.warning("⚠️ Could not process the uploaded PDF. Please try again with a different file.")

    # Ensure vectorstore is loaded
    if vectorstore:
        # Initialize conversation chain
        llm = ChatOpenAI(model='gpt-3.5-turbo', temperature=0)
        memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
        conversation_chain = ConversationalRetrievalChain.from_llm(
            llm=llm,
            retriever=vectorstore.as_retriever(),
            memory=memory
        )

        if "chat_history" not in st.session_state:
            st.session_state["chat_history"] = []

        # Chat Interface
        user_input = st.text_input("Ask a question about the uploaded PDF:", key="user_input")

        if user_input:
            with st.spinner("Fetching response..."):
                response = conversation_chain({
                    "question": user_input,
                    "chat_history": st.session_state["chat_history"]
                })
                st.session_state["chat_history"].append({"user": user_input, "bot": response["answer"]})

            # Display Chat History
            chat_container = st.container()
            for chat in st.session_state["chat_history"]:
                with chat_container:
                    st.markdown(f"**You:** {chat['user']}")
                    st.markdown(f"**Lana:** {chat['bot']}")

    else:
        st.warning("📂 Please upload a PDF file to get started.")

# Run the app
if __name__ == "__main__":
    main()
