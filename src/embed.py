import os
import re
import chromadb
from google import genai
from dotenv import load_dotenv
import time

load_dotenv()
client_ai = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Initialize ChromaDB — stores everything locally in a chroma_db/ folder
client = chromadb.PersistentClient(path="chroma_db")

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """
    Split text into overlapping chunks of ~chunk_size words.
    Overlap means consecutive chunks share 50 words — so we don't
    lose context at the boundaries.
    """
    text = re.sub(r'\s+', ' ', text).strip()
    words = text.split()

    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def embed_texts(texts: list[str]) -> list[list[float]]:
    embeddings = []
    for i, text in enumerate(texts):
        print(f"  Embedding chunk {i+1}/{len(texts)}...", end="\r")
        while True:
            try:
                result = client_ai.models.embed_content(
                    model="gemini-embedding-001",
                    contents=text,
                )
                embeddings.append(result.embeddings[0].values)
                time.sleep(1)  # wait 1 second between calls to avoid rate limit
                break
            except Exception as e:
                if "429" in str(e):
                    print(f"\n  Rate limited, waiting 15 seconds...")
                    time.sleep(15)  # if we still get rate limited, wait longer
                else:
                    raise e
    print()
    return embeddings


def ingest_file(filepath: str, ticker: str):
    """
    Main function: read a saved 10-K text file, chunk it, embed it,
    and store everything in ChromaDB under a collection named after the ticker.
    """
    print(f"[1/3] Reading {filepath}...")
    with open(filepath, "r", encoding="utf-8") as f:
        text = f.read()
    print(f"  Read {len(text):,} characters")

    print(f"[2/3] Chunking text...")
    chunks = chunk_text(text)
    print(f"  Created {len(chunks)} chunks")

    ids = [f"{ticker}_chunk_{i}" for i in range(len(chunks))]

    print(f"[3/3] Embedding chunks and storing in ChromaDB...")
    embeddings = embed_texts(chunks)

    collection = client.get_or_create_collection(name=ticker.lower())

    collection.add(
        ids=ids,
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"ticker": ticker, "chunk_index": i} for i in range(len(chunks))]
    )

    print(f"Done! Stored {len(chunks)} chunks for {ticker} in ChromaDB")


if __name__ == "__main__":
    data_dir = "data"
    files = [f for f in os.listdir(data_dir) if f.startswith("AAPL")]

    if not files:
        print("No AAPL file found — run ingest.py first")
    else:
        filepath = os.path.join(data_dir, files[0])
        ingest_file(filepath, "AAPL")