from openai import OpenAI
import json
from typing import Any, Dict, List
from src.config.settings import (
    OPENROUTER_API_KEY, 
    OPENROUTER_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_TEMPERATURE
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class LLMClient:
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )
        self.default_model = DEFAULT_MODEL

    async def analyze(self, 
                     prompt: str, 
                     model: str = None,
                     temperature: float = DEFAULT_TEMPERATURE) -> List[Dict[str, Any]]:
        """
        Send analysis request to OpenRouter API with structured output.
        """
        try:
            response = self.client.chat.completions.create(
                model=model or self.default_model,
                messages=[{
                    "role": "system",
                    "content": "You are a precise market analyst specializing in finding arbitrage opportunities."
                }, {
                    "role": "user",
                    "content": prompt
                }],
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "arbitrage_relationships",
                        "strict": True,
                        "schema": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "markets": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "List of market questions involved in the relationship"
                                    },
                                    "relationship_type": {
                                        "type": "string",
                                        "enum": ["mutually_exclusive", "complementary", "conditional", "unrelated"],
                                        "description": "Type of relationship between markets"
                                    },
                                    "confidence_score": {
                                        "type": "number",
                                        "minimum": 0,
                                        "maximum": 1,
                                        "description": "Confidence in the analysis (0-1)"
                                    },
                                    "explanation": {
                                        "type": "string",
                                        "description": "Detailed explanation of the relationship"
                                    },
                                    "potential_arbitrage": {
                                        "type": "boolean",
                                        "description": "Whether there's a potential arbitrage opportunity"
                                    },
                                    "combined_probability": {
                                        "type": ["number", "null"],
                                        "minimum": 0,
                                        "maximum": 1,
                                        "description": "Combined probability if applicable"
                                    },
                                    "arbitrage_explanation": {
                                        "type": "string",
                                        "description": "Explanation of the arbitrage opportunity if exists"
                                    }
                                },
                                "required": [
                                    "markets",
                                    "relationship_type",
                                    "confidence_score",
                                    "explanation",
                                    "potential_arbitrage",
                                    "arbitrage_explanation"
                                ],
                                "additionalProperties": False
                            }
                        }
                    }
                },
                extra_headers={
                    "HTTP-Referer": "http://localhost",
                    "X-Title": "Local Testing"
                }
            )
            logger.debug(f"Raw LLM response: {response.choices[0].message.content}") 
            
            # The response will already be proper JSON
            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"LLM analysis failed: {str(e)}")
            raise
