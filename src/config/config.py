# config/config.py
from pathlib import Path
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Project structure
ROOT_DIR = Path(__file__).parent.parent.parent
DATA_DIR = ROOT_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EMBEDDINGS_DIR = PROCESSED_DATA_DIR / "embeddings"

# Create directories if missing
for dir_path in [RAW_DATA_DIR, PROCESSED_DATA_DIR, EMBEDDINGS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Data processing settings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 100
SQLITE_BATCH_SIZE = 1000

# Actual columns in your dataset
REQUIRED_COLUMNS = {
    "type",
    "bedrooms",
    "bathrooms",
    "price",
    "listing_update_date",
    "property_type_full_description",
    "flood_risk",
    "is_new_home",
    "laua",
    "crime_score_weight",
    "address"
}

# Correct data type mapping
DTYPE_MAP = {
    "type": "string",
    "bedrooms": "int64",
    "bathrooms": "int64",
    "price": "float64",
    "listing_update_date": "string",
    "property_type_full_description": "string",
    "flood_risk": "string",
    "is_new_home": "bool",
    "laua": "string",
    "crime_score_weight": "float64",
    "address": "string",
}

#  Database settings
SQLITE_DB_PATH = PROCESSED_DATA_DIR / "properties.db"
VECTOR_DB_PATH = PROCESSED_DATA_DIR / "vector_store"
SQLITE_TIMEOUT = 30

#  Field categories for query logic
NUMERIC_FIELDS = [
    "price",
    "bedrooms",
    "bathrooms",
    "crime_score_weight",
]

CATEGORICAL_FIELDS = [
    "type",
    "flood_risk",
    "property_type_full_description",
    "laua",
]

BOOLEAN_FIELDS = [
    "is_new_home",
]

TEXT_FIELDS = [
    "address",
]

# Columns to show in Streamlit UI
DISPLAY_COLUMNS = [
    "address",
    "type",
    "bedrooms",
    "bathrooms",
    "price",
    "flood_risk",
    "crime_score_weight",
    "is_new_home",
    "laua",
    "property_type_full_description",
    "listing_update_date",
]

# Text summary template for LLM / retrieval context
DB_FIELDS_DESCRIPTION_USER_INTEREST = f"""The database has property records with fields:
- Type: {', '.join(['type', 'property_type_full_description'])}
- Location: {', '.join(['address', 'laua'])}
- Details: {', '.join(['bedrooms', 'bathrooms', 'flood_risk', 'is_new_home'])}
- Price and Safety: {', '.join(['price', 'crime_score_weight'])}
- Date: listing_update_date
"""
