import asyncio
from src.data.polymarket_client import PolymarketClient
from src.analysis.market_analyzer import MarketAnalyzer
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def main():
    try:
        client = PolymarketClient()
        tags = ["Trump"]
        logger.info(f"Fetching markets with tags: {tags}")
        markets = client.get_all_markets(tags=tags)

        analyzer = MarketAnalyzer()
        results = await analyzer.analyze_markets(markets)
        
        logger.info(f"Analysis complete:")
        logger.info(f"- Total markets analyzed: {results.total_markets}")
        logger.info(f"- Relationships found: {len(results.relationships)}")
        logger.info(f"- Arbitrage opportunities: {sum(1 for r in results.relationships if r.potential_arbitrage)}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())
