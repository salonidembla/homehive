# src/query/response_generator.py
import pandas as pd
import logging
from typing import Dict, Any, Tuple
from ..query.schema import QueryType

logger = logging.getLogger(__name__)


class ResponseGenerator:
    def __init__(self):
        logger.info("Using enhanced local ResponseGenerator (offline).")

    def format_response(self, query: str, parsed_query, query_results: Dict[str, Any]) -> Tuple[str, pd.DataFrame, pd.DataFrame]:
        """
        Generates a text narrative and both preview + full DataFrames.
        Returns:
            narrative (str)
            preview_df (pd.DataFrame)
            full_df (pd.DataFrame)
        """

        # 1️ Aggregation Queries
        if parsed_query.query_type == QueryType.AGGREGATION:
            # 🔹 Which area has the most crime
            if "best_area" in query_results:
                area = query_results["best_area"]
                val = round(query_results.get("aggregation_result", 0), 2)
                df = pd.DataFrame([{"Area": area, "Avg Crime Score": val}])
                return (
                    f"The area with the most crime is **{area}** (avg score {val}).",
                    df.head(10),
                    df
                )

            # 🔹 Compare prices
            if query_results.get("aggregation_function") == "COMPARE":
                c = query_results["comparison"]
                df = pd.DataFrame([c])
                text = (
                    f"The **average price** of studio homes is **${c['studio_avg_price']}**, "
                    f"while 2-bedroom homes average **${c['two_bed_avg_price']}**. "
                    f"The difference is about **${c['difference']}**."
                )
                return text, df.head(10), df

            # 🔹 Normal aggregations
            result = query_results.get("aggregation_result")
            field = query_results.get("aggregation_field", "value")
            func = query_results.get("aggregation_function", "AVG")
            total = query_results.get("total_records", 0)

            if result is None:
                empty_df = pd.DataFrame()
                return f"No data available to calculate {func.lower()} of {field}.", empty_df, empty_df

            df = pd.DataFrame([{
                "Metric": f"{func}_{field}",
                "Value": round(result, 2),
                "Records Used": total
            }])

            text = (
                f"The **{func.lower()} {field}** for your query is "
                f"**{round(result, 2)}**, based on {total} records."
            )
            return text, df.head(10), df

        # 2️ Retrieval / Filter Queries
        results = query_results.get("structured_results", [])
        if not results:
            empty_df = pd.DataFrame()
            return "No matching properties found for your query.", empty_df, empty_df

        df = pd.DataFrame(results)
        display_cols = [c for c in [
            "address", "price", "bedrooms", "bathrooms", "type",
            "property_type_full_description", "flood_risk", "crime_score_weight"
        ] if c in df.columns]

        df_display = df[display_cols] if display_cols else df
        top_n = min(10, len(df_display))

        text = (
            f"I found **{len(df_display)} properties** matching your query: "
            f"'{query.strip()}'. Here are the top {top_n}:"
        )

        return text, df_display.head(top_n), df_display
