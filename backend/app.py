from flask import Flask, jsonify, request
from langchain.document_loaders import TextLoader  # Use TextLoader for markdown files
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from sentence_transformers import SentenceTransformer
import chromadb
import os
from dotenv import load_dotenv
import nltk
import fitz  # PyMuPDF for PDF extraction

# Load environment variables
load_dotenv()

# Initialize Flask app
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Allow all origins, modify for production security


# Constants
CHROMA_PATH = "chroma"
COLLECTION_NAME = "documents"
K = 3  # Number of top results to retrieve
RELEVANCE_THRESHOLD = 0.7

# Download NLTK data
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

# Define the prompt template
PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

def load_documents(file_path: str):
    # Check if the file is a markdown file or a PDF file and load accordingly
    if file_path.endswith('.md'):
        # Use TextLoader for Markdown files
        loader = TextLoader(file_path)
        documents = loader.load()
    elif file_path.endswith('.pdf'):
        # Use custom function to extract text from PDFs
        documents = load_pdf(file_path)
    else:
        raise ValueError("Unsupported file type. Only .md and .pdf are supported.")
    
    return documents

def load_pdf(file_path: str):
    # Use PyMuPDF (fitz) to extract text from PDF
    doc = fitz.open(file_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)  # Load each page
        text += page.get_text("text")  # Extract text from the page
    doc.close()
    
    # Wrap the extracted text into a Document object
    document = Document(page_content=text)
    return [document]  # Return as a list of documents

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
    try:
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
    
    except Exception as e:
        print(f"Error connecting to Chroma: {str(e)}")
        raise

@app.route('/generate_data_store', methods=['POST'])
def generate_data_store():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "Empty file uploaded"}), 400
        
        # Save the file temporarily
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        # Process the file
        documents = load_documents(file_path)
        chunks = split_text(documents)
        save_to_chroma(chunks)

        return jsonify({"message": "Data store generated and embeddings saved to ChromaDB!"}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500



import ollama

@app.route('/query_data', methods=['POST'])
def query_data():
    try:
        # Get query text from the request
        data = request.get_json()
        query_text = data.get("query_text", None)
        
        if not query_text:
            return jsonify({"error": "No query text provided"}), 400
        
        # Retrieve relevant chunks from RAG
        results = retrieve_relevant_chunks(query_text)
        
        if not results:
            return jsonify({"error": "No relevant results found"}), 404

        # Generate meaningful response using Llama 3.2 via Ollama
        refined_response = generate_llama_response(results)

        return jsonify({"response": refined_response}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import ollama
import json

def generate_llama_response(text):
    """Calls local Llama 3.2 model via Ollama to refine response."""
    # Ensure text is a string (convert dict/list to JSON if needed)
    if not isinstance(text, str):
        text = json.dumps(text, indent=2)  # Convert to formatted JSON string

    print("text",text)
    response = ollama.chat(model="llama3.2", messages=[{"role": "user", "content": text}])
    print("reponse",response)
    return response['message']['content']



def retrieve_relevant_chunks(query_text: str):
    try:
        # Initialize Chroma client and load the collection
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_collection(COLLECTION_NAME)
        
        # Load the sentence transformer model
        model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
        query_embedding = model.encode(query_text).tolist()
        
        # Perform similarity search
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=K
        )
        
        if not results["documents"] or len(results["documents"][0]) == 0:
            print("Unable to find matching results.")
            return None
        
        context_texts = results["documents"][0]
        metadata = results["metadatas"][0]
        
        context = "\n\n---\n\n".join(context_texts)
        prompt = PROMPT_TEMPLATE.format(context=context, question=query_text)
        
        # Display sources
        sources = [meta.get("source", "Unknown") for meta in metadata]
        
        return {
            "generated_prompt": prompt,
            "sources": sources
        }
    except Exception as e:
        print(f"Error retrieving relevant chunks: {str(e)}")
        return None

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
