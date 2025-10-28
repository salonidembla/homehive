# src/query/executor.py
from typing import Dict, Any, List, Optional
import logging
from sqlalchemy import create_engine, text
import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
from .schema import QueryStructure, QueryType
from ..config.config import SQLITE_DB_PATH

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryExecutor:
    """
    Executes structured property queries locally using SQLite + FAISS.
    Handles:
    - SQL filters
    - Aggregations (AVG, COUNT, MAX, MIN, SUM)
    - Semantic fallback search
    """

    def __init__(self):
        self.engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # Load FAISS index + metadata
        self.index = faiss.read_index("faiss_index.bin")
        with open("metadata.pkl", "rb") as f:
            self.metadata = pickle.load(f)

        with self.engine.connect() as conn:
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
            self.table_name = tables[0][0] if tables else "properties"

        self._known_locations: Optional[List[str]] = None
        logger.info(f"Local FAISS index and table '{self.table_name}' loaded successfully.")

    # ------------------------------------------------------------------
    def get_known_locations(self) -> List[str]:
        """Extract all known property addresses (for parser location detection)."""
        if self._known_locations is not None:
            return self._known_locations

        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT DISTINCT address FROM {self.table_name} WHERE address IS NOT NULL")
            ).fetchall()
            self._known_locations = [r[0] for r in result if r[0]]
        return self._known_locations

    # ------------------------------------------------------------------
    def _build_sql_query(self, parsed_query: QueryStructure):
        """
        Build SELECT * FROM <table> WHERE ... and params.
        For COUNT queries we will reuse and transform this SQL to SELECT COUNT(*).
        """
        query = f"SELECT * FROM {self.table_name}"
        conditions = []
        params: Dict[str, Any] = {}

        def add_numeric(cond, col):
            if not cond:
                return
            op_map = {"eq": "=", "gte": ">=", "gt": ">", "lte": "<=", "lt": "<"}
            if cond.operator == "between":
                conditions.append(f"{col} BETWEEN :{col}_min AND :{col}_max")
                params[f"{col}_min"] = cond.value
                params[f"{col}_max"] = cond.value_end
            elif cond.operator in op_map:
                conditions.append(f"{col} {op_map[cond.operator]} :{col}")
                params[col] = cond.value

        add_numeric(parsed_query.bedrooms, "bedrooms")
        add_numeric(parsed_query.bathrooms, "bathrooms")
        add_numeric(parsed_query.price, "price")
        add_numeric(parsed_query.crime_score_weight, "crime_score_weight")

        # Use LIKE for flood risk to be robust to case/wording
        if parsed_query.flood_risk:
            if parsed_query.flood_risk.lower() == "low":
                conditions.append("LOWER(flood_risk) LIKE '%low%'")
            elif parsed_query.flood_risk.lower() == "medium":
                conditions.append("LOWER(flood_risk) LIKE '%medium%'")
            elif parsed_query.flood_risk.lower() == "high":
                conditions.append("LOWER(flood_risk) LIKE '%high%'")
        if parsed_query.is_new_home:
            conditions.append("is_new_home=1")
        if parsed_query.laua:
            conditions.append("LOWER(laua)=:laua")
            params["laua"] = parsed_query.laua.lower()
        if parsed_query.property_type_full_description:
            conditions.append("(LOWER(property_type_full_description) LIKE :ptype OR LOWER(type) LIKE :ptype)")
            params["ptype"] = f"%{parsed_query.property_type_full_description.lower()}%"
        if parsed_query.address:
            conditions.append("LOWER(address) LIKE :address")
            params["address"] = f"%{parsed_query.address.lower()}%"

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        return query, params

    # ------------------------------------------------------------------
    def _perform_semantic_search(self, query_text: str, top_k: int = 20):
        """Perform FAISS vector similarity search."""
        vec = self.model.encode([query_text], convert_to_numpy=True).astype("float32")
        dist, idx = self.index.search(vec, top_k)

        results = []
        for i, d in zip(idx[0], dist[0]):
            if i < 0:
                continue
            record = self.metadata[i].copy()
            record["similarity_score"] = float(d)
            results.append(record)
        logger.info(f"🔎 Semantic search returned {len(results)} results.")
        return results

    # ------------------------------------------------------------------
    # src/query/executor.py (inside class QueryExecutor)
    def execute_query(self, parsed_query: QueryStructure) -> Dict[str, Any]:
        try:
            text_query = parsed_query.original_text.lower()

            # Special case: Most crime
            if "most crime" in text_query or "highest crime" in text_query:
                q = f"""
                    SELECT laua, AVG(crime_score_weight) AS avg_crime
                    FROM {self.table_name}
                    WHERE laua IS NOT NULL
                    GROUP BY laua
                    ORDER BY avg_crime DESC
                    LIMIT 1
                """
                with self.engine.connect() as conn:
                    result = conn.execute(text(q)).fetchone()
                    if result:
                        return {
                            "query_type": QueryType.AGGREGATION,
                            "aggregation_function": "MAX",
                            "aggregation_field": "crime_score_weight",
                            "aggregation_result": result[1],
                            "best_area": result[0],
                            "structured_results": [],  # ensure consistent key
                            "semantic_search_performed": False,
                        }

            # Special: Compare prices
            if "compare" in text_query and "price" in text_query:
                with self.engine.connect() as conn:
                    s1 = conn.execute(text(f"SELECT AVG(price) FROM {self.table_name} WHERE LOWER(property_type_full_description) LIKE '%studio%'")).fetchone()[0] or 0
                    s2 = conn.execute(text(f"SELECT AVG(price) FROM {self.table_name} WHERE LOWER(property_type_full_description) LIKE '%2 bed%' OR bedrooms=2")).fetchone()[0] or 0
                return {
                    "query_type": QueryType.AGGREGATION,
                    "aggregation_function": "COMPARE",
                    "comparison": {
                        "studio_avg_price": round(s1, 2),
                        "two_bed_avg_price": round(s2, 2),
                        "difference": round(abs(s1 - s2), 2)
                    },
                    "structured_results": [],
                    "semantic_search_performed": False
                }

            # Normal Aggregation
            if parsed_query.query_type == QueryType.AGGREGATION:
                sql_query, params = self._build_sql_query(parsed_query)
                with self.engine.connect() as conn:
                    res = conn.execute(text(sql_query), params)
                    cols = res.keys()
                    rows = [dict(zip(cols, r)) for r in res.fetchall()]

                if not rows:
                    return {"aggregation_result": None, "structured_results": []}

                field = parsed_query.aggregation_field or "price"
                vals = [float(r.get(field, 0)) for r in rows if r.get(field) is not None]
                func = parsed_query.aggregation_function or "AVG"
                if func == "AVG":
                    result = sum(vals) / len(vals)
                elif func == "MAX":
                    result = max(vals)
                elif func == "MIN":
                    result = min(vals)
                elif func == "SUM":
                    result = sum(vals)
                elif func == "COUNT":
                    result = len(vals)
                else:
                    result = None

                return {
                    "query_type": QueryType.AGGREGATION,
                    "aggregation_function": func,
                    "aggregation_field": field,
                    "aggregation_result": result,
                    "total_records": len(vals),
                    "structured_results": rows,  # full dataset here
                    "semantic_search_performed": False
                }

            # Normal Retrieval
            sql_query, params = self._build_sql_query(parsed_query)
            with self.engine.connect() as conn:
                res = conn.execute(text(sql_query), params)
                cols = res.keys()
                rows = [dict(zip(cols, r)) for r in res.fetchall()]

            if not rows:
                sem = self._perform_semantic_search(parsed_query.original_text)
                return {
                    "structured_results": sem,
                    "semantic_search_performed": True
                }

            return {
                "structured_results": rows,  # full result list (no truncation)
                "semantic_search_performed": False
            }

        except Exception as e:
            logger.error(f" Executor error: {e}")
            raise
