# src/query/schema.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, Literal
from enum import Enum
from ..config.config import NUMERIC_FIELDS


class QueryType(str, Enum):
    """Defines what kind of query the user asked for."""
    FILTER = "filter"
    AGGREGATION = "aggregation"
    RETRIEVAL = "retrieval"


#  Valid aggregation functions
AggregationFunction = Literal["COUNT", "AVG", "SUM", "MIN", "MAX" , "COMPARE"]

#  Aggregation fields (based on your dataset)
ValidAggregationField = Literal["*","price", "bedrooms", "bathrooms", "crime_score_weight"]


class NumericCondition(BaseModel):
    """Represents a single numeric comparison condition."""
    field: str
    operator: Literal["eq", "gt", "lt", "gte", "lte", "between"]
    value: Union[float, int]
    value_end: Optional[Union[float, int]] = None  # for ranges (like between)


class QueryStructure(BaseModel):
    """Structured representation of parsed property query."""

    # Core metadata
    query_type: QueryType = Field(
        description="Type of query (filter, aggregation, or retrieval)"
    )
    original_text: Optional[str] = Field(
        None, description="Raw user input query text"
    )

    # Property filters
    bedrooms: Optional[NumericCondition] = Field(None, description="Filter on bedroom count")
    bathrooms: Optional[NumericCondition] = Field(None, description="Filter on bathroom count")
    price: Optional[NumericCondition] = Field(None, description="Filter on price")
    crime_score_weight: Optional[NumericCondition] = Field(None, description="Filter on crime score")
    flood_risk: Optional[str] = Field(None, description="Flood risk filter (low, medium, high)")
    is_new_home: Optional[bool] = Field(None, description="Filter for new homes only")
    laua: Optional[str] = Field(None, description="Local authority area filter")
    property_type_full_description: Optional[str] = Field(None, description="Property type filter")
    address: Optional[str] = Field(None, description="Address filter")

    # Aggregation details
    aggregation_field: Optional[ValidAggregationField] = Field(
        None, description="Field to aggregate (numeric fields only)"
    )
    aggregation_function: Optional[AggregationFunction] = Field(
        None, description="Aggregation function (AVG, MAX, MIN, SUM, COUNT)"
    )

    # Semantic / descriptive search
    description_requirements: Optional[List[str]] = Field(
        None, description="Keywords for semantic matching"
    )

    #  Validator: ensure aggregation fields are consistent
    @field_validator("aggregation_field")
    @classmethod
    def validate_aggregation_field(cls, v, info):
        """
        Ensure that aggregation fields only appear in aggregation queries
        and numeric functions are applied to numeric fields.
        """
        if v is not None:
            query_type = info.data.get("query_type")
            agg_func = info.data.get("aggregation_function")

            if query_type != QueryType.AGGREGATION:
                raise ValueError("Aggregation field only allowed for aggregation queries")

            if agg_func in ["AVG", "SUM", "MIN", "MAX"] and v not in NUMERIC_FIELDS:
                raise ValueError(
                    f"{agg_func} can only be applied to numeric fields: {', '.join(NUMERIC_FIELDS)}"
                )

        return v
