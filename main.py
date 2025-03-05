
# main.py
import os
from openai_setup import openai
from langchain_community.chat_models import ChatOpenAI
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from file_reader import FileReader
from chunk_maker import chunk_documents
import time

# Initialize embeddings
embeddings = OpenAIEmbeddings()

# Initialize the language model
llm = ChatOpenAI(
    model_name="gpt-4o",  # Use "gpt-4" if you have access
    temperature=0.7
)

# Path to the folder containing all training data
training_data_folder = "/Users/moss_kibria/Capstone/Chatbot_full/Data"

# Path to the saved vector store
faiss_directory = "medical_knowledge_base"
faiss_path = os.path.join(faiss_directory, "index.faiss")

vector_store = None  # Global variable for the vector store
qa_chain = None      # Global variable for the QA chain

# Function to initialize the knowledge base and QA chain
def initialize_knowledge_base():
    global vector_store, qa_chain

    if vector_store is not None:
        return  # Knowledge base already initialized

    # Check if the vector store already exists
    if os.path.exists(faiss_path):
        # Load the vector store if it exists
        print("Loading the existing medical knowledge base...")
        vector_store = FAISS.load_local(faiss_directory, embeddings, allow_dangerous_deserialization=True)
    else:
        # Initialize FileReader
        file_reader = FileReader()

        # Read all medical knowledge documents from the folder
        documents_texts = file_reader.read_files_in_folder(training_data_folder)

        # Clean and split the text into chunks
        split_documents = chunk_documents(documents_texts)

        # Build the knowledge base from the chunks
        print("Building the medical knowledge base...")

        # Batch processing to avoid exceeding API rate limits
        batch_size = 15  # Number of chunks to process in each batch
        for i in range(0, len(split_documents), batch_size):
            batch = split_documents[i:i + batch_size]
            try:
                if vector_store is None:
                    vector_store = FAISS.from_texts(batch, embeddings)
                else:
                    vector_store.add_texts(batch)
            except openai.error.RateLimitError as e:
                print("Rate limit exceeded. Retrying after delay...")
                time.sleep(10)  # Wait before retrying to avoid rate limit issues

        # Save the vector store to disk
        vector_store.save_local(faiss_directory)
        print("Medical knowledge base saved.")

    # Initialize the QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vector_store.as_retriever()
    )

# Function to add uploaded document temporarily to the vector store
def add_uploaded_document_to_store(document_text):
    global vector_store
    document_chunks = chunk_documents([document_text])  # Split the document into chunks
    vector_store.add_texts(document_chunks)  # Add chunks to the existing vector store

# Function to handle general queries
def answer_medical_query(query):
    if qa_chain is None:
        raise ValueError("Knowledge base is not initialized.")
    response = qa_chain.run(query)
    return response


# Only build the knowledge base if this script is executed directly
if __name__ == "__main__":
    print("Initializing knowledge base...")
    initialize_knowledge_base()
    print("Knowledge base initialized. Ready to be used by the web server.")