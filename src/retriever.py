import os
import chromadb
from google import genai
from dotenv import load_dotenv

load_dotenv()
client_ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
client = chromadb.PersistentClient(path="chroma_db")


def embed_query(query: str) -> list[float]:
    """Convert the user's question into a vector — same way we embedded the chunks."""
    result = client_ai.models.embed_content(
        model="gemini-embedding-001",
        contents=query,
    )
    return result.embeddings[0].values


def retrieve(query: str, ticker: str, top_k: int = 5) -> list[dict]:
    """
    Find the top_k most relevant chunks for a given query.
    Returns a list of dicts with 'text' and 'chunk_index'.
    """
    query_vector = embed_query(query)

    collection = client.get_or_create_collection(name=ticker.lower())

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k,
    )

    chunks = []
    for i, doc in enumerate(results["documents"][0]):
        chunks.append({
            "text": doc,
            "chunk_index": results["metadatas"][0][i]["chunk_index"],
        })

    return chunks


if __name__ == "__main__":
    # Test it with a sample question
    query = "What are Apple's main risk factors?"
    print(f"Query: {query}\n")

    chunks = retrieve(query, "AAPL", top_k=3)

    for i, chunk in enumerate(chunks):
        print(f"--- Chunk {chunk['chunk_index']} ---")
        print(chunk["text"][:300])  # print first 300 chars of each chunk
        print()