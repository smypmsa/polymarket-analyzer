from typing import List, Dict, Any
import json
from datetime import datetime
from pathlib import Path

from src.analysis.llm_client import LLMClient
from src.analysis.models import AnalysisResult
from src.data.models import Market
from src.config.settings import ANALYSIS_DIR
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MarketAnalyzer:
    def __init__(self):
        self.llm_client = LLMClient()

    def _build_relationship_prompt(self, markets: List[Market]) -> str:
        """Build prompt for analyzing relationships between ALL markets."""
        markets_text = "\n\n".join([
            f"Market {i+1}:\nQuestion: {m.question}\nDescription: {m.description}\n"
            f"Current Prices: {m.prices}\nEnd Date: {m.end_date}"
            for i, m in enumerate(markets)
        ])
        
        return f"""
        You are an expert Polymarket arbitrage analyst. Your goal is to find ONLY GUARANTEED arbitrage opportunities 
        where buying combinations of YES or NO shares across markets creates mathematically certain profit. 
        Remember: You can only BUY positions (YES or NO shares) - no short selling is allowed. Price of shares for all outcomes must be less 1.
        
        {markets_text}
        
        IMPORTANT: Return ONLY a JSON array without any additional text, markdown, or explanation.
        Each element in the array should follow this exact structure:
        {{
            "markets": ["market question 1", "market question 2"],
            "relationship_type": "mutually_exclusive|complementary|conditional|unrelated",
            "confidence_score": 0.95,
            "explanation": "Detailed explanation",
            "potential_arbitrage": true,
            "combined_probability": 0.95,
            "arbitrage_explanation": "Specific arbitrage mechanics"
        }}

        Your response should start with [ and end with ] and be valid JSON.
        Do not include any other text or explanations outside the JSON array.
        """

    async def analyze_markets(self, 
                            markets: List[Market],
                            save_output: bool = True) -> AnalysisResult:
        """
        Analyze all markets for arbitrage opportunities in a single pass.
        """
        try:
            logger.info(f"Starting analysis of {len(markets)} markets")
            
            relationships = await self.llm_client.analyze(
                self._build_relationship_prompt(markets)
            )

            results = AnalysisResult(
                timestamp=datetime.now().isoformat(),
                total_markets=len(markets),
                relationships=relationships
            )

            if save_output:
                self._save_analysis(results.dict())
                logger.info(f"Analysis saved with {len(results.relationships)} relationships found")

            return results

        except Exception as e:
            logger.error(f"Market analysis failed: {str(e)}")
            raise

    def _save_analysis(self, results: Dict[str, Any]) -> None:
        """Save analysis results to file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = ANALYSIS_DIR / f"arbitrage_analysis_{timestamp}.json"
        
        try:
            with open(filename, "w", encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            logger.info(f"Analysis saved to {filename}")
        except Exception as e:
            logger.error(f"Failed to save analysis: {str(e)}")
