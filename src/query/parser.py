# src/query/parser.py
import logging
import re
from typing import List, Optional
from ..query.schema import QueryType, QueryStructure, NumericCondition

logger = logging.getLogger(__name__)


class QueryParser:
    """
    Offline Rule-based QueryParser
    Converts natural-language questions into structured QueryStructure.
    """

    def __init__(self):
        logger.info("Using final enhanced QueryParser (offline).")

    NUM_WORDS = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10
    }

    def _word_to_num(self, w: str) -> Optional[int]:
        return self.NUM_WORDS.get(w.lower())

    # ------------------ BEDROOMS ------------------
    def _extract_bedrooms(self, q: str) -> Optional[NumericCondition]:
        m = re.search(r'(?:at least|minimum|min|>=|greater than|more than)\s*(\d+)\s*(?:bedrooms?|bhk|beds?)', q)
        if m:
            return NumericCondition(field="bedrooms", operator="gte", value=int(m.group(1)))

        m = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)\s*(?:bedrooms?|bhk|beds?)', q)
        if m:
            return NumericCondition(field="bedrooms", operator="between", value=int(m.group(1)), value_end=int(m.group(2)))

        m = re.search(r'(\d+)\+\s*(?:bedrooms?|bhk|beds?)', q)
        if m:
            return NumericCondition(field="bedrooms", operator="gte", value=int(m.group(1)))

        m = re.search(r'\b(\d+)\s*(?:bedrooms?|bhk|beds?)\b', q)
        if m:
            return NumericCondition(field="bedrooms", operator="eq", value=int(m.group(1)))

        m = re.search(r'\b(' + '|'.join(self.NUM_WORDS.keys()) + r')\b\s*(?:bedrooms?|bhk|beds?)', q)
        if m:
            return NumericCondition(field="bedrooms", operator="eq", value=self._word_to_num(m.group(1)))

        return None

    # ------------------ BATHROOMS ------------------
    def _extract_bathrooms(self, q: str) -> Optional[NumericCondition]:
    # support phrases like "with 2+ bathrooms", "at least 2 bathrooms", etc.
        m = re.search(r'(?:with\s*|at least\s*|minimum\s*|>=|more than\s*)(\d+)\s*\+?\s*(?:bathrooms?|baths?)', q)
        if m:
            return NumericCondition(field="bathrooms", operator="gte", value=int(m.group(1)))

        m = re.search(r'(\d+)\s*(?:to|-)\s*(\d+)\s*(?:bathrooms?|baths?)', q)
        if m:
            return NumericCondition(field="bathrooms", operator="between", value=int(m.group(1)), value_end=int(m.group(2)))

        m = re.search(r'\b(\d+)\+\s*(?:bathrooms?|baths?)\b', q)
        if m:
            return NumericCondition(field="bathrooms", operator="gte", value=int(m.group(1)))

        m = re.search(r'\b(\d+)\s*(?:bathrooms?|baths?)\b', q)
        if m:
            return NumericCondition(field="bathrooms", operator="eq", value=int(m.group(1)))

        return None

    # ------------------ PRICE ------------------
    def _extract_price(self, q: str) -> Optional[NumericCondition]:
        m = re.search(r'(?:under|below|less than)\s*\$?([\d,\.kK]+)', q)
        if m:
            raw = m.group(1).replace(",", "")
            if raw.lower().endswith("k"):
                val = float(raw[:-1]) * 1000
            else:
                val = float(raw)
            return NumericCondition(field="price", operator="lte", value=val)

        m = re.search(r'\b(?:around|~)\s*\$?([\d,\.kK]+)', q)
        if m:
            raw = m.group(1).replace(",", "")
            if raw.lower().endswith("k"):
                val = float(raw[:-1]) * 1000
            else:
                val = float(raw)
            low, high = val * 0.9, val * 1.1
            return NumericCondition(field="price", operator="between", value=low, value_end=high)

        return None

    # ------------------ CRIME ------------------
    def _extract_crime(self, q: str) -> Optional[NumericCondition]:
        m = re.search(r'crime.*(?:less than|<)\s*(\d+)', q)
        if m:
            return NumericCondition(field="crime_score_weight", operator="lt", value=float(m.group(1)))
        return None

    # ------------------ PROPERTY TYPE ------------------
    def _extract_property_type(self, q: str) -> Optional[str]:
        types = ["house", "flat", "apartment", "bungalow", "detached", "semi-detached", "terraced", "studio"]
        for t in types:
            if re.search(r'\b' + re.escape(t) + r'\b', q):
                return t
        return None

    # ------------------ LOCATION ------------------
    def _extract_location(self, q: str, known_locations: Optional[List[str]] = None) -> Optional[str]:
        if known_locations:
            q_low = q.lower()
            for known in known_locations:
                if not known:
                    continue
                if known.lower() in q_low:
                    return known
            for known in known_locations:
                if not known:
                    continue
                for tok in known.lower().split():
                    if tok in q_low and len(tok) > 2:
                        return known

        m = re.search(r'\bin\s+([a-z][a-z\s\-]+?)(?:\b|$|,)', q)
        if m:
            loc = m.group(1).strip()
            return re.sub(r'[^\w\s\-]', '', loc)
        return None

    # ------------------ MAIN PARSER ------------------
    def parse_query(self, query: str, known_locations: Optional[List[str]] = None) -> QueryStructure:
        q = query.lower().strip()
        logger.info(f"🔍 Parsing query: {query}")

        # detect query type (supports "what's" and "what is")
        if any(k in q for k in ["average", "avg", "mean", "sum", "count", "total number", "compare", "most", "minimum", "maximum"]):
            query_type = QueryType.AGGREGATION
        elif any(k in q for k in ["show", "list", "find", "display", "properties", "homes", "houses", "find properties"]):
            query_type = QueryType.FILTER
        else:
            query_type = QueryType.RETRIEVAL

        bedrooms = self._extract_bedrooms(q)
        bathrooms = self._extract_bathrooms(q)
        price = self._extract_price(q)
        crime_score_weight = self._extract_crime(q)

        # ---------------- FLOOD RISK ----------------
        flood_risk = None
        if re.search(r"\b(very\s+low|low)(?:\s+flood|\s+flood\s+risk|\s+risk)?", q):
            flood_risk = "low"
        elif re.search(r"\bmedium(?:\s+flood|\s+flood\s+risk|\s+risk)?", q):
            flood_risk = "medium"
        elif re.search(r"\bhigh(?:\s+flood|\s+flood\s+risk|\s+risk)?", q):
            flood_risk = "high"

        is_new_home = "new home" in q or "newly built" in q

        laua_match = re.search(r'in\s+([a-z\s]+)\s+area', q)
        laua = laua_match.group(1).strip() if laua_match else None

        property_type_full_description = self._extract_property_type(q)
        address = self._extract_location(q, known_locations)

        description_requirements = []
        for word in ["studio", "luxury", "affordable", "cheap", "family"]:
            if word in q:
                description_requirements.append(word)

        aggregation_field = aggregation_function = None
        if query_type == QueryType.AGGREGATION:
            if "crime" in q and "most" in q:
                aggregation_field = "crime_score_weight"
                aggregation_function = "MAX"
            elif "average price" in q or "mean price" in q:
                aggregation_field = "price"
                aggregation_function = "AVG"
            elif "compare" in q and "price" in q:
                aggregation_field = "price"
                aggregation_function = "COMPARE"
            elif "sum" in q:
                aggregation_field = "price"
                aggregation_function = "SUM"
            elif "count" in q or "total number" in q:
                aggregation_field = "*"
                aggregation_function = "COUNT"

        parsed = QueryStructure(
            query_type=query_type,
            original_text=query,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            price=price,
            crime_score_weight=crime_score_weight,
            flood_risk=flood_risk,
            is_new_home=is_new_home or None,
            laua=laua,
            aggregation_field=aggregation_field,
            aggregation_function=aggregation_function,
            description_requirements=description_requirements or None,
            property_type_full_description=property_type_full_description,
            address=address,
        )

        logger.info(f"Parsed query: {parsed}")
        return parsed
