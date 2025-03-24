from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
import chromadb
import os
from dotenv import load_dotenv
import nltk
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Load environment variables. Assumes that project contains .env file with API keys
load_dotenv()

CHROMA_PATH = "chroma"
DATA_PATH = "data/books"
COLLECTION_NAME = "documents"

def main():
    generate_data_store()

def generate_data_store():
    documents = load_documents()
    chunks = split_text(documents)
    save_to_chroma(chunks)

def load_documents():
    # Load documents from the specified directory.
    loader = DirectoryLoader(DATA_PATH, glob="*.md")
    documents = loader.load()
    return documents

def split_text(documents: list[Document]):
    # Split the documents into smaller chunks for processing.
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=300,
        chunk_overlap=100,
        length_function=len,
        add_start_index=True,
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Split {len(documents)} documents into {len(chunks)} chunks.")
    return chunks

def save_to_chroma(chunks: list[Document]):
    # Initialize Chroma client
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(COLLECTION_NAME)
    
    # Load sentence transformer model
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    
    # Generate embeddings and add them to Chroma
    for i, doc in enumerate(chunks):
        embedding = model.encode(doc.page_content).tolist()
        collection.add(
            ids=[str(i)],  # Unique ID for each document
            embeddings=[embedding],
            metadatas=[doc.metadata],
            documents=[doc.page_content]
        )
    
    print(f"Saved {len(chunks)} chunks to ChromaDB at {CHROMA_PATH}.")

if __name__ == "__main__":
    main()
