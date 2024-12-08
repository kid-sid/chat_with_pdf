import streamlit as st
import os
import uuid
import shutil
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from database import init_db, save_user_query, signup_user, login_user, get_api_key, save_api_key, get_user_queries  # Import database functions
from dotenv import load_dotenv
import openai, re

load_dotenv()

# PDF Processing Functions
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

def get_text_chunks(text):
    if not text.strip():
        return []
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=200, length_function=len
    )
    return text_splitter.split_text(text)

def create_vectorstore(text_chunks, user_dir, openai_api_key):
    if not text_chunks:
        st.error("No valid text extracted from the uploaded PDF.")
        return None
    embeddings = OpenAIEmbeddings(openai_api_key=openai_api_key)
    vectorstore = FAISS.from_texts(texts=text_chunks, embedding=embeddings)
    vectorstore.save_local(user_dir)
    return vectorstore

def load_vectorstore(user_dir, openai_api_key):
    if os.path.exists(os.path.join(user_dir, "index.faiss")):
        try:
            return FAISS.load_local(user_dir, OpenAIEmbeddings(openai_api_key=openai_api_key))
        except Exception as e:
            st.error(f"Error loading FAISS index: {e}")
    return None


def validate_api_key(api_key):
    
    # Define the regex pattern for the API key validation
    pattern = r"^sk-.{161}$" 
    
    # Check if the provided API key matches the pattern
    if re.match(pattern, api_key):
        print("API Key is valid!")
        return True
    else:
        print("Invalid API Key!")
        return False



# Main Streamlit App
def main():
    st.set_page_config(page_title="PDF Chatbot with Authentication", layout="wide")
    st.sidebar.title("PDF Chatbot")

    # Initialize database
    init_db()

    # Initialize session state variables
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        st.sidebar.subheader("Login / Signup")

        option = st.sidebar.radio("Select an option:", ["Login", "Signup"])

        username = st.sidebar.text_input("Username")
        password = st.sidebar.text_input("Password", type="password")
        openai_api_key = st.sidebar.text_input("OpenAI API Key", type="password")

        # Signup logic
        if option == "Signup":
            if st.sidebar.button("Signup"):
                if validate_api_key(openai_api_key):
                    if signup_user(username, password):
                        save_api_key(username, openai_api_key)  # Save API key during signup
                        st.success("Signup successful! Please login.")
                    else:
                        st.error("Username already exists. Please try a different one.")
                else:
                    st.warning("Invalid API Key. Please provide a valid OpenAI API Key.")

        # Login logic
        elif option == "Login":
            if st.sidebar.button("Login"):
                if validate_api_key(openai_api_key):
                    if login_user(username, password, openai_api_key):  # Pass API key here
                        st.session_state["logged_in"] = True
                        st.session_state["username"] = username
                        st.success(f"Welcome, {username}!")
                    else:
                        st.error("Invalid username, password, or API key.")
                else:
                    st.warning("Invalid API Key. Please provide a valid OpenAI API Key.")

            # Optional: Prompt for API Key if not provided
            if not openai_api_key:
                st.warning("Please provide your OpenAI API Key to log in.")

    else:
        st.sidebar.success(f"Logged in as {st.session_state['username']}")

    # Logout option
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state.pop("username", None)
        st.experimental_rerun()

    # Main app logic after login
    if st.session_state["logged_in"]:
        st.title("📄 Query your PDF")

        # Fetch the stored OpenAI API key
        openai_api_key = get_api_key(st.session_state["username"])
        if not openai_api_key:
            st.error("No OpenAI API key found. Please log out and provide your API key during login.")
            return

        # Ensure valid API key is entered before continuing
        if openai_api_key.strip() == "":
            st.error("OpenAI API Key is required to proceed.")
            return

        # Query history button and functionality
        if st.button("Show Query History"):
            user_queries = get_user_queries(st.session_state["username"])
            if user_queries:
                st.markdown("### Previous Queries")
                for question, answer in user_queries:
                    st.markdown(f"**Question:** {question}")
                    st.markdown(f"**Answer:** {answer}")
            else:
                st.info("No queries found.")

        # Rest of your chatbot functionality
        uploaded_files = st.file_uploader("Upload your PDF:", type=["pdf"])

        user_dir = os.path.join("faiss_indices", st.session_state["username"])
        os.makedirs(user_dir, exist_ok=True)

        vectorstore = load_vectorstore(user_dir, openai_api_key)

        if uploaded_files:
            with st.spinner("Processing your PDF..."):
                pdf_text = get_pdf_text([uploaded_files])
                text_chunks = get_text_chunks(pdf_text)

                shutil.rmtree(user_dir, ignore_errors=True)
                os.makedirs(user_dir, exist_ok=True)
                vectorstore = create_vectorstore(text_chunks, user_dir, openai_api_key)

            if vectorstore:
                st.success("PDF processed! Ask questions below.")

        # Ensure vectorstore is loaded
        if vectorstore:
            llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=openai_api_key)
            memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
            conversation_chain = ConversationalRetrievalChain.from_llm(
                llm=llm, retriever=vectorstore.as_retriever(), memory=memory
            )

            if "chat_history" not in st.session_state:
                st.session_state["chat_history"] = []

            user_input = st.text_input("Ask a question about the uploaded PDF:", key="user_input")

            if user_input:
                with st.spinner("Fetching response..."):
                    response = conversation_chain({
                        "question": user_input,
                        "chat_history": st.session_state["chat_history"]
                    })
                    answer = response["answer"]

                    # Save the question and answer to the database
                    save_user_query(st.session_state["username"], user_input, answer)

                    # Update chat history
                    st.session_state["chat_history"].append({"user": user_input, "bot": answer})

                # Display chat history
                st.markdown("### Chat History:")
                for chat in st.session_state["chat_history"]:
                    st.markdown(f"**You:** {chat['user']}")
                    st.markdown(f"**Bot:** {chat['bot']}")
        else:
            st.info("Upload a PDF to start asking questions.")

# Run the app
if __name__ == "__main__":
    main()
