from typing import List, Optional
from pydantic import BaseModel
from enum import Enum

class RelationType(str, Enum):
    MUTUALLY_EXCLUSIVE = "mutually_exclusive"
    COMPLEMENTARY = "complementary"
    CONDITIONAL = "conditional"
    UNRELATED = "unrelated"

class ArbitrageRelationship(BaseModel):
    markets: List[str]
    relationship_type: RelationType
    confidence_score: float
    explanation: str
    potential_arbitrage: bool
    combined_probability: Optional[float]
    arbitrage_explanation: str

class AnalysisResult(BaseModel):
    timestamp: str
    total_markets: int
    relationships: List[ArbitrageRelationship]
