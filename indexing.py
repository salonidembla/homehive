"""
indexing.py
-----------
This script initializes the HomeHive database and vector index.

It:
1. Loads and cleans the property dataset.
2. Stores it in an SQLite database.
3. Generates sentence embeddings for semantic retrieval using FAISS.
"""
# indexing.py
import logging
from pathlib import Path
import pandas as pd
import sqlite3
import faiss
import pickle
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_PATH = Path("data/raw/Dataset_Cleaned.csv")
DB_PATH = Path("data/processed/properties.db")

def create_sqlite_database(df: pd.DataFrame):
    """Create or replace SQLite table with property data."""
    logger.info("🏗️ Creating SQLite database...")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as conn:
        df.to_sql("properties", conn, if_exists="replace", index=False)

    logger.info(f" SQLite database created at {DB_PATH} with {len(df)} records.")

def create_faiss_index(df: pd.DataFrame, model_name="all-MiniLM-L6-v2"):
    """Create FAISS vector index from property data."""
    logger.info("Loading embedding model...")
    model = SentenceTransformer(model_name)

    # Build textual representation for embedding
    texts = df.apply(
        lambda row: f"Type: {row['type']}, "
                    f"Bedrooms: {row['bedrooms']}, "
                    f"Bathrooms: {row['bathrooms']}, "
                    f"Price: {row['price']}, "
                    f"Flood risk: {row['flood_risk']}, "
                    f"Crime score: {row['crime_score_weight']}, "
                    f"New home: {row['is_new_home']}, "
                    f"Location: {row['laua']}, "
                    f"Address: {row['address']}. "
                    f"Listing date: {row['listing_update_date']}",
        axis=1
    ).tolist()

    logger.info("⚙️ Generating embeddings (this might take a minute)...")
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)

    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)

    # Save FAISS index and metadata
    faiss.write_index(index, "faiss_index.bin")
    with open("metadata.pkl", "wb") as f:
        pickle.dump(df.to_dict(orient="records"), f)

    logger.info(f"✅ FAISS index saved with {index.ntotal} records.")

def init_databases():
    """Main setup pipeline."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f" CSV not found at {DATA_PATH}")

    logger.info(f"Loading dataset from {DATA_PATH}...")
    df = pd.read_csv(DATA_PATH)

    # Normalize columns
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Verify expected columns
    expected_cols = [
        "type", "bedrooms", "bathrooms", "price", "listing_update_date",
        "property_type_full_description", "flood_risk", "is_new_home",
        "laua", "crime_score_weight", "address"
    ]
    missing_cols = [c for c in expected_cols if c not in df.columns]
    if missing_cols:
        logger.warning(f"⚠️ Missing columns auto-filled: {missing_cols}")
        for c in missing_cols:
            df[c] = ""

    # Clean types
    df["price"] = pd.to_numeric(df["price"], errors="coerce").fillna(0)
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce").fillna(0)
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce").fillna(0)
    df["crime_score_weight"] = pd.to_numeric(df["crime_score_weight"], errors="coerce").fillna(0)
    df["is_new_home"] = df["is_new_home"].astype(str).str.lower().isin(["true", "1", "yes"])

    logger.info(f"Cleaned {len(df)} records, ready to index.")
    create_sqlite_database(df)
    create_faiss_index(df)
    logger.info("All databases created successfully!")

if __name__ == "__main__":
    init_databases()
