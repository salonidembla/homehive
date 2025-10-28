#rag/embeddings.py
import faiss
import pickle
import numpy as np
import logging
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmbeddingManager:
    """
    Handles loading of FAISS index and performing similarity searches
    for retrieved property data.
    """

    def __init__(self, index_path="faiss_index.bin", metadata_path="metadata.pkl",
                 model_name="all-MiniLM-L6-v2"):
        self.index_path = index_path
        self.metadata_path = metadata_path
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

        logger.info("Loading FAISS index and metadata...")
        self.index = faiss.read_index(self.index_path)

        with open(self.metadata_path, "rb") as f:
            self.metadata = pickle.load(f)

        logger.info(f"Loaded FAISS index with {self.index.ntotal} entries.")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """
        Retrieve top-k most relevant properties for a user query.
        Returns list of metadata dicts with similarity scores.
        """
        logger.info(f"Searching for: {query}")
        query_embedding = self.model.encode([query])
        distances, indices = self.index.search(np.array(query_embedding, dtype=np.float32), top_k)

        results = []
        for i, score in zip(indices[0], distances[0]):
            if 0 <= i < len(self.metadata):
                record = self.metadata[i].copy()
                record["similarity_score"] = float(score)
                results.append(record)
        return results

    def get_relevant_context(self, query: str, top_k: int = 5) -> str:
        """
        Returns a formatted string of retrieved results to be used as context for LLM generation.
        """
        results = self.search(query, top_k)
        if not results:
            return "No relevant data found."

        context = ""
        for r in results:
            context += (
                f"Address: {r.get('address', 'N/A')} | "
                f"Price: {r.get('price', 'N/A')} | "
                f"Bedrooms: {r.get('bedrooms', 'N/A')} | "
                f"Bathrooms: {r.get('bathrooms', 'N/A')} | "
                f"Type: {r.get('type', 'N/A')} | "
                f"Listing date: {r.get('listing_update_date', 'N/A')} | "
                f"Description: {r.get('property_type_full_description', 'N/A')}\n"
            )
        return context
