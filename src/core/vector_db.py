import os
import uuid

import chromadb
import dotenv
from chromadb.utils import embedding_functions

from src.core.logger import logger

dotenv.load_dotenv()


# 1. Setup ChromaDB (Local Storage)
# Folder 'news_db' akan otomatis dibuat
client = chromadb.CloudClient(
    api_key=os.getenv("CHROMA_DB_API_KEY"),
    tenant=os.getenv("CHROMA_DB_TENANT"),
    database=os.getenv("CHROMA_DB_DATABASE", "devai"),
)

# 2. Setup Embedding Function
# Kita pakai model default yang ringan dan gratis
emb_fn = embedding_functions.DefaultEmbeddingFunction()

# 3. Get or Create Collection
news_collection = client.get_or_create_collection(
    name="market_narratives", embedding_function=emb_fn
)


def save_news_vector(symbol, summary, sentiment_score, raw_text):
    """
    Menyimpan analisis berita ke Vector DB.
    """
    try:
        # ID Unik
        news_id = f"{symbol}_{str(uuid.uuid4())[:8]}"

        # Metadata (Data pendukung yang bisa difilter)
        meta = {
            "symbol": symbol,
            "sentiment": float(sentiment_score),
            "raw_text": raw_text[:200],  # Simpan potongan teks asli
        }

        # Simpan ke Chroma
        news_collection.add(
            documents=[summary],  # Ini yang akan di-vektor-kan (Isi analisis AI)
            metadatas=[meta],
            ids=[news_id],
        )
        logger.info(f"💾 Vector Saved: {summary[:30]}...")

    except Exception as e:
        logger.error(f"ChromaDB Save Error: {e}")


def recall_similar_events(query_text, n_results=3):
    """
    Mencari kejadian serupa di masa lalu berdasarkan kemiripan semantik.
    """
    try:
        results = news_collection.query(query_texts=[query_text], n_results=n_results)

        # Format hasil agar mudah dibaca
        history_context = []
        if results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0]

            for doc, meta in zip(docs, metas):
                history_context.append(
                    {
                        "summary": doc,
                        "symbol": meta["symbol"],
                        "past_sentiment": meta["sentiment"],
                    }
                )

        return history_context

    except Exception as e:
        logger.error(f"ChromaDB Query Error: {e}")
        return []
