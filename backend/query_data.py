import argparse
import chromadb
from sentence_transformers import SentenceTransformer

CHROMA_PATH = "chroma"
COLLECTION_NAME = "documents"
K = 3  # Number of top results to retrieve
RELEVANCE_THRESHOLD = 0.7

PROMPT_TEMPLATE = """
Answer the question based only on the following context:

{context}

---

Answer the question based on the above context: {question}
"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("query_text", type=str, help="The query text.")
    args = parser.parse_args()
    query_text = args.query_text
    
    retrieve_relevant_chunks(query_text)

def retrieve_relevant_chunks(query_text: str):
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
        return
    
    context_texts = results["documents"][0]
    metadata = results["metadatas"][0]
    
    context = "\n\n---\n\n".join(context_texts)
    prompt = PROMPT_TEMPLATE.format(context=context, question=query_text)
    print("Generated Prompt:\n", prompt)
    
    # Display sources
    sources = [meta.get("source", "Unknown") for meta in metadata]
    print(f"Sources: {sources}")

if __name__ == "__main__":
    main()