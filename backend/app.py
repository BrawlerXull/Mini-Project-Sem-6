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
from ocr import extract_text_from_pdf  # Custom OCR function
from levenshtein_accuracy import calculate_levenshtein_accuracy


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
    full_text = extract_text_from_pdf(file_path, "K83693271888957")
    # document = Document(page_content=text)
    document = Document(page_content=full_text)
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
        
        # Retrieve all document IDs in the collection
        existing_docs = collection.get()
        existing_ids = [doc_id for doc_id in existing_docs['ids']]
        
        if existing_ids:
            # Delete all existing documents
            collection.delete(ids=existing_ids)
            print(f"Deleted {len(existing_ids)} documents from the collection.")

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

import os
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

def convert_to_pdf(input_path):
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_dir = os.path.join(os.getcwd(), "uploads", "converted")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{base_name}.pdf")

    ext = os.path.splitext(input_path)[1].lower()

    if ext in ['.png', '.jpg', '.jpeg']:
        image = Image.open(input_path).convert("RGB")
        image.save(output_path)
        return output_path

    elif ext == '.txt':
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas

        with open(input_path, 'r', encoding='utf-8') as f:
            text = f.read()

        c = canvas.Canvas(output_path, pagesize=letter)
        width, height = letter
        y = height - 50
        for line in text.split('\n'):
            c.drawString(40, y, line)
            y -= 15
            if y < 50:
                c.showPage()
                y = height - 50
        c.save()
        return output_path

    elif ext == '.docx':
        from docx2pdf import convert
        convert(input_path, output_path)
        return output_path

    elif ext == '.pdf':
        return input_path

    else:
        raise Exception(f"Unsupported file type: {ext}")




import os
from flask import request, jsonify
from werkzeug.utils import secure_filename

@app.route('/generate_data_store', methods=['POST'])
def generate_data_store():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty file uploaded"}), 400

        filename = secure_filename(file.filename)
        temp_path = os.path.join("/tmp", filename)
        file.save(temp_path)

        print("File name:", filename)

        # Convert to PDF if not already a PDF
        if not filename.lower().endswith('.pdf'):
            print(temp_path)
            pdf_path = convert_to_pdf(temp_path)
            print("Converted PDF path:", pdf_path)
        else:
            pdf_path = temp_path

        # Process the (PDF) file
        documents = load_documents(pdf_path)
        print("oh yeah")
        chunks = split_text(documents)
        print("oh yeah 2")
        save_to_chroma(chunks)

        return jsonify({"message": "Data store generated and embeddings saved to ChromaDB!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



import ollama
@app.route('/query_data', methods=['POST'])
def query_data():
    try:
        data = request.get_json()
        query_text = data.get("query_text", None)
        model = data.get("model", "groq") 
        
        if not query_text:
            return jsonify({"error": "No query text provided"}), 400

        results = retrieve_relevant_chunks(query_text)
        
        if not results:
            return jsonify({"error": "No relevant results found"}), 404

        if model == "llama":
            refined_response = generate_llama_response_offline(results)
        else:
            refined_response = generate_llama_response_groq(results)

        return jsonify({"response": refined_response}), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

import ollama
import json

import requests
import json

GROQ_API_KEY = "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"
GROQ_MODEL = "llama3-70b-8192"  # or "mixtral-8x7b-32768"

def generate_llama_response_groq(text):
    """Calls Groq API to refine response."""
    if not isinstance(text, str):
        text = json.dumps(text, indent=2)

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": text}],
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    result = response.json()
    return result["choices"][0]["message"]["content"]


def generate_llama_response_offline(text):
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


import json
@app.route('/summarize', methods=['POST'])
def summarize():
    try:
        # Parse form data for file and model (if provided)
        data = request.form
        file = request.files.get("file", None)
        model = data.get("model", "groq")

        if not file:
            return jsonify({"error": "No file uploaded"}), 400
        
        if file.filename == "":
            return jsonify({"error": "Empty file uploaded"}), 400

        # Save the uploaded file to a temporary location
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        # Load PDF and extract text
        documents = load_pdf(file_path)
        full_text = "\n".join([doc.page_content for doc in documents])

        # Create a summary prompt with markdown formatting
        summary_prompt = f"Summarize the following text as a markdown bullet list or paragraph when appropriate:\n\n{full_text}"

        # Generate summary based on model selection
        if model == "llama":
            summary = generate_llama_response_offline(summary_prompt)
        else:
            summary = generate_llama_response_groq(summary_prompt)

        return jsonify({
            "summary": summary
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

import json
@app.route('/expand', methods=['POST'])
def expand():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty file uploaded"}), 400

        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        # Get model from form data
        model = request.form.get("model", "groq")

        documents = load_pdf(file_path)
        full_text = "\n".join([doc.page_content for doc in documents])

        # Add markdown formatting hint
        summary_prompt = f"Expand the following text on the main topics mentioned in the text as a markdown bullet list or paragraph when appropriate:\n\n{full_text}"
        summary = generate_llama_response_groq(summary_prompt)

        return jsonify({
            "summary": summary
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



superposition_text = """6.4) Superposition of Waves
Principle:

When two or more waves, travelling through a medium, pass through a common point, each wave produces its own displacement at that point, independent of the presence of other waves. The resultant displacement at that point is equal to the vector sum of displacements due to the individual wave at that point.

There is no change in shape & nature of individual waves due to superposition of waves.

This principle is applicable to all types of waves like sound waves, light waves, waves on string etc."""


wmax = """Technologies using TDD:

WiMAX (Worldwide Interoperability for Microwave Access):
→ WiMAX uses the same frequency band for both uplink and downlink communication. Time slots are allocated dynamically for uplink or downlink depending on network traffic.

5G NTR-TDD (New Radio Time Division Duplex):
→ TDD in 5G is used to enable high-speed data transmission, especially in mid-band and mmWave spectrum, where spectrum is limited but bandwidth demand is high.

Q.5: Is TDD going to be used in 5G? Discuss.

→ Yes, TDD is being used in 5G and is playing a significant role especially in high frequency bands.
→ Flexibility: Allows dynamic allocation of resources between uplink and downlink traffic. This aims to support various applications with diverse traffic patterns.
→ Efficiency in higher frequency: In higher frequency bands like mmWave, TDD is more efficient due to shorter wavelengths and higher propagation losses.
→ Support Diverse Cases: TDD is well suited for applications that require asymmetric traffic, such as:
i. Enhanced Mobile Broadband
ii. Ultra-reliable low latency
iii. Massive machine type communication"""



import json

@app.route('/summarize_ocr', methods=['POST'])
def summarize_ocr():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["file"]
        
        if file.filename == "":
            return jsonify({"error": "Empty file uploaded"}), 400

        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        full_text = extract_text_from_pdf(file_path, "K83693271888957")

        accuracy = calculate_levenshtein_accuracy(full_text, wmax)
        print(f"Levenshtein accuracy: {accuracy:.2f}%")

        # Get model from form data
        model = request.form.get("model", "groq")
        print("Model selected:", model)

        summary_prompt = f"Summarize the following text as a markdown bullet list or paragraph when appropriate:\n\n{full_text}"

        # Select model for summary generation
        if model == "llama":
            summary = generate_llama_response_offline(summary_prompt)
        else:
            summary = generate_llama_response_groq(summary_prompt)

        return jsonify({
            "summary": summary,
            "accuracy": accuracy
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    
import json
from flask import request, jsonify
import os

@app.route('/expand_ocr', methods=['POST'])
def expand_ocr():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty file uploaded"}), 400

        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        full_text = extract_text_from_pdf(file_path, "K83693271888957")

        accuracy = calculate_levenshtein_accuracy(full_text, "Expected text for accuracy check")
        print(f"Levenshtein accuracy: {accuracy:.2f}%")

        # Get model and character count from form data
        model = request.form.get("model", "groq")
        desired_character_count = int(request.form.get("desired_character_count", 1000))

        expansion_prompt = f"""
            You are an expert researcher and explainer. Expand on the key topics mentioned in the following text by adding relevant background, causes, effects, real-world examples, and related concepts. Present your expansion as a well-structured Markdown output — use bullet points for lists, and paragraphs when necessary. Maintain clarity and avoid repetition. The expanded response should be approximately {desired_character_count} characters long.

            Text to expand:
            \"\"\"
            {full_text}
            \"\"\"
        """

        # Use selected model
        if model == "llama":
            summary = generate_llama_response_offline(expansion_prompt)
        else:
            summary = generate_llama_response_groq(expansion_prompt)

        # Trim or pad the output as needed
        if len(summary) > desired_character_count:
            summary = summary[:desired_character_count]
        elif len(summary) < desired_character_count:
            summary += " " * (desired_character_count - len(summary))

        return jsonify({
            "summary": summary,
            "character_count": len(summary)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

import json
import re

@app.route('/generate_questions', methods=['POST'])
def generate_questions():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400
        
        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "Empty file uploaded"}), 400

        # Save the file temporarily
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        # Extract text from the PDF
        documents = load_pdf(file_path)
        full_text = "\n".join([doc.page_content for doc in documents])

        # Generate key questions with answers
        questions_prompt = f"""
        You are an assistant that generates questions based on the provided text.
        Read the following text and generate exactly 5 key questions along with their answers in a JSON array format.
        The JSON array should contain question-answer pairs like this:
        [
            {{"question": "What is the main idea?", "answer": "The main idea is ..."}},
            {{"question": "How does X work?", "answer": "X works by ..."}},
            {{"question": "What are the key points?", "answer": "The key points are ..."}},
            {{"question": "Why is Y important?", "answer": "Y is important because ..."}},
            {{"question": "What is the conclusion?", "answer": "The conclusion is ..."}}
        ]
        Only return the JSON array, and do not include any additional text or summaries.
        Text:
        {full_text}
        """

        questions = generate_llama_response_groq(questions_prompt)

        # Clean up the response: remove extra spaces, newlines, and unwanted characters.
        questions = questions.strip()

        print("Questions after LLAMA Response:", repr(questions))

        # Ensure that we only clean up unwanted characters, not valid JSON format
        # Remove any leading or trailing whitespaces or newlines that might interfere with JSON parsing
        questions_cleaned = questions.strip()

        # Now attempt to parse the cleaned-up JSON response
        try:
            # Attempt to parse the cleaned JSON
            questions_json = json.loads(questions_cleaned)  # Attempt to parse as JSON
        except json.JSONDecodeError:
            # If JSON decode fails, log and return an empty list
            print(f"JSON decoding failed: {questions_cleaned}")
            questions_json = []  # Return an empty list in case of failure

        print("Questions JSON:", questions_json)

        return jsonify({
            "questions": questions_json  # Return the JSON formatted questions & answers
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

from flask import request, jsonify
import json

@app.route('/generate_questions_from_text', methods=['POST'])
def generate_questions_from_text():
    try:
        data = request.get_json()

        if not data or "text" not in data:
            return jsonify({"error": "Missing 'text' in request body"}), 400

        full_text = data["text"]

        # Prompt to generate key questions with answers
        questions_prompt = f"""
        You are an assistant that generates questions based on the provided text.
        Read the following text and generate exactly 5 key questions along with their answers in a JSON array format.
        The JSON array should contain question-answer pairs like this:
        [
            {{"question": "What is the main idea?", "answer": "The main idea is ..."}},
            {{"question": "How does X work?", "answer": "X works by ..."}},
            {{"question": "What are the key points?", "answer": "The key points are ..."}},
            {{"question": "Why is Y important?", "answer": "Y is important because ..."}},
            {{"question": "What is the conclusion?", "answer": "The conclusion is ..."}}
        ]
        Only return the JSON array, and do not include any additional text or summaries.
        Text:
        {full_text}
        """

        questions = generate_llama_response_groq(questions_prompt).strip()

        try:
            questions_json = json.loads(questions)
        except json.JSONDecodeError:
            print(f"❌ JSON decoding failed: {questions}")
            questions_json = []

        return jsonify({"questions": questions_json}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500










if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
