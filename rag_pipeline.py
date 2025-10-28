# rag_pipeline.py
import logging
from typing import Tuple
import pandas as pd
from src.query.parser import QueryParser
from src.query.executor import QueryExecutor
from src.query.response_generator import ResponseGenerator

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger(__name__)


class PropertyRAG:
    """
    Main RAG pipeline for the Property Dataset
    Works fully offline with SQLite + FAISS
    """

    def __init__(self):
        logger.info("Initializing PropertyRAG system...")
        self.parser = QueryParser()
        self.executor = QueryExecutor()
        self.response_generator = ResponseGenerator()
        logger.info("PropertyRAG initialized successfully.\n")

    def process_query(self, query: str) -> Tuple[str, pd.DataFrame, pd.DataFrame]:
        """
        Parse → Execute → Format results.
        Returns:
            narrative (str): Response text summary
            preview_df (pd.DataFrame): Preview (top 10)
            full_df (pd.DataFrame): All matching records
        """
        try:
            # 1️ Get known locations (for better address extraction)
            try:
                known_locations = self.executor.get_known_locations()
            except Exception:
                known_locations = []

            # 2️ Parse query (pass known locations)
            parsed_query = self.parser.parse_query(query, known_locations=known_locations)
            parsed_query.original_text = query
            logger.info(f"Query Type: {parsed_query.query_type}")
            logger.info(f"Parsed Query Details: {parsed_query}")

            # 3️ Execute
            results = self.executor.execute_query(parsed_query)
            logger.info("Query execution completed successfully")

            # 4️ Format (ResponseGenerator now returns narrative, preview_df, full_df)
            narrative, preview_df, full_df = self.response_generator.format_response(
                query=query,
                parsed_query=parsed_query,
                query_results=results
            )

            # 5️ Logging
            if isinstance(full_df, pd.DataFrame) and not full_df.empty:
                logger.info(f"Retrieved {len(full_df)} total records (showing {len(preview_df)} preview).")
            else:
                logger.info("No results found.")

            return narrative, preview_df, full_df

        except Exception as e:
            logger.exception(f"Error processing query: {e}")
            # Always return three values to prevent FastAPI unpacking errors
            return f"An error occurred while processing your query: {e}", pd.DataFrame(), pd.DataFrame()


if __name__ == "__main__":
    rag = PropertyRAG()
    query = "Show me 4 bedroom houses"
    text, preview, full = rag.process_query(query)
    print("\nResponse:", text)
    print("\nPreview (top 10):")
    print(preview.head(10))
    print("\nFull (sample):")
    print(full.head(10))
